"""Модульные тесты построения графа зависимостей на тестовых репозиториях."""

import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from graph import build_graph, find_nodes, reverse_dependencies  # noqa: E402
from test_repo import TestRepoError, TestRepository  # noqa: E402


def repo(name):
    return TestRepository(os.path.join(HERE, "repos", name))


class GraphTest(unittest.TestCase):
    def test_transitive(self):
        g = build_graph(repo("simple.txt"), "A")
        self.assertEqual(g.edges, {"A": ["B", "C"], "B": ["D"], "D": [], "C": ["D"]})
        self.assertEqual(g.cycles, [])

    def test_cycle(self):
        g = build_graph(repo("cycle.txt"), "A")
        self.assertEqual(g.cycles, [["A", "B", "C", "A"]])
        self.assertEqual(set(g.nodes), {"A", "B", "C", "D"})

    def test_self_loop(self):
        g = build_graph(repo("self_loop.txt"), "A")
        self.assertEqual(g.cycles, [["A", "A"]])

    def test_multiple_cycles(self):
        g = build_graph(repo("multi_cycle.txt"), "A")
        self.assertEqual(g.cycles, [["A", "B", "A"], ["C", "D", "C"]])

    def test_filter(self):
        g = build_graph(repo("filter.txt"), "A", "X")
        self.assertEqual(set(g.nodes), {"A", "B", "E"})
        self.assertEqual(g.filtered, {"XC", "XD"})

    def test_filter_breaks_cycle(self):
        g = build_graph(repo("cycle.txt"), "A", "C")
        self.assertEqual(g.edges, {"A": ["B"], "B": []})
        self.assertEqual(g.cycles, [])

    def test_undefined_package_is_leaf(self):
        g = build_graph(repo("complex.txt"), "A")
        self.assertEqual(g.edges["Z"], [])
        self.assertNotIn("Q", g.edges)

    def test_deep_chain(self):
        g = build_graph(repo("chain.txt"), "A")
        self.assertEqual(len(g.nodes), 10)

    def test_bad_file(self):
        with self.assertRaises(TestRepoError):
            repo("err_format.txt")



class ReverseTest(unittest.TestCase):
    def reverse(self, file, root, target, filt=""):
        src = repo(file)
        g = build_graph(src, root, filt)
        return reverse_dependencies(g, target, src.name_of)

    def test_reverse_transitive(self):
        r = self.reverse("reverse.txt", "A", "G")
        self.assertEqual(r.edges["G"], ["D", "E"])
        self.assertEqual(set(r.nodes) - {"G"}, {"A", "B", "C", "D", "E"})
        self.assertEqual(r.edges["E"], ["B", "C"])

    def test_reverse_single_path(self):
        r = self.reverse("reverse.txt", "A", "F")
        self.assertEqual(r.edges, {"F": ["C"], "C": ["A"], "A": []})

    def test_reverse_of_root(self):
        r = self.reverse("simple.txt", "A", "A")
        self.assertEqual(r.edges, {"A": []})

    def test_reverse_cycle(self):
        r = self.reverse("cycle.txt", "A", "B")
        self.assertEqual(set(r.nodes), {"A", "B", "C"})
        self.assertEqual(r.cycles, [["B", "A", "C", "B"]])

    def test_reverse_with_filter(self):
        r = self.reverse("reverse.txt", "A", "G", "C")
        self.assertNotIn("C", r.edges)
        self.assertEqual(r.edges["E"], ["B"])

    def test_find_nodes(self):
        src = repo("simple.txt")
        g = build_graph(src, "A")
        self.assertEqual(find_nodes(g, src.name_of, "D"), ["D"])
        self.assertEqual(find_nodes(g, src.name_of, "Q"), [])


if __name__ == "__main__":
    unittest.main()
