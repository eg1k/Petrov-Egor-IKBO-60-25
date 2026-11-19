"""Модульные тесты визуализации (Mermaid) и выбора версии как в npm."""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from graph import build_graph, reverse_dependencies
from mermaid import safe_filename, save_and_show, to_mermaid
from npm_registry import pick_version
from test_repo import TestRepository


def repo(name):
    return TestRepository(os.path.join(HERE, "repos", name))


class MermaidTest(unittest.TestCase):
    def test_simple(self):
        g = build_graph(repo("simple.txt"), "A")
        text = to_mermaid(g)
        self.assertTrue(text.startswith("flowchart TD\n"))
        for line in [
            'n0["A"]',
            "n0 --> n1",
            "n0 --> n3",
            "n1 --> n2",
            "n3 --> n2",
            "class n0 root",
        ]:
            self.assertIn(line, text)

    def test_cycle_edge_dashed(self):
        g = build_graph(repo("cycle.txt"), "A")
        text = to_mermaid(g)
        self.assertIn("n2 -.-> n0", text)
        self.assertEqual(text.count("-.->"), 1)

    def test_reverse_arrows_point_to_dependency(self):
        src = repo("reverse.txt")
        rev = reverse_dependencies(build_graph(src, "A"), "F", src.name_of)
        text = to_mermaid(rev, reverse=True)
        self.assertIn('n0["F"]', text)
        self.assertIn("n1 --> n0", text)
        self.assertIn("n2 --> n1", text)

    def test_labels_escaped(self):
        g = build_graph(repo("simple.txt"), "A")
        g.edges['say"hi"@1.0.0'] = []
        self.assertIn('"say#quot;hi#quot;@1.0.0"', to_mermaid(g))

    def test_safe_filename(self):
        self.assertEqual(safe_filename("@babel/core@8.1.2"), "babel_core_8.1.2")

    def test_files_saved(self):
        g = build_graph(repo("simple.txt"), "A")
        with tempfile.TemporaryDirectory() as d:
            text, mmd, html_path = save_and_show(g, "t", d, show=False)
            with open(mmd, encoding="utf-8") as f:
                self.assertEqual(f.read(), text)
            with open(html_path, encoding="utf-8") as f:
                self.assertIn('class="mermaid"', f.read())


class PickVersionTest(unittest.TestCase):
    versions = {
        "1.2.0": {},
        "1.3.0": {},
        "1.3.1": {},
        "1.4.0": {"deprecated": "bug"},
    }

    def test_latest_tag_preferred(self):
        self.assertEqual(
            pick_version(self.versions, {"latest": "1.3.0"}, "^1.2.0"), "1.3.0"
        )

    def test_latest_not_matching(self):
        self.assertEqual(
            pick_version(self.versions, {"latest": "1.3.0"}, "~1.2.0"), "1.2.0"
        )

    def test_deprecated_skipped(self):
        self.assertEqual(pick_version(self.versions, {}, "^1.2.0"), "1.3.1")
        self.assertEqual(pick_version(self.versions, {}, ">=1.4.0"), "1.4.0")


if __name__ == "__main__":
    unittest.main()
