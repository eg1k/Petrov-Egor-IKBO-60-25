"""Построение графа зависимостей с учётом транзитивности.

Граф строится обходом в глубину (DFS) с рекурсией. Источник данных
(реальный npm-репозиторий или тестовый файл) передаётся объектом с методами:

    resolve(name, spec) -> узел          подобрать версию зависимости
    dependencies(node)  -> [(name, spec)] прямые зависимости узла
    name_of(node)       -> имя пакета
"""

import sys
from dataclasses import dataclass, field

# Глубина дерева зависимостей может быть большой — увеличиваем лимит рекурсии.
sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))


@dataclass
class DependencyGraph:
    root: str
    # Список смежности в порядке обхода: узел -> его прямые зависимости.
    edges: dict = field(default_factory=dict)
    # Найденные циклы: списки узлов вида [A, B, C, A].
    cycles: list = field(default_factory=list)
    # Имена пакетов, исключённых фильтром.
    filtered: set = field(default_factory=set)
    # Предупреждения (не удалось получить данные о части пакетов и т. п.).
    warnings: list = field(default_factory=list)

    @property
    def nodes(self):
        return list(self.edges)

    def edge_count(self):
        return sum(len(children) for children in self.edges.values())


def build_graph(source, root, filter_substring=""):
    """Строит граф зависимостей пакета root рекурсивным обходом в глубину.

    - пакеты, имя которых содержит filter_substring, не учитываются;
    - каждый пакет раскрывается один раз (повторные вхождения не обходятся);
    - ребро в пакет, который сейчас находится в стеке обхода, означает
      циклическую зависимость: цикл запоминается, а обход по нему не
      продолжается, поэтому зацикливания не происходит.
    """
    graph = DependencyGraph(root)
    state = {}  # узел -> "visiting" (в стеке обхода) | "done" (обработан)
    path = []   # текущий путь от корня

    def dfs(node):
        state[node] = "visiting"
        path.append(node)
        children = []
        graph.edges[node] = children  # сохраняем порядок обхода (pre-order)
        try:
            deps = source.dependencies(node)
        except Exception as e:  # нет данных о пакете — считаем его листом
            graph.warnings.append(f"{node}: не удалось получить зависимости ({e})")
            deps = []

        for name, spec in deps:
            if filter_substring and filter_substring in name:
                graph.filtered.add(name)
                continue
            try:
                child = source.resolve(name, spec)
            except Exception as e:
                graph.warnings.append(f"{node} -> {name} {spec or ''}: {e}".rstrip())
                continue
            if child not in children:
                children.append(child)
            if state.get(child) is None:
                dfs(child)
            elif state[child] == "visiting":
                graph.cycles.append(path[path.index(child):] + [child])

        path.pop()
        state[node] = "done"

    dfs(root)
    return graph
