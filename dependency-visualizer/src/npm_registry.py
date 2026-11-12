"""Получение информации о пакетах из npm-репозитория по HTTP.

Менеджер пакетов npm и сторонние библиотеки не используются:
данные запрашиваются напрямую у реестра (registry API) средствами
стандартной библиотеки Python.
"""

import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from semver import SemverError, max_satisfying

TIMEOUT = 15  # секунд
# Сокращённый формат метаданных (используется самим npm при установке):
# содержит все версии пакета с их зависимостями, но без README и т. п.
ACCEPT = "application/vnd.npm.install-v1+json; q=1.0, application/json; q=0.8"


class RegistryError(Exception):
    """Ошибка получения данных из репозитория."""


def package_url(registry, package):
    """URL метаданных пакета: <registry>/<имя>.

    Для пакетов с областью видимости (@scope/name) символ '/' кодируется как %2F.
    """
    return f"{registry.rstrip('/')}/{quote(package, safe='@')}"


def _fetch_json(url, what):
    request = Request(url, headers={"Accept": ACCEPT})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read()
    except HTTPError as e:
        if e.code == 404:
            raise RegistryError(f"{what} не найден в репозитории ({url})")
        raise RegistryError(f"репозиторий вернул ошибку HTTP {e.code} ({url})")
    except (socket.timeout, TimeoutError):
        raise RegistryError(f"превышено время ожидания ответа от {url}")
    except URLError as e:
        raise RegistryError(f"не удалось подключиться к репозиторию {url}: {e.reason}")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RegistryError(f"ответ репозитория не является корректным JSON ({url})")
    if not isinstance(data, dict):
        raise RegistryError(f"неожиданный формат ответа репозитория ({url})")
    return data


def direct_dependencies(manifest):
    """Прямые зависимости из манифеста версии: {имя: диапазон версий}.

    Учитывается поле "dependencies" — зависимости, необходимые пакету
    во время работы (devDependencies при установке пакета не ставятся).
    """
    deps = manifest.get("dependencies") or {}
    if not isinstance(deps, dict):
        raise RegistryError("поле dependencies в манифесте имеет неверный формат")
    return {str(name): str(spec) for name, spec in deps.items()}


class NpmRegistry:
    """Источник данных о зависимостях — реальный npm-репозиторий.

    Узел графа — строка "имя@версия". Метаданные каждого пакета
    загружаются один раз и кешируются.
    """

    test_mode = False

    def __init__(self, registry):
        self.registry = registry
        self._cache = {}
        self.warnings = []

    def packument(self, name):
        if name not in self._cache:
            self._cache[name] = _fetch_json(package_url(self.registry, name), f"пакет {name!r}")
        return self._cache[name]

    def resolve(self, name, spec):
        """Подбирает конкретную версию пакета по диапазону; возвращает узел."""
        if spec.startswith("npm:"):
            # Псевдоним: "npm:настоящее-имя@диапазон".
            target = spec[4:]
            at = target.rfind("@")
            if at > 0:
                name, spec = target[:at], target[at + 1:]
            else:
                name, spec = target, "latest"
        data = self.packument(name)
        versions = data.get("versions") or {}
        tags = data.get("dist-tags") or {}
        spec = spec.strip()
        if spec in tags:
            version = tags[spec]
        elif spec in versions:
            version = spec
        else:
            try:
                version = max_satisfying(versions.keys(), spec or "*")
            except SemverError as e:
                raise RegistryError(f"{name}: неподдерживаемая спецификация версии {spec!r} ({e})")
            if version is None:
                raise RegistryError(f"{name}: нет версии, подходящей под {spec!r}")
        if version not in versions:
            raise RegistryError(f"пакет {name!r} версии {version!r} не найден в репозитории")
        return f"{name}@{version}"

    @staticmethod
    def split(node):
        at = node.rfind("@")
        return node[:at], node[at + 1:]

    def name_of(self, node):
        return self.split(node)[0]

    def dependencies(self, node):
        """Прямые зависимости узла: список пар (имя, диапазон версий)."""
        name, version = self.split(node)
        manifest = self.packument(name)["versions"][version]
        return list(direct_dependencies(manifest).items())


def get_direct_dependencies(registry, package, version):
    """Возвращает (фактическая версия, {зависимость: диапазон версий})."""
    source = NpmRegistry(registry)
    node = source.resolve(package, version)
    return source.split(node)[1], dict(source.dependencies(node))
