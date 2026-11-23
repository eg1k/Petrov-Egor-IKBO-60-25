"""Translate variant 23 configuration text into Python values."""

from pathlib import Path

from lark import Lark, Token, Transformer, UnexpectedInput, v_args
from lark.exceptions import VisitError


GRAMMAR = Path(__file__).with_name("config.lark")
PARSER = Lark(GRAMMAR.read_text(encoding="utf-8"), parser="lalr")
QUOTE_LENGTH = 1


class ConfigError(ValueError):
    """Report an invalid configuration."""


def location(token):
    """Format the source position of a token."""
    return f"строка {token.line}, столбец {token.column}"


@v_args(inline=True)
class Evaluate(Transformer):
    """Evaluate declarations and substitute references in source order."""

    def __init__(self):
        super().__init__()
        self.constants = {}

    def start(self, *items):
        return items[-1]

    def integer(self, token):
        try:
            return int(token)
        except ValueError as error:
            raise ConfigError(
                f"{location(token)}: целое число слишком длинное"
            ) from error

    def string(self, token):
        return token[QUOTE_LENGTH:-QUOTE_LENGTH]

    def entry(self, name, value):
        return name, value

    def dictionary(self, *entries):
        result = {}
        for name, value in entries:
            if name in result:
                raise ConfigError(
                    f"{location(name)}: повторный ключ «{name}»"
                )
            result[str(name)] = value
        return result

    def declaration(self, value, name):
        if name in self.constants:
            raise ConfigError(
                f"{location(name)}: повторное объявление «{name}»"
            )
        self.constants[name] = value

    def reference(self, name):
        try:
            return self.constants[name]
        except KeyError as error:
            raise ConfigError(
                f"{location(name)}: неизвестная константа «{name}»"
            ) from error


def translate(source):
    """Parse source and return the value to serialize as JSON."""
    try:
        return Evaluate().transform(PARSER.parse(source))
    except UnexpectedInput as error:
        token = getattr(error, "token", None)
        if isinstance(token, Token) and token.type == "$END":
            raise ConfigError("неожиданный конец файла") from error
        context = error.get_context(source).rstrip()
        raise ConfigError(
            f"{location(error)}: синтаксическая ошибка\n{context}"
        ) from error
    except VisitError as error:
        if isinstance(error.orig_exc, ConfigError):
            raise error.orig_exc from error
        raise
