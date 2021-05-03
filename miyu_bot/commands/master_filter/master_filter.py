from __future__ import annotations

import asyncio
import dataclasses
import functools
import re
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from inspect import getfullargspec
from typing import Any, Optional, Union, Callable, List
from typing import TypeVar, Generic, Dict

import discord
from d4dj_utils.master.master_asset import MasterAsset
from discord.ext import commands

import miyu_bot.bot.bot
from miyu_bot.bot.bot import D4DJBot
from miyu_bot.commands.common.argument_parsing import ParsedArguments, list_operator_for, list_to_list_operator_for
from miyu_bot.commands.common.fuzzy_matching import FuzzyFilteredMap, romanize
from miyu_bot.commands.common.reaction_message import run_reaction_message, run_paged_message


class MasterFilterMeta(ABCMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        command_sources = []
        data_attributes = []
        for k, v in namespace.items():
            if data_info := getattr(v, '_data_attribute_info', False):
                data_attributes.append(data_info)
            if command_info := getattr(v, '_command_source_info', False):
                command_sources.append(command_info)
        namespace['_data_attributes'] = data_attributes
        namespace['_command_sources'] = command_sources
        return super().__new__(mcs, name, bases, namespace, **kwargs)


TData = TypeVar('TData', bound=MasterAsset)


class MasterFilter(Generic[TData], metaclass=MasterFilterMeta):
    _command_sources: List[CommandSourceInfo]
    _data_attributes: List[DataAttributeInfo]
    command_sources: List[CommandSourceInfo]
    data_attributes: List[DataAttributeInfo]

    def __init__(self, bot: D4DJBot, data: Dict[Any, TData], aliases: Dict[str, Any] = {}):
        self.bot = bot
        self.data = data
        self.default_filter = FuzzyFilteredMap(self.is_released)
        self.unrestricted_filter = FuzzyFilteredMap()
        for master in data.values():
            name = self.get_name(master)
            self.default_filter[name] = master
            self.unrestricted_filter[name] = master
        if aliases:
            for alias, mid in aliases.items():
                self.add_alias(alias, mid)
        self.command_sources = [dataclasses.replace(c) for c in self._command_sources]
        self.data_attributes = [dataclasses.replace(c) for c in self._data_attributes]

        for d in self.data_attributes:
            if init_function := d.init_function:
                init_function(self, d)

    def add_alias(self, alias, master_id):
        master = self.data[master_id]
        alias = romanize(alias)
        self.default_filter[alias] = master
        self.unrestricted_filter[alias] = master

    def get(self, name_or_id: Union[str, int], ctx: Optional[miyu_bot.bot.bot.PrefContext]):
        if ctx and ctx.preferences.leaks:
            try:
                return self.data[int(name_or_id)]
            except (KeyError, ValueError):
                if isinstance(name_or_id, int):
                    return None
                return self.unrestricted_filter[name_or_id]
        else:
            try:
                master = self.data[int(name_or_id)]
                if master not in self.default_filter.values():
                    master = self.default_filter[name_or_id]
                return master
            except (KeyError, ValueError):
                if isinstance(name_or_id, int):
                    return None
                return self.default_filter[name_or_id]

    def get_by_relevance(self, name: str, ctx: miyu_bot.bot.bot.PrefContext):
        try:
            master = self.data[int(name)]
            id_result = [master]
            if not ctx or (not ctx.preferences.leaks and master not in self.default_filter.values()):
                if master not in self.default_filter.values():
                    id_result = []
        except (KeyError, ValueError):
            id_result = []

        if name:
            if ctx.preferences.leaks:
                return id_result + self.unrestricted_filter.get_sorted(name)
            else:
                return id_result + self.default_filter.get_sorted(name)
        else:
            if ctx.preferences.leaks:
                return list(self.unrestricted_filter.values())
            else:
                return list(self.default_filter.values())

    def values(self, ctx: Optional[miyu_bot.bot.bot.PrefContext]):
        if ctx is not None and ctx.preferences.leaks:
            return self.unrestricted_filter.values()
        else:
            return self.default_filter.values()

    @abstractmethod
    def get_name(self, value: TData) -> str:
        pass

    def is_released(self, value: TData) -> bool:
        return value.is_released

    def get_current(self, ctx) -> Optional[TData]:
        return None

    def get_commands(self, include_self_parameter: bool = False):
        def wrap(f):
            async def wrapped(self, ctx, *, arg: Optional[ParsedArguments]):
                return await f(ctx, arg=arg)

            return wrapped

        for cs in self.command_sources:
            if include_self_parameter:
                if args := cs.command_args:
                    yield commands.command(**args)(wrap(self.get_primary_command_function(cs)))
                if args := cs.list_command_args:
                    yield commands.command(**args)(wrap(self.get_list_command_function(cs)))
            else:
                if args := cs.command_args:
                    yield commands.command(**args)(self.get_primary_command_function(cs))
                if args := cs.list_command_args:
                    yield commands.command(**args)(self.get_list_command_function(cs))

    def get_primary_command_function(self, source):
        if hasattr(source, '_command_source_info'):
            source = source._command_source_info

        flag_data_attributes = [a for a in self.data_attributes if a.is_flag]
        tag_data_attributes = [a for a in self.data_attributes if a.is_tag]
        keyword_data_attributes = [a for a in self.data_attributes if a.is_keyword]
        sortable_data_attributes = [a for a in self.data_attributes if a.is_sortable]
        comparable_data_attributes = [a for a in self.data_attributes if a.is_comparable]

        # is_comparable already includes the needed behavior (and really, only one of the two should be used).
        eq_data_attributes = [a for a in self.data_attributes if a.is_eq and not a.is_comparable]

        sort_arguments = {}
        for info in sortable_data_attributes:
            sort_arguments[info.name] = info
            for alias in info.aliases:
                sort_arguments[alias] = info

        async def command(ctx, *, arg: Optional[ParsedArguments]):
            arg = arg or await ParsedArguments.convert(ctx, '')
            sort = None
            reverse_sort = arg.tag('reverse')
            if sortable_data_attributes:
                sort, sort_op = arg.single_op('sort', None, allowed_operators=['<', '>', '='], converter=sort_arguments)
                if sort:
                    reverse_sort ^= (sort_op == '<') ^ sort.reverse_sort
            tag_arguments = {a: arg.tags(a.value_mapping.keys()) for a in tag_data_attributes}
            keyword_arguments = {a: arg.words(a.value_mapping.keys()) for a in keyword_data_attributes}
            flag_arguments = {a: bool(arg.tags([a.name] + a.aliases)) for a in flag_data_attributes}
            comparable_arguments = {
                a: arg.repeatable_op([a.name] + a.aliases, is_list=True,
                                     allowed_operators=['=', '==', '!=', '>', '<', '>=', '<='],
                                     converter=self.wrap_compare_converter(ctx, a.compare_converter) or (lambda s: float(s))) for a in
                comparable_data_attributes}
            eq_arguments = {
                a: arg.repeatable_op([a.name] + a.aliases, is_list=True,
                                     allowed_operators=['=', '==', '!='],
                                     converter=self.wrap_compare_converter(ctx, a.compare_converter) or a.value_mapping or (lambda s: float(s)))
                for a in eq_data_attributes}
            text = arg.text()

            arg.require_all_arguments_used()

            index = 0
            current = self.get_current(ctx)
            is_relative_only = re.fullmatch(r'[+-]\d+', arg.original.strip()) and current
            if is_relative_only:
                text = ''
            elif re.fullmatch(r'-\d+', text.strip()):
                index = int(text.strip()[1:]) - 1
                text = ''

            tab = source.default_tab
            if source.suffix_tab_aliases:
                words = text.split()
                if len(words) >= 2 and words[-1].lower() in source.suffix_tab_aliases:
                    tab = source.suffix_tab_aliases[words[-1].lower()]
                    text = ' '.join(words[:-1])

            values = self.get_by_relevance(text, ctx)

            for attr, tags in tag_arguments.items():
                if tags:
                    targets = {attr.value_mapping[t] for t in tags}
                    if attr.is_multi_category:
                        values = [v for v in values if targets.issubset(attr.accessor(self, ctx, v))]
                    else:
                        values = [v for v in values if attr.accessor(self, ctx, v) in targets]
            for attr, tags in keyword_arguments.items():
                if tags:
                    targets = {attr.value_mapping[t] for t in tags}
                    if attr.is_multi_category:
                        values = [v for v in values if targets.issubset(attr.accessor(self, ctx, v))]
                    else:
                        values = [v for v in values if attr.accessor(self, ctx, v) in targets]
            for attr, flag_present in flag_arguments.items():
                if flag_present:
                    if attr.flag_callback:
                        callback_value = attr.flag_callback(self, ctx, values)
                        if callback_value is not None:
                            values = callback_value
                    else:
                        values = [v for v in values if attr.accessor(self, ctx, v)]
            for attr, arguments in {**comparable_arguments, **eq_arguments}.items():
                for argument in arguments:
                    argument_value, operation = argument
                    if attr.is_multi_category:
                        operator = list_to_list_operator_for(operation)
                    else:
                        operator = list_operator_for(operation)
                    values = [v for v in values if operator(attr.accessor(self, ctx, v), argument_value)]

            if source.default_sort and not text:
                values = sorted(values, key=lambda v: source.default_sort.accessor(self, ctx, v))
                if source.default_sort.reverse_sort ^ bool(sort and reverse_sort):
                    values = values[::-1]
            if sort:
                values = sorted(values, key=lambda v: sort.accessor(self, ctx, v))
            if reverse_sort:
                values = values[::-1]

            if not values:
                await ctx.send('No results.')
                return

            if is_relative_only and current in values:
                index = values.index(current)
                index -= int(arg.original.strip())

            index = min(len(values) - 1, max(0, index))

            if source.tabs:
                message = await ctx.send(embed=source.embed_source(self, ctx, values[index], tab))

                emojis = [ctx.bot.get_emoji(e) if isinstance(e, int) else e for e in source.tabs] + ['◀', '▶']

                async def callback(emoji):
                    nonlocal tab
                    nonlocal index
                    try:
                        emoji_index = emojis.index(emoji)
                        if emoji_index < len(source.tabs):
                            tab = emoji_index
                        elif emoji_index == len(source.tabs):
                            index -= 1
                        else:
                            index += 1

                        index = min(len(values) - 1, max(0, index))

                        await message.edit(embed=source.embed_source(self, ctx, values[index], tab))
                    except ValueError:
                        pass

                asyncio.create_task(run_reaction_message(ctx, message, emojis, callback))
            else:
                message = await ctx.send(embed=source.embed_source(self, ctx, values[index]))

                emojis = ['◀', '▶']

                async def callback(emoji):
                    nonlocal index
                    try:
                        if emoji == '◀':
                            index -= 1
                        else:
                            index += 1

                        index = min(len(values) - 1, max(0, index))

                        await message.edit(embed=source.embed_source(self, ctx, values[index]))
                    except ValueError:
                        pass

                asyncio.create_task(run_reaction_message(ctx, message, emojis, callback))

        return command

    def get_list_command_function(self, source):
        if hasattr(source, '_command_source_info'):
            source = source._command_source_info

        if not source.list_formatter:
            raise ValueError('Command source does not have a list formatter.')

        flag_data_attributes = [a for a in self.data_attributes if a.is_flag]
        tag_data_attributes = [a for a in self.data_attributes if a.is_tag]
        keyword_data_attributes = [a for a in self.data_attributes if a.is_keyword]
        sortable_data_attributes = [a for a in self.data_attributes if a.is_sortable]
        comparable_data_attributes = [a for a in self.data_attributes if a.is_comparable]

        # is_comparable already includes the needed behavior (and really, only one of the two should be used).
        eq_data_attributes = [a for a in self.data_attributes if a.is_eq and not a.is_comparable]

        sort_arguments = {}
        for info in sortable_data_attributes:
            sort_arguments[info.name] = info
            for alias in info.aliases:
                sort_arguments[alias] = info

        async def command(ctx, *, arg: Optional[ParsedArguments]):
            arg = arg or await ParsedArguments.convert(ctx, '')
            sort = None
            display = None
            reverse_sort = arg.tag('reverse')
            if sortable_data_attributes:
                sort, sort_op = arg.single_op('sort', None, allowed_operators=['<', '>', '='], converter=sort_arguments)
                if sort:
                    reverse_sort ^= (sort_op == '<') ^ sort.reverse_sort
                display = arg.single(['display', 'disp'], sort if sort and sort.formatter else None,
                                     converter={**sort_arguments, 'none': None})
            tag_arguments = {a: arg.tags(a.value_mapping.keys()) for a in tag_data_attributes}
            keyword_arguments = {a: arg.words(a.value_mapping.keys()) for a in keyword_data_attributes}
            flag_arguments = {a: bool(arg.tags([a.name] + a.aliases)) for a in flag_data_attributes}
            comparable_arguments = {
                a: arg.repeatable_op([a.name] + a.aliases, is_list=True,
                                     allowed_operators=['=', '==', '!=', '>', '<', '>=', '<='],
                                     converter=self.wrap_compare_converter(ctx, a.compare_converter) or (lambda s: float(s))) for a in
                comparable_data_attributes}
            eq_arguments = {
                a: arg.repeatable_op([a.name] + a.aliases, is_list=True,
                                     allowed_operators=['=', '==', '!='],
                                     converter=self.wrap_compare_converter(ctx, a.compare_converter) or a.value_mapping or (lambda s: float(s)))
                for a in eq_data_attributes}
            text = arg.text()

            arg.require_all_arguments_used()

            values = self.get_by_relevance(text, ctx)

            for attr, tags in tag_arguments.items():
                if tags:
                    targets = {attr.value_mapping[t] for t in tags}
                    if attr.is_multi_category:
                        values = [v for v in values if targets.issubset(attr.accessor(self, ctx, v))]
                    else:
                        values = [v for v in values if attr.accessor(self, ctx, v) in targets]
            for attr, tags in keyword_arguments.items():
                if tags:
                    targets = {attr.value_mapping[t] for t in tags}
                    if attr.is_multi_category:
                        values = [v for v in values if targets.issubset(attr.accessor(self, ctx, v))]
                    else:
                        values = [v for v in values if attr.accessor(self, ctx, v) in targets]
            for attr, flag_present in flag_arguments.items():
                if flag_present:
                    if attr.flag_callback:
                        callback_value = attr.flag_callback(self, ctx, values)
                        if callback_value is not None:
                            values = callback_value
                    else:
                        values = [v for v in values if attr.accessor(self, ctx, v)]
            for attr, arguments in {**comparable_arguments, **eq_arguments}.items():
                for argument in arguments:
                    argument_value, operation = argument
                    if attr.is_multi_category:
                        operator = list_to_list_operator_for(operation)
                    else:
                        operator = list_operator_for(operation)
                    values = [v for v in values if operator(attr.accessor(self, ctx, v), argument_value)]

            display = display or source.default_display

            if source.default_sort and not text:
                values = sorted(values, key=lambda v: source.default_sort.accessor(self, ctx, v))
                if source.default_sort.reverse_sort ^ bool(sort and reverse_sort):
                    values = values[::-1]
            if sort:
                values = sorted(values, key=lambda v: sort.accessor(self, ctx, v))
            if reverse_sort:
                values = values[::-1]

            if display and display.formatter:
                listing = [f'{display.formatter(self, ctx, value)} {source.list_formatter(self, ctx,  value)}' for value in values]
            else:
                listing = [source.list_formatter(self, ctx, value) for value in values]

            embed = discord.Embed(title=source.list_name if source.list_name is not None else 'Search')
            asyncio.create_task(run_paged_message(ctx, embed, listing))

        return command

    def wrap_compare_converter(self, ctx, f):
        if f is None:
            return None
        else:
            argspec = getfullargspec(f)
            if len(argspec.args) == 2:
                return functools.partial(f, self)
            else:
                return functools.partial(f, self, ctx)

def _get_accessor(f):
    if len(getfullargspec(f).args) == 2:
        def accessor(self, ctx, value):
            return f(self, value)
        return accessor
    else:
        return f

@dataclass
class CommandSourceInfo:
    embed_source: Callable
    command_args: Optional[Dict] = None
    list_command_args: Optional[Dict] = None
    default_sort: Optional[DataAttributeInfo] = None
    default_display: Optional[DataAttributeInfo] = None
    tabs: Optional[List] = None
    default_tab: int = 0
    suffix_tab_aliases: Optional[Dict[str, int]] = None
    list_name: Optional[str] = None
    list_formatter: Optional[Callable] = None


def command_source(
        *,
        command_args: Optional[Dict] = None,
        list_command_args: Optional[Dict] = None,
        default_sort: Optional[Union[DataAttributeInfo, Callable]] = None,
        default_display: Optional[Union[DataAttributeInfo, Callable]] = None,
        tabs: Optional[List] = None,
        default_tab: int = 0,
        suffix_tab_aliases: Optional[Dict[str, int]] = None,
        list_name: Optional[str] = None,
):
    def decorator(func):
        info = CommandSourceInfo(
            command_args=command_args,
            list_command_args=list_command_args,
            embed_source=func,
            default_sort=getattr(default_sort, '_data_attribute_info', default_sort),
            default_display=getattr(default_display, '_data_attribute_info', default_display),
            tabs=tabs,
            default_tab=default_tab,
            suffix_tab_aliases=suffix_tab_aliases,
            list_name=list_name,
        )
        func._command_source_info = info

        def list_formatter(f):
            info.list_formatter = _get_accessor(f)
            return f

        func.list_formatter = list_formatter

        return func

    return decorator


@dataclass
class DataAttributeInfo:
    name: str
    aliases: List[str]
    description: Optional[str]
    accessor: Callable
    formatter: Optional[Callable] = None
    value_mapping: Optional[Dict[str, Any]] = None
    is_flag: bool = False
    flag_callback: Optional[Callable] = None
    is_tag: bool = False
    is_keyword: bool = False
    is_multi_category: bool = False
    is_sortable: bool = False
    reverse_sort: bool = False
    is_comparable: bool = False
    is_eq: bool = False
    compare_converter: Optional[Callable] = None
    init_function: Optional[Callable] = None

    def __hash__(self):
        return self.name.__hash__()


def data_attribute(
        name: str,
        *,
        aliases: Optional[List[str]] = None,
        description: Optional[str] = None,
        value_mapping: Optional[Dict[str, Any]] = None,
        is_flag: bool = False,
        is_tag: bool = False,
        is_keyword: bool = False,
        is_multi_category: bool = False,
        is_sortable: bool = False,
        reverse_sort: bool = False,
        is_comparable: bool = False,
        is_eq: bool = False,
):
    def decorator(func):
        info = DataAttributeInfo(
            name=name,
            aliases=aliases or [],
            description=description,
            accessor=_get_accessor(func),
            value_mapping=value_mapping,
            is_flag=is_flag,
            is_tag=is_tag,
            is_keyword=is_keyword,
            is_multi_category=is_multi_category,
            is_sortable=is_sortable,
            reverse_sort=reverse_sort,
            is_comparable=is_comparable,
            is_eq=is_eq,
        )
        func._data_attribute_info = info

        def formatter(f):
            info.formatter = _get_accessor(f)
            return f

        def compare_converter(f):
            info.compare_converter = f
            return f

        def flag_callback(f):
            info.flag_callback = _get_accessor(f)
            return f

        def init(f):
            info.init_function = f
            return f

        func.formatter = formatter
        func.compare_converter = compare_converter
        func.flag_callback = flag_callback
        func.init = init

        return func

    return decorator
