"""Инструмент визуализации графа зависимостей npm-пакетов (вариант 23).

Этап 1: минимальный CLI-прототип с конфигурацией в формате YAML.
"""

import argparse
import sys

from config import ConfigError, load_config

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

    # Только для этапа 1: вывод всех параметров в формате ключ-значение.
    for key, value in config.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
