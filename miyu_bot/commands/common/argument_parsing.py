import re

from collections import namedtuple
from types import SimpleNamespace
from typing import Dict, List, Optional, Container, Any, Union, Callable, Set, Iterable

# https://stackoverflow.com/questions/249791/regex-for-quoted-string-with-escaping-quotes
# https://stackoverflow.com/questions/21105360/regex-find-comma-not-inside-quotes
# The ` ?` is just so it matches the space after during the replace with blank so there's no double spaces
from discord.ext.commands import CommandError, BadArgument

from miyu_bot.bot.models import all_preferences
from miyu_bot.commands.cogs.preferences import get_preferences

_param_re = re.compile(
    r'(([a-zA-Z_+/.\-]+)(!=|>=|<=|>|<|==|=)(("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[^,\s]+)(,("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[^,\s]+))*)) ?')
# The intention of having both = and == is that they might have different behavior.
# What that means depends on the usage.
_param_operator_re = re.compile(r'!=|==|=|>|<|>=|<=')
_param_argument_re = re.compile(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[^,\s]+)')
_param_string_re = re.compile(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')')

_tag_re = re.compile(r'(\$[^\s]+) ?')

NamedArgument = namedtuple('NamedArgument', 'name operator value')
ArgumentValue = namedtuple('ArgumentValue', 'value operator')


def _parse_named_argument(arg):
    groups = _param_re.fullmatch(arg).groups()
    name = groups[1]
    operator = groups[2]
    values = [value[1:-1] if _param_string_re.fullmatch(value) else value for value in
              _param_argument_re.findall(groups[3])]
    return NamedArgument(name.lower(), operator, values)


def parse_arguments(arg):
    # Note: this lowercases tags, words, and argument names

    original = arg
    named_arguments_parsed = [_parse_named_argument(na[0]) for na in _param_re.findall(arg)]
    arg = _param_re.sub('', arg)
    # Technically, the order (named arguments then tags)
    # matters because otherwise a fake tag could appear as a value to a named argument
    tags = [t[1:].lower() for t in _tag_re.findall(arg)]
    arg = _tag_re.sub('', arg)
    named_arguments = {}
    for na in named_arguments_parsed:
        if na.name not in named_arguments:
            named_arguments[na.name] = []
        named_arguments[na.name].append(ArgumentValue(na.value, na.operator))
    return ParsedArguments(original, arg.strip(), set(tags), named_arguments)


class ArgumentError(BadArgument):
    pass


class ParsedArguments:
    text_argument: str
    word_arguments: Set[str]
    tag_arguments: Set[str]
    named_arguments: Dict[str, List[ArgumentValue]]

    def __init__(self, original: str, text: str, tags: Set[str], named_arguments: Dict[str, List[ArgumentValue]]):
        self.original = original
        self.text_argument = text
        self.word_arguments = set(word.lower() for word in text.split())
        self.tag_arguments = tags
        self.named_arguments = named_arguments
        self.used_named_arguments = set()
        self.used_tags = set()
        self.used_words = set()

    def word(self, value: str):
        if value in self.word_arguments:
            self.used_words.add(value)
            return True
        return False

    def words(self, values: Optional[Iterable[str]] = None, aliases: Optional[Dict[str, str]] = None):
        results = set()
        if values is not None:
            for value in values:
                if value in self.word_arguments:
                    results.add(value)
                    self.used_words.add(value)
        if aliases is not None:
            for alias, value in aliases.items():
                if alias in self.word_arguments:
                    results.add(value)
                    self.used_words.add(alias)
        return results

    def text(self):
        return ' '.join(word for word in self.text_argument.split() if word.lower() not in self.used_words)

    def tag(self, name: str):
        if name in self.tag_arguments:
            self.used_tags.add(name)
            return True
        return False

    def tags(self, names: Optional[Iterable[str]] = None, aliases: Optional[Dict[str, str]] = None):
        results = set()
        if names is not None:
            for name in names:
                if name in self.tag_arguments:
                    results.add(name)
                    self.used_tags.add(name)
        if aliases is not None:
            for alias, value in aliases.items():
                if alias in self.tag_arguments:
                    results.add(value)
                    self.used_tags.add(alias)
        return results

    def has_named(self, name: str):
        return name in self.named_arguments

    def single(self, names: Union[List[str], str], default: Any = None,
               is_list=False, numeric=False, converter: Union[dict, Callable] = lambda n: n):
        return self.single_op(names, default, ['='], is_list, numeric, converter)[0]

    def single_op(self, names: Union[List[str], str], default: Any = None,
                  allowed_operators: Optional[Container] = None,
                  is_list=False, numeric=False, converter: Union[dict, Callable] = lambda n: n):
        if allowed_operators is None:
            allowed_operators = ['=']
        if not isinstance(default, tuple):
            default = ArgumentValue(default, '=')
        if not isinstance(names, list):
            names = [names]
        for name in names:
            self.used_named_arguments.add(name)
        name = f'{names[0]} ({", ".join(names[1:])})' if len(names) > 1 else names[0]
        value = [arg for args in (self.named_arguments.get(name) for name in names) if args for arg in args]
        if not value:
            return default
        if len(value) != 1:
            raise ArgumentError(f'Expected only one value for parameter "{name}".')
        value = value[0]
        if value.operator not in allowed_operators:
            raise ArgumentError(
                f'Allowed operators for parameter "{name}" are {", ".join(str(o) for o in allowed_operators)}.')
        if numeric:
            try:
                value = ArgumentValue([float(v) for v in value.value], value.operator)
            except ValueError:
                raise ArgumentError(f'Expected numerical arguments for parameter "{name}".')
        try:
            if isinstance(converter, dict):
                value = ArgumentValue([converter[v.lower()] for v in value.value], value.operator)
            else:
                value = ArgumentValue([converter(v) for v in value.value], value.operator)
        except Exception:
            raise ArgumentError(f'Invalid value for parameter "{name}".')
        if not is_list:
            if len(value.value) != 1:
                raise ArgumentError(f'List not allowed for parameter "{name}".')
            value = ArgumentValue(value.value[0], value.operator)
        return value

    def repeatable_op(self, names: Union[List[str], str], default: Any = None,
                      allowed_operators: Optional[Container] = None,
                      is_list=False, numeric=False, converter: Union[dict, Callable] = lambda n: n):
        if allowed_operators is None:
            allowed_operators = ['=']
        if not isinstance(default, tuple) and default is not None:
            default = [ArgumentValue(default, '=')]
        if default is None:
            default = []
        if not isinstance(names, list):
            names = [names]
        for name in names:
            self.used_named_arguments.add(name)
        name = f'{names[0]} ({", ".join(names[1:])})' if len(names) > 1 else names[0]
        values = [arg for args in (self.named_arguments.get(name) for name in names) if args for arg in args]
        if not values:
            return default
        if any(value.operator not in allowed_operators for value in values):
            raise ArgumentError(
                f'Allowed operators for parameter "{name}" are {", ".join(str(o) for o in allowed_operators)}.')
        if numeric:
            try:
                values = [ArgumentValue([float(v) for v in value.value], value.operator) for value in values]
            except ValueError:
                raise ArgumentError(f'Expected numerical arguments for parameter "{name}".')
        try:
            if isinstance(converter, dict):
                values = [ArgumentValue([converter[v.lower()] for v in value.value], value.operator) for value in values]
            else:
                values = [ArgumentValue([converter(v) for v in value.value], value.operator) for value in values]
        except Exception:
            raise ArgumentError(f'Invalid value for parameter "{name}".')
        if not is_list:
            if any(len(value.value) != 1 for value in values):
                raise ArgumentError(f'List not allowed for parameter "{name}".')
            values = [ArgumentValue(value.value[0], value.operator) for value in values]
        return values

    def has_unused(self):
        return self.has_unused_named_arguments() or self.has_unused_tags()

    def has_unused_named_arguments(self):
        return any(name not in self.used_named_arguments for name in self.named_arguments.keys())

    def has_unused_tags(self):
        return any(t not in self.used_tags for t in self.tag_arguments)

    def require_all_arguments_used(self):
        def quote(s):
            return f'"{s}"'

        if self.has_unused_named_arguments():
            raise ArgumentError(
                f'Unknown arguments with names {", ".join(quote(v) for v in self.named_arguments.keys() if v not in self.used_named_arguments)}.')
        if self.has_unused_tags():
            raise ArgumentError(
                f'Unknown tags {", ".join(quote(v) for v in self.tag_arguments if v not in self.used_tags)}.')

    async def preferences(self, ctx):
        preference_values = await get_preferences(ctx, self.tag('p'))
        for name in preference_values.keys():
            preference = all_preferences[name]
            override = self.single(name)
            if override:
                if preference.is_privileged and not await ctx.bot.is_owner(ctx.author):
                    raise ArgumentError(f'Privileged preference.')
                if error_message := preference.validate_or_get_error_message(override):
                    raise ArgumentError(f'Invalid value "{override}" for preference "{name}": {error_message}')
                preference_values[name] = preference.convert(preference.transform(override))
        return preference_values

    async def update_preferences(self, ctx):
        ctx.preferences = SimpleNamespace(**await self.preferences(ctx))

    @classmethod
    async def convert(cls, ctx, argument):
        value = parse_arguments(argument)
        await value.update_preferences(ctx)
        return value


_operators = {
    '=': lambda a, b: a == b,
    '==': lambda a, b: a == b,
    '!=': lambda a, b: a != b,
    '>': lambda a, b: a > b,
    '<': lambda a, b: a < b,
    '>=': lambda a, b: a >= b,
    '<=': lambda a, b: a <= b,
}

_list_operators = {
    '=': lambda a, b: any(a == v for v in b),
    '==': lambda a, b: all(a == v for v in b),  # Not very useful when b has more than one element
    '!=': lambda a, b: all(a != v for v in b),
    '>': lambda a, b: all(a > v for v in b),
    '<': lambda a, b: all(a < v for v in b),
    '>=': lambda a, b: all(a >= v for v in b),
    '<=': lambda a, b: all(a <= v for v in b),
}

_list_to_list_operators = {
    '=': lambda a, b: not set(a).isdisjoint(b),
    '==': lambda a, b: set(b).issubset(set(a)),
    '!=': lambda a, b: set(a).isdisjoint(b),
    '>': lambda a, b: all(u > v for v in b for u in a),  # Also not very useful when b has more than one element
    '<': lambda a, b: all(u < v for v in b for u in a),  # Same here and below
    '>=': lambda a, b: all(u >= v for v in b for u in a),
    '<=': lambda a, b: all(u <= v for v in b for u in a),
}

full_operators = {'>', '<', '>=', '<=', '!=', '==', '='}


def operator_for(operator: str):
    return _operators[operator]


def list_operator_for(operator: str):
    return _list_operators[operator]


def list_to_list_operator_for(operator: str):
    return _list_to_list_operators[operator]
