"""Модульные тесты подбора версий по диапазонам npm."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from semver import SemverError, Version, max_satisfying  # noqa: E402

VERSIONS = ["0.9.0", "1.0.0", "1.2.0", "1.2.5", "1.3.0-beta.1", "1.3.0",
            "1.10.1", "2.0.0-rc.1", "2.0.0", "2.4.1", "3.0.0"]


class SemverTest(unittest.TestCase):
    def check(self, rng, expected):
        self.assertEqual(max_satisfying(VERSIONS, rng), expected, rng)

    def test_order(self):
        self.assertLess(Version.parse("1.3.0-beta.1"), Version.parse("1.3.0"))
        self.assertLess(Version.parse("1.3.0-beta.2"), Version.parse("1.3.0-beta.10"))
        self.assertLess(Version.parse("1.9.0"), Version.parse("1.10.0"))

    def test_exact_and_wildcards(self):
        self.check("1.2.0", "1.2.0")
        self.check("=1.2.5", "1.2.5")
        self.check("*", "3.0.0")
        self.check("", "3.0.0")
        self.check("1.x", "1.10.1")
        self.check("1.2.*", "1.2.5")
        self.check("2", "2.4.1")

    def test_tilde_and_caret(self):
        self.check("~1.2.0", "1.2.5")
        self.check("~1", "1.10.1")
        self.check("^1.2.0", "1.10.1")
        self.check("^0.9.0", "0.9.0")
        self.check("^2.0.0-rc.1", "2.4.1")

    def test_comparators(self):
        self.check(">=1.2.0 <1.3.0", "1.2.5")
        self.check(">= 2", "3.0.0")
        self.check("<2", "1.10.1")
        self.check("<=1.2", "1.2.5")
        self.check(">1.10", "3.0.0")
        self.check(">1.10 <3", "2.4.1")
        self.check(">1.10.1 <2", None)
        self.check("1.0.0 - 1.2", "1.2.5")
        self.check("^5.0.0 || ~1.2.0", "1.2.5")
        self.check("^9.0.0", None)

    def test_prerelease_excluded(self):
        self.check(">=1.2.6 <1.3.0", None)
        self.check(">=2.0.0-rc.0 <2.0.0", "2.0.0-rc.1")

    def test_invalid(self):
        with self.assertRaises(SemverError):
            max_satisfying(VERSIONS, "git+https://example.com/repo.git")
        with self.assertRaises(SemverError):
            Version.parse("1.2")


if __name__ == "__main__":
    unittest.main()
