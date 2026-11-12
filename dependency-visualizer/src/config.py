"""Загрузка и проверка конфигурации из YAML-файла."""

import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import yaml

# Режимы работы с тестовым репозиторием.
#   off  — работа с реальным репозиторием по URL;
#   file — вместо репозитория используется файл описания графа.
REPO_MODES = ("off", "file")

# Имя пакета npm: необязательный scope (@scope/), далее строчные буквы,
# цифры и символы - . _ ~; длина не более 214 символов.
# В тестовом режиме пакеты называются большими латинскими буквами.
NPM_NAME_RE = re.compile(r"^(@[a-z0-9][a-z0-9._~-]*/)?[a-z0-9][a-z0-9._~-]*$")
TEST_NAME_RE = re.compile(r"^[A-Z]+$")

# Версия в формате SemVer (MAJOR.MINOR.PATCH[-pre][+build]) или "latest".
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?"
    r"(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$"
)

REQUIRED_KEYS = ("package", "repository", "test_repo_mode", "version")
OPTIONAL_KEYS = ("filter",)
ALL_KEYS = REQUIRED_KEYS + OPTIONAL_KEYS


class ConfigError(Exception):
    """Ошибка конфигурации; содержит список всех найденных проблем."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("\n".join(self.errors))


@dataclass
class Config:
    package: str
    repository: str
    test_repo_mode: str
    version: str
    filter: str

    def items(self):
        """Параметры в порядке объявления: (ключ, значение)."""
        return [
            ("package", self.package),
            ("repository", self.repository),
            ("test_repo_mode", self.test_repo_mode),
            ("version", self.version),
            ("filter", self.filter),
        ]


def _read_yaml(path):
    if not os.path.exists(path):
        raise ConfigError([f"конфигурационный файл не найден: {path}"])
    if not os.path.isfile(path):
        raise ConfigError([f"путь к конфигурации не является файлом: {path}"])
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except UnicodeDecodeError:
        raise ConfigError([f"файл {path} не в кодировке UTF-8"])
    except OSError as e:
        raise ConfigError([f"не удалось прочитать {path}: {e.strerror}"])
    except yaml.YAMLError as e:
        raise ConfigError([f"синтаксическая ошибка YAML в {path}: {e}"])
    if data is None:
        raise ConfigError([f"конфигурационный файл пуст: {path}"])
    if not isinstance(data, dict):
        raise ConfigError(
            ["корень конфигурации должен быть словарём (ключ: значение), "
             f"получено: {type(data).__name__}"]
        )
    return data


def _check_str(data, key, errors, allow_empty=False):
    """Проверяет, что значение ключа — строка; возвращает её или None."""
    value = data.get(key)
    if value is None:
        if allow_empty:
            return ""
        errors.append(f"{key}: значение не задано")
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        errors.append(
            f"{key}: ожидается строка, получено {type(value).__name__}"
        )
        return None
    if not isinstance(value, str):
        # Например, version: 1.0 YAML прочитает как число.
        errors.append(
            f"{key}: ожидается строка, получено число {value!r} "
            "(заключите значение в кавычки)"
        )
        return None
    value = value.strip()
    if not value and not allow_empty:
        errors.append(f"{key}: значение не может быть пустым")
        return None
    return value


def _check_mode(data, errors):
    value = data.get("test_repo_mode")
    if isinstance(value, bool):
        # YAML превращает off/on/yes/no в bool — допускаем это.
        value = "file" if value else "off"
    if value is None:
        errors.append("test_repo_mode: значение не задано")
        return None
    if not isinstance(value, str):
        errors.append(
            "test_repo_mode: ожидается строка, получено "
            f"{type(value).__name__}"
        )
        return None
    value = value.strip().lower()
    if value not in REPO_MODES:
        errors.append(
            f"test_repo_mode: недопустимое значение {value!r}, "
            f"допустимо: {', '.join(REPO_MODES)}"
        )
        return None
    return value


def _check_repository(repo, mode, base_dir, errors):
    if mode == "file":
        # Относительный путь отсчитывается от каталога конфигурационного файла.
        repo = os.path.normpath(os.path.join(base_dir, repo))
        if not os.path.exists(repo):
            errors.append(f"repository: файл тестового репозитория не найден: {repo}")
        elif not os.path.isfile(repo):
            errors.append(f"repository: путь не является файлом: {repo}")
        return
    parsed = urlparse(repo)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        errors.append(
            f"repository: в режиме off ожидается URL вида http(s)://..., "
            f"получено {repo!r}"
        )


def load_config(path):
    """Читает YAML-файл, проверяет все параметры и возвращает Config.

    При любых ошибках выбрасывает ConfigError со списком всех проблем.
    """
    data = _read_yaml(path)
    errors = []

    for key in data:
        if key not in ALL_KEYS:
            errors.append(
                f"неизвестный параметр {key!r}, допустимы: {', '.join(ALL_KEYS)}"
            )
    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"{key}: обязательный параметр отсутствует")

    mode = _check_mode(data, errors) if "test_repo_mode" in data else None

    package = _check_str(data, "package", errors) if "package" in data else None
    if package is not None:
        if mode == "file":
            if not TEST_NAME_RE.match(package):
                errors.append(
                    f"package: в тестовом режиме имя пакета — большие "
                    f"латинские буквы, получено {package!r}"
                )
        elif len(package) > 214 or not NPM_NAME_RE.match(package):
            errors.append(f"package: недопустимое имя npm-пакета {package!r}")

    repo = _check_str(data, "repository", errors) if "repository" in data else None
    if repo is not None and mode is not None:
        _check_repository(repo, mode, os.path.dirname(os.path.abspath(path)), errors)

    version = _check_str(data, "version", errors) if "version" in data else None
    if version is not None and version != "latest" and not SEMVER_RE.match(version):
        errors.append(
            f"version: ожидается версия вида 1.2.3 или 'latest', получено {version!r}"
        )

    filt = _check_str(data, "filter", errors, allow_empty=True)

    if errors:
        raise ConfigError(errors)
    return Config(package, repo, mode, version, filt)
