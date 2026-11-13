"""Сравнение графа программы с выводом штатного инструмента npm (npm ls).

Сам npm программой не используется — скрипт нужен только для проверки
результатов этапа 5. Порядок действий (нужен установленный Node.js):

    mkdir cmp && cd cmp
    npm init -y
    npm install express@4.21.2 --omit=dev --ignore-scripts
    npm ls --all --json > ls.json

    python tools/compare_with_npm.py cmp/ls.json express 4.21.2
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from graph import build_graph  # noqa: E402
from npm_registry import NpmRegistry  # noqa: E402

REGISTRY = "https://registry.npmjs.org"


def npm_graph(ls_json_path):
    """Пакеты и рёбра из дерева npm ls --all --json (с учётом deduped)."""
    with open(ls_json_path, encoding="utf-8") as f:
        tree = json.load(f)
    nodes, edges = set(), set()

    def walk(entry, parent):
        for name, dep in (entry.get("dependencies") or {}).items():
            node = f"{name}@{dep.get('version')}"
            nodes.add(node)
            if parent:
                edges.add((parent, node))
            walk(dep, node)

    walk(tree, None)
    return nodes, edges


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    ls_path, package, version = sys.argv[1:]
    npm_nodes, npm_edges = npm_graph(ls_path)
    source = NpmRegistry(REGISTRY)
    graph = build_graph(source, source.resolve(package, version))
    nodes = set(graph.edges)
    edges = {(a, b) for a, children in graph.edges.items() for b in children}

    print(f"{package}@{version}")
    print(f"  npm ls:    {len(npm_nodes)} пакетов, {len(npm_edges)} рёбер")
    print(f"  программа: {len(nodes)} пакетов, {len(edges)} рёбер")
    for title, diff in [
        ("пакеты только у программы", nodes - npm_nodes),
        ("пакеты только у npm", npm_nodes - nodes),
        ("рёбра только у программы", edges - npm_edges),
        ("рёбра только у npm", npm_edges - edges),
    ]:
        print(f"  {title}: " + (", ".join(sorted(map(str, diff))) if diff else "нет"))
    same = nodes == npm_nodes and edges == npm_edges
    print("  результат: " + ("графы совпадают" if same else "есть расхождения"))
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
