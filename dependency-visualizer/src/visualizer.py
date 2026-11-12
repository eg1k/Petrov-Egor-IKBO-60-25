"""Инструмент визуализации графа зависимостей npm-пакетов (вариант 23).

Этап 1: минимальный CLI-прототип с конфигурацией в формате YAML.
Этап 2: получение прямых зависимостей пакета из npm-репозитория.
"""

import argparse
import sys

from config import ConfigError, load_config
from npm_registry import RegistryError, get_direct_dependencies

DEFAULT_CONFIG = "config.yaml"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей npm-пакетов"
    )
    parser.add_argument(
        "-c", "--config",
        default=DEFAULT_CONFIG,
        help=f"путь к конфигурационному файлу YAML (по умолчанию {DEFAULT_CONFIG})",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Ошибка конфигурации ({args.config}):", file=sys.stderr)
        for err in e.errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if config.test_repo_mode != "off":
        print(
            "Ошибка: работа с тестовым репозиторием (test_repo_mode: file) "
            "пока не поддерживается, укажите test_repo_mode: off",
            file=sys.stderr,
        )
        return 1

    try:
        version, deps = get_direct_dependencies(
            config.repository, config.package, config.version
        )
    except RegistryError as e:
        print(f"Ошибка репозитория: {e}", file=sys.stderr)
        return 1

    # Только для этапа 2: вывод всех прямых зависимостей пакета.
    print(f"Прямые зависимости {config.package}@{version}:")
    if not deps:
        print("  (нет зависимостей)")
    for name, spec in sorted(deps.items()):
        print(f"  {name} {spec}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
