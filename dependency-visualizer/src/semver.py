"""Минимальная реализация семантического версионирования (SemVer) для npm.

Нужна, чтобы по диапазону версий из поля dependencies (например, ^1.2.0,
~1.8.1, >=2 <3, 1.x || 2.x) выбрать конкретную версию зависимости.
Поддерживаемый синтаксис диапазонов соответствует основным правилам
node-semver: точные версии, x-диапазоны, ~, ^, операторы сравнения,
диапазоны через дефис и объединение через ||.
"""

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
        return cls(int(m.group(1)), int(m.group(2)), int(m.group(3)), pre, text.strip())

    def _format(self):
        s = f"{self.major}.{self.minor}.{self.patch}"
        return s + ("-" + ".".join(self.prerelease) if self.prerelease else "")

    def _key(self):
        # Версия без prerelease старше любой своей prerelease-версии.
        if not self.prerelease:
            return (self.major, self.minor, self.patch, 1, ())
        ids = tuple((0, int(p), "") if p.isdigit() else (1, 0, p) for p in self.prerelease)
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
    # После подстановочного символа все младшие части тоже подстановочные.
    for i in range(1, 3):
        if parts[i - 1] is None:
            parts[i] = None
    pre = tuple(m.group(4).split(".")) if m.group(4) and parts[2] is not None else ()
    return parts[0], parts[1], parts[2], pre


def _comparators(op, text):
    """Переводит один элемент диапазона в список пар (оператор, Version)."""
    M, m, p, pre = _parse_partial(text)
    V = Version
    if op in ("", "="):
        if M is None:
            return []
        if m is None:
            return [(">=", V(M, 0, 0)), ("<", V(M + 1, 0, 0))]
        if p is None:
            return [(">=", V(M, m, 0)), ("<", V(M, m + 1, 0))]
        return [("=", V(M, m, p, pre))]
    if op in ("~", "~>"):
        if M is None:
            return []
        if m is None:
            return [(">=", V(M, 0, 0)), ("<", V(M + 1, 0, 0))]
        return [(">=", V(M, m, p or 0, pre)), ("<", V(M, m + 1, 0))]
    if op == "^":
        if M is None:
            return []
        low = V(M, m or 0, p or 0, pre)
        if M > 0 or m is None:
            return [(">=", low), ("<", V(M + 1, 0, 0))]
        if m > 0 or p is None:
            return [(">=", low), ("<", V(0, m + 1, 0))]
        return [(">=", low), ("<", V(0, 0, p + 1))]
    if op == ">":
        if M is None:
            return [("<", V(0, 0, 0))]  # ничему не удовлетворяет
        if m is None:
            return [(">=", V(M + 1, 0, 0))]
        if p is None:
            return [(">=", V(M, m + 1, 0))]
        return [(">", V(M, m, p, pre))]
    if op == ">=":
        if M is None:
            return []
        return [(">=", V(M, m or 0, p or 0, pre))]
    if op == "<":
        if M is None:
            return [("<", V(0, 0, 0))]
        return [("<", V(M, m or 0, p or 0, pre))]
    if op == "<=":
        if M is None:
            return []
        if m is None:
            return [("<", V(M + 1, 0, 0))]
        if p is None:
            return [("<", V(M, m + 1, 0))]
        return [("<=", V(M, m, p, pre))]
    raise SemverError(f"неизвестный оператор {op!r}")


def _parse_set(text):
    """Одна часть диапазона (без ||): список пар (оператор, Version)."""
    text = text.strip()
    hyphen = re.match(r"^(\S+)\s+-\s+(\S+)$", text)
    if hyphen:
        M, m, p, pre = _parse_partial(hyphen.group(1))
        low = [] if M is None else [(">=", Version(M, m or 0, p or 0, pre))]
        return low + _comparators("<=", hyphen.group(2))
    # Убираем пробелы между оператором и версией: ">= 1.2" -> ">=1.2".
    text = re.sub(r"(<=|>=|<|>|=|~>|~|\^)\s+", r"\1", text)
    result = []
    for token in text.split():
        op, ver = COMPARATOR_RE.match(token).groups()
        result.extend(_comparators(op or "", ver))
    return result


class Range:
    """Диапазон версий npm."""

    def __init__(self, text):
        self.text = text
        self.sets = [_parse_set(part) for part in text.split("||")]

    def _test_set(self, comps, v):
        for op, bound in comps:
            if op == "=" and not v == bound:
                return False
            if op == ">" and not v > bound:
                return False
            if op == ">=" and not v >= bound:
                return False
            if op == "<" and not v < bound:
                return False
            if op == "<=" and not v <= bound:
                return False
        if v.prerelease:
            # Prerelease-версия подходит, только если в диапазоне явно
            # указана prerelease-версия с теми же MAJOR.MINOR.PATCH.
            return any(
                b.prerelease and (b.major, b.minor, b.patch) == (v.major, v.minor, v.patch)
                for _, b in comps
            )
        return True

    def test(self, version):
        return any(self._test_set(s, version) for s in self.sets)


def max_satisfying(versions, range_text):
    """Наибольшая версия из versions (строки), подходящая под диапазон, или None."""
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
