"""Тестовый репозиторий: граф пакетов, описанный в текстовом файле.

Формат файла — по одной строке на пакет:

    # комментарий
    A: B C      # пакет A зависит от B и C
    B: D
    D:          # у пакета D нет зависимостей

Имена пакетов — большие латинские буквы. Зависимости разделяются
пробелами или запятыми. Пакет, на который есть ссылка, но который не
описан отдельной строкой, считается пакетом без зависимостей.
"""

import re

NAME_RE = re.compile(r"^[A-Z]+$")


class TestRepoError(Exception):
    """Ошибка в файле тестового репозитория."""


def parse_test_repo(path):
    """Читает файл и возвращает словарь {пакет: [зависимости]}."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        raise TestRepoError(f"файл {path} не в кодировке UTF-8")
    except OSError as e:
        raise TestRepoError(f"не удалось прочитать {path}: {e.strerror}")

    graph, errors = {}, []
    for lineno, line in enumerate(lines, 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            errors.append(f"строка {lineno}: ожидается формат 'ПАКЕТ: ЗАВИСИМОСТИ'")
            continue
        name, deps_text = (part.strip() for part in line.split(":", 1))
        deps = [d for d in re.split(r"[\s,]+", deps_text) if d]
        bad = [n for n in [name] + deps if not NAME_RE.match(n)]
        if bad:
            errors.append(
                f"строка {lineno}: имена пакетов должны состоять из больших "
                f"латинских букв: {', '.join(repr(b) for b in bad)}"
            )
            continue
        if name in graph:
            errors.append(f"строка {lineno}: пакет {name} описан повторно")
            continue
        if len(set(deps)) != len(deps):
            errors.append(f"строка {lineno}: у пакета {name} повторяются зависимости")
            continue
        graph[name] = deps
    if errors:
        raise TestRepoError("\n".join(errors))
    if not graph:
        raise TestRepoError(f"тестовый репозиторий {path} не содержит пакетов")
    return graph


class TestRepository:
    """Источник данных о зависимостях — файл тестового репозитория.

    Узел графа — имя пакета; версии в тестовом режиме не используются.
    """

    test_mode = True

    def __init__(self, path):
        self.graph = parse_test_repo(path)
        self.warnings = []

    def resolve(self, name, spec=None):
        return name

    def name_of(self, node):
        return node

    def dependencies(self, node):
        return [(dep, None) for dep in self.graph.get(node, [])]
