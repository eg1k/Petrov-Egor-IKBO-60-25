"""Минимальная реализация семантического версионирования (SemVer) для npm.

Нужна, чтобы по диапазону версий из поля dependencies (например, ^1.2.0,
~1.8.1, >=2 <3, 1.x || 2.x) выбрать конкретную версию зависимости.
Поддерживаемый синтаксис диапазонов соответствует основным правилам
node-semver: точные версии, x-диапазоны, ~, ^, операторы сравнения,
диапазоны через дефис и объединение через ||.
"""

import operator
import re

VERSION_RE = re.compile(
    r"^\s*v?(\d+)\.(\d+)\.(\d+)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?\s*$"
)
PARTIAL_RE = re.compile(
    r"^v?(\d+|[xX*])(?:\.(\d+|[xX*])(?:\.(\d+|[xX*])"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?)?)?$"
)
COMPARATOR_RE = re.compile(r"^(<=|>=|<|>|=|~>|~|\^)?(.*)$")


class SemverError(ValueError):
    """Строка не является корректной версией или диапазоном версий."""


class Version:
    __slots__ = ("major", "minor", "patch", "prerelease", "text")

    def __init__(self, major, minor, patch, prerelease=(), text=None):
        self.major, self.minor, self.patch = major, minor, patch
        self.prerelease = tuple(prerelease)
        self.text = text or self._format()

    @classmethod
    def parse(cls, text):
        m = VERSION_RE.match(text)
        if not m:
            raise SemverError(f"некорректная версия {text!r}")
        pre = tuple(m.group(4).split(".")) if m.group(4) else ()
        return cls(
            int(m.group(1)), int(m.group(2)), int(m.group(3)), pre, text.strip()
        )

    def _format(self):
        s = f"{self.major}.{self.minor}.{self.patch}"
        return s + ("-" + ".".join(self.prerelease) if self.prerelease else "")

    def _key(self):
        """Ставит стабильную версию выше её предварительных версий."""
        if not self.prerelease:
            return (self.major, self.minor, self.patch, 1, ())
        ids = tuple(
            (0, int(p), "") if p.isdigit() else (1, 0, p)
            for p in self.prerelease
        )
        return (self.major, self.minor, self.patch, 0, ids)

    def __eq__(self, other):
        return self._key() == other._key()

    def __lt__(self, other):
        return self._key() < other._key()

    def __le__(self, other):
        return self._key() <= other._key()

    def __gt__(self, other):
        return self._key() > other._key()

    def __ge__(self, other):
        return self._key() >= other._key()

    def __hash__(self):
        return hash(self._key())

    def __repr__(self):
        return f"Version({self.text!r})"

    def __str__(self):
        return self.text


def _parse_partial(text):
    """'1.2' -> (1, 2, None, ()); 'x' -> (None, None, None, ())."""
    m = PARTIAL_RE.match(text)
    if not m:
        raise SemverError(f"некорректная версия в диапазоне: {text!r}")
    parts = []
    for g in m.group(1, 2, 3):
        parts.append(None if g is None or g in "xX*" else int(g))
    for i in range(1, 3):
        if parts[i - 1] is None:
            parts[i] = None
    pre = (
        tuple(m.group(4).split("."))
        if m.group(4) and parts[2] is not None
        else ()
    )
    return parts[0], parts[1], parts[2], pre


def _range_equal(major, minor, patch, pre):
    if major is None:
        return []
    if minor is None:
        return [(">=", Version(major, 0, 0)), ("<", Version(major + 1, 0, 0))]
    if patch is None:
        return [
            (">=", Version(major, minor, 0)),
            ("<", Version(major, minor + 1, 0)),
        ]
    return [("=", Version(major, minor, patch, pre))]


def _range_tilde(major, minor, patch, pre):
    if major is None:
        return []
    if minor is None:
        return [(">=", Version(major, 0, 0)), ("<", Version(major + 1, 0, 0))]
    return [
        (">=", Version(major, minor, patch or 0, pre)),
        ("<", Version(major, minor + 1, 0)),
    ]


def _range_caret(major, minor, patch, pre):
    if major is None:
        return []
    low = Version(major, minor or 0, patch or 0, pre)
    if major > 0 or minor is None:
        return [(">=", low), ("<", Version(major + 1, 0, 0))]
    if minor > 0 or patch is None:
        return [(">=", low), ("<", Version(0, minor + 1, 0))]
    return [(">=", low), ("<", Version(0, 0, patch + 1))]


def _range_greater(major, minor, patch, pre):
    if major is None:
        return [("<", Version(0, 0, 0))]
    if minor is None:
        return [(">=", Version(major + 1, 0, 0))]
    if patch is None:
        return [(">=", Version(major, minor + 1, 0))]
    return [(">", Version(major, minor, patch, pre))]


def _range_at_least(major, minor, patch, pre):
    if major is None:
        return []
    return [(">=", Version(major, minor or 0, patch or 0, pre))]


def _range_less(major, minor, patch, pre):
    if major is None:
        return [("<", Version(0, 0, 0))]
    return [("<", Version(major, minor or 0, patch or 0, pre))]


def _range_at_most(major, minor, patch, pre):
    if major is None:
        return []
    if minor is None:
        return [("<", Version(major + 1, 0, 0))]
    if patch is None:
        return [("<", Version(major, minor + 1, 0))]
    return [("<=", Version(major, minor, patch, pre))]


_RANGE_OPERATORS = {
    "": _range_equal,
    "=": _range_equal,
    "~": _range_tilde,
    "~>": _range_tilde,
    "^": _range_caret,
    ">": _range_greater,
    ">=": _range_at_least,
    "<": _range_less,
    "<=": _range_at_most,
}


def _comparators(op, text):
    """Переводит один элемент диапазона в список пар (оператор, Version)."""
    parts = _parse_partial(text)
    handler = _RANGE_OPERATORS.get(op)
    if handler is None:
        raise SemverError(f"неизвестный оператор {op!r}")
    return handler(*parts)


def _parse_set(text):
    """Одна часть диапазона (без ||): список пар (оператор, Version)."""
    text = text.strip()
    hyphen = re.match(r"^(\S+)\s+-\s+(\S+)$", text)
    if hyphen:
        major, minor, patch, pre = _parse_partial(hyphen.group(1))
        low = (
            []
            if major is None
            else [(">=", Version(major, minor or 0, patch or 0, pre))]
        )
        return low + _comparators("<=", hyphen.group(2))
    text = re.sub(r"(<=|>=|<|>|=|~>|~|\^)\s+", r"\1", text)
    result = []
    for token in text.split():
        op, ver = COMPARATOR_RE.match(token).groups()
        result.extend(_comparators(op or "", ver))
    return result


_MATCH_OPERATORS = {
    "=": operator.eq,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}


class Range:
    """Диапазон версий npm."""

    def __init__(self, text):
        self.text = text
        self.sets = [_parse_set(part) for part in text.split("||")]

    def _test_set(self, comps, v):
        """Для prerelease требует явную границу с той же основной версией."""
        if not all(_MATCH_OPERATORS[op](v, bound) for op, bound in comps):
            return False
        if v.prerelease:
            return any(
                b.prerelease
                and (b.major, b.minor, b.patch) == (v.major, v.minor, v.patch)
                for _, b in comps
            )
        return True

    def test(self, version):
        return any(self._test_set(s, version) for s in self.sets)


def max_satisfying(versions, range_text):
    """Возвращает наибольшую подходящую версию или None."""
    rng = Range(range_text)
    best = None
    for text in versions:
        try:
            v = Version.parse(text)
        except SemverError:
            continue
        if rng.test(v) and (best is None or v > best):
            best = v
    return best.text if best else None
