"""Парсер командной строки эмулятора.

Разбивает строку на слова с учётом кавычек и раскрывает переменные
окружения реальной ОС вида $VAR и ${VAR}. Внутри одинарных кавычек
переменные не раскрываются, внутри двойных — раскрываются.
"""

import os
import re

NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class ParseError(Exception):
    pass


def expand_variable(line, start, env):
    """Раскрывает переменную, начинающуюся с '$' в позиции start.

    Возвращает пару (значение, позиция после переменной).
    """
    i = start + 1
    if i < len(line) and line[i] == "{":
        end = line.find("}", i + 1)
        if end < 0:
            raise ParseError("незакрытая фигурная скобка в ${...}")
        name = line[i + 1:end]
        if not NAME_RE.fullmatch(name):
            raise ParseError("${%s}: неверная подстановка" % name)
        return env.get(name, ""), end + 1

    match = NAME_RE.match(line, i)
    if not match:
        # Одиночный '$' без имени переменной остаётся как есть
        return "$", i
    # Неопределённая переменная раскрывается в пустую строку, как в bash
    return env.get(match.group(), ""), match.end()


def parse(line, env=None):
    """Возвращает список слов команды после раскрытия переменных."""
    if env is None:
        env = os.environ
    tokens = []
    current = []
    in_token = False
    i = 0

    while i < len(line):
        c = line[i]
        if c.isspace():
            if in_token:
                tokens.append("".join(current))
                current = []
                in_token = False
            i += 1
        elif c == "'":
            end = line.find("'", i + 1)
            if end < 0:
                raise ParseError("незакрытая одинарная кавычка")
            current.append(line[i + 1:end])
            in_token = True
            i = end + 1
        elif c == '"':
            i += 1
            while i < len(line) and line[i] != '"':
                if line[i] == "\\" and i + 1 < len(line) and line[i + 1] in '"\\$':
                    current.append(line[i + 1])
                    i += 2
                elif line[i] == "$":
                    value, i = expand_variable(line, i, env)
                    current.append(value)
                else:
                    current.append(line[i])
                    i += 1
            if i >= len(line):
                raise ParseError("незакрытая двойная кавычка")
            in_token = True
            i += 1
        elif c == "\\":
            if i + 1 < len(line):
                current.append(line[i + 1])
            in_token = True
            i += 2
        elif c == "$":
            value, i = expand_variable(line, i, env)
            current.append(value)
            in_token = True
        else:
            current.append(c)
            in_token = True
            i += 1

    if in_token:
        tokens.append("".join(current))
    return tokens
