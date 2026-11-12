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

TIMEOUT = 15  # секунд


class RegistryError(Exception):
    """Ошибка получения данных из репозитория."""


def manifest_url(registry, package, version):
    """URL манифеста конкретной версии пакета.

    Формат реестра npm: <registry>/<имя>/<версия>.
    Для пакетов с областью видимости (@scope/name) символ '/' кодируется
    как %2F. Вместо версии допускается dist-tag, например 'latest'.
    """
    name = quote(package, safe="@")
    return f"{registry.rstrip('/')}/{name}/{quote(version, safe='')}"


def fetch_manifest(registry, package, version):
    """Загружает и разбирает манифест (package.json) версии пакета."""
    url = manifest_url(registry, package, version)
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read()
    except HTTPError as e:
        if e.code == 404:
            raise RegistryError(
                f"пакет {package!r} версии {version!r} не найден в репозитории ({url})"
            )
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
    """Прямые зависимости из манифеста: словарь {имя: диапазон версий}.

    Учитывается поле "dependencies" — зависимости, необходимые пакету
    во время работы (devDependencies при установке пакета не ставятся).
    """
    deps = manifest.get("dependencies") or {}
    if not isinstance(deps, dict):
        raise RegistryError("поле dependencies в манифесте имеет неверный формат")
    return {str(name): str(spec) for name, spec in deps.items()}


def get_direct_dependencies(registry, package, version):
    """Возвращает (фактическая версия, {зависимость: диапазон версий})."""
    manifest = fetch_manifest(registry, package, version)
    return manifest.get("version", version), direct_dependencies(manifest)
