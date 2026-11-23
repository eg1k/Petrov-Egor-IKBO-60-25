"""Exercise the grammar, evaluation, examples and CLI."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

from src.translator import ConfigError, translate


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "src" / "main.py"


class TranslatorTests(unittest.TestCase):
    def test_literals_and_empty_dictionary(self):
        examples = (
            ("13", 13),
            ("+8", 8),
            ("-2", -2),
            ("'Пример'", "Пример"),
            ("''", ""),
            ("begin end", {}),
        )
        for source, expected in examples:
            with self.subTest(source=source):
                self.assertEqual(translate(source), expected)

    def test_comments_and_nested_references(self):
        source = """
        %{ многострочный
           комментарий %}
        +2 -> number
        begin inner := begin n := ![number]; end; end -> box
        ![box] -> alias
        begin _key := ![alias]; marker := '%{ текст %}'; end
        """
        expected = {"_key": {"inner": {"n": 2}}, "marker": "%{ текст %}"}
        self.assertEqual(translate(source), expected)

    def test_invalid_syntax(self):
        examples = (
            "",
            "begin x := 2 end",
            "begin x1 := 2; end",
            "begin x := 2;",
            "'unterminated",
            "%{ unterminated",
            "1 2",
            "1 -> name",
        )
        for source in examples:
            with self.subTest(source=source):
                with self.assertRaises(ConfigError):
                    translate(source)

    def test_invalid_constant_or_key(self):
        examples = (
            ("![unknown]", "неизвестная константа"),
            ("![b] -> a 1 -> b ![a]", "неизвестная константа"),
            ("1 -> a 2 -> a ![a]", "повторное объявление"),
            ("begin a := 1; a := 2; end", "повторный ключ"),
        )
        for source, message in examples:
            with self.subTest(source=source):
                with self.assertRaisesRegex(ConfigError, message):
                    translate(source)

    def test_cli_examples(self):
        examples = {
            "data-center.conf": {
                "location": "Москва",
                "gateway": {"protocol": "https", "listen": 443},
            },
            "museum.conf": {
                "title": "Музей космонавтики",
                "guided_tour": {"language": "русский", "capacity": 20},
                "coat_check": {"floor": -1},
            },
        }
        for name, expected in examples.items():
            with self.subTest(name=name):
                result = run_cli(ROOT / "examples" / name)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertEqual(json.loads(result.stdout), expected)

    def test_cli_missing_file(self):
        result = run_cli(ROOT / "missing.conf")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("missing.conf", result.stderr)


def run_cli(path):
    """Capture the UTF-8 output and exit status of the command."""
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(CLI), "--input", str(path)],
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
