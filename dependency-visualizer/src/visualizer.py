"""Инструмент визуализации графа зависимостей npm-пакетов (вариант 23).

Этап 1: минимальный CLI-прототип с конфигурацией в формате YAML.
Этап 2: получение прямых зависимостей пакета из npm-репозитория.
Этап 3: построение графа зависимостей (DFS с рекурсией), фильтрация
        пакетов, обработка циклов, режим тестового репозитория.
"""

import argparse
import os
import sys

from config import ConfigError, load_config
from graph import build_graph
from npm_registry import NpmRegistry, RegistryError
from test_repo import TestRepoError, TestRepository

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


def make_source(config, config_path):
    """Создаёт источник данных и возвращает (источник, корневой узел)."""
    if config.test_repo_mode == "file":
        # Относительный путь отсчитывается от каталога конфигурационного файла.
        base = os.path.dirname(os.path.abspath(config_path))
        source = TestRepository(os.path.normpath(os.path.join(base, config.repository)))
        if config.package not in source.graph:
            raise TestRepoError(f"пакет {config.package} не описан в тестовом репозитории")
        return source, config.package
    source = NpmRegistry(config.repository)
    return source, source.resolve(config.package, config.version)


def print_graph(graph, config):
    where = "тестовый репозиторий" if config.test_repo_mode == "file" else "репозиторий"
    print(f"Граф зависимостей {graph.root} ({where}: {config.repository})")
    if config.filter:
        print(f"Фильтр: пакеты, содержащие {config.filter!r}, не учитываются")
    print()
    for node, children in graph.edges.items():
        print(f"  {node} -> {', '.join(children) if children else '(нет зависимостей)'}")
    print()
    print(f"Пакетов: {len(graph.edges)}, зависимостей (рёбер): {graph.edge_count()}")

    if graph.cycles:
        print("Циклические зависимости:")
        for cycle in graph.cycles:
            print("  " + " -> ".join(cycle))
    else:
        print("Циклических зависимостей нет")
    if graph.filtered:
        print("Исключены фильтром: " + ", ".join(sorted(graph.filtered)))
    for warning in graph.warnings:
        print(f"Предупреждение: {warning}", file=sys.stderr)


def main(argv=None):
    args = parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Ошибка конфигурации ({args.config}):", file=sys.stderr)
        for err in e.errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if config.filter and config.filter in config.package:
        print(
            f"Ошибка: имя анализируемого пакета {config.package!r} содержит "
            f"подстроку фильтра {config.filter!r}",
            file=sys.stderr,
        )
        return 1

    try:
        source, root = make_source(config, args.config)
    except TestRepoError as e:
        print(f"Ошибка тестового репозитория:\n{e}", file=sys.stderr)
        return 1
    except RegistryError as e:
        print(f"Ошибка репозитория: {e}", file=sys.stderr)
        return 1

    graph = build_graph(source, root, config.filter)
    print_graph(graph, config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
