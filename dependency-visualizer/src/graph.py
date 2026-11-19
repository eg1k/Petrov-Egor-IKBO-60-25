"""Построение графа зависимостей с учётом транзитивности.

Граф строится обходом в глубину (DFS) с рекурсией. Источник данных
(реальный npm-репозиторий или тестовый файл) передаётся объектом с методами:

    resolve(name, spec) -> узел          подобрать версию зависимости
    dependencies(node)  -> [(name, spec)] прямые зависимости узла
    name_of(node)       -> имя пакета
"""

import sys
from dataclasses import dataclass, field

sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))


@dataclass
class DependencyGraph:
    """Хранит список смежности в порядке обхода, циклы и диагностику.

    Цикл представлен путём с повтором начального узла в конце.
    Поле filtered содержит имена пакетов, исключённых фильтром,
    а warnings — сообщения о недоступных данных.
    """

    root: str
    edges: dict = field(default_factory=dict)
    cycles: list = field(default_factory=list)
    filtered: set = field(default_factory=set)
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
    state = {}
    path = []

    def dfs(node):
        state[node] = "visiting"
        path.append(node)
        children = []
        graph.edges[node] = children
        for child in _resolve_children(source, node, graph, filter_substring):
            if child not in children:
                children.append(child)
            if state.get(child) is None:
                dfs(child)
            elif state[child] == "visiting":
                graph.cycles.append(path[path.index(child) :] + [child])

        path.pop()
        state[node] = "done"

    dfs(root)
    return graph


def _resolve_children(source, node, graph, filter_substring):
    for name, spec in _dependencies(source, node, graph):
        if filter_substring and filter_substring in name:
            graph.filtered.add(name)
            continue
        try:
            child = source.resolve(name, spec)
        except Exception as e:
            graph.warnings.append(
                f"{node} -> {name} {spec or ''}: {e}".rstrip()
            )
            continue
        yield child


def _dependencies(source, node, graph):
    """При недоступных метаданных оставляет пакет листом графа."""
    try:
        return source.dependencies(node)
    except Exception as e:
        graph.warnings.append(f"{node}: не удалось получить зависимости ({e})")
        return []


class ReverseSource:
    """Источник данных с развёрнутыми рёбрами уже построенного графа.

    "Зависимости" узла здесь — пакеты, которые от него зависят. Это позволяет
    получить обратные зависимости тем же рекурсивным алгоритмом build_graph.
    """

    def __init__(self, graph, name_of):
        self.parents = {node: [] for node in graph.edges}
        for node, children in graph.edges.items():
            for child in children:
                if node not in self.parents.setdefault(child, []):
                    self.parents[child].append(node)
        self._name_of = name_of

    def resolve(self, name, spec=None):
        return name

    def name_of(self, node):
        return self._name_of(node)

    def dependencies(self, node):
        return [(parent, None) for parent in self.parents.get(node, [])]


def find_nodes(graph, name_of, target):
    """Узлы графа, соответствующие пакету target ("имя" или "имя@версия")."""
    return [n for n in graph.edges if n == target or name_of(n) == target]


def reverse_dependencies(graph, target, name_of):
    """Граф обратных зависимостей узла target внутри графа graph.

    Строится тем же обходом в глубину, что и прямой граф, но по развёрнутым
    рёбрам: в результат попадают все пакеты, которые зависят от target
    напрямую или транзитивно.
    """
    return build_graph(ReverseSource(graph, name_of), target)
