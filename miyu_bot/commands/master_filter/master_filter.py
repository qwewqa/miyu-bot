"""
Master filter class and related functions.
"""

from __future__ import annotations

import dataclasses
import functools
import re
from abc import abstractmethod, ABCMeta
from collections import defaultdict
from dataclasses import dataclass
from inspect import getfullargspec
from typing import Any, Optional, Union, Callable, List, Sequence, Protocol, NamedTuple, Tuple
from typing import TypeVar, Generic, Dict

import discord
from d4dj_utils.master.master_asset import MasterAsset
from discord.ext import commands

import miyu_bot.bot.bot
from miyu_bot.bot.bot import MiyuBot, PrefContext
from miyu_bot.bot.servers import Server
from miyu_bot.commands.common.argument_parsing import ParsedArguments, list_operator_for, list_to_list_operator_for
from miyu_bot.commands.common.fuzzy_matching import FuzzyFilteredMap
from miyu_bot.commands.master_filter.filter_display_manager import FilterDisplayManager
from miyu_bot.commands.master_filter.localization_manager import LocalizationManager


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
    # Note: only works for masters that have an id field

    _command_sources: List[CommandSourceInfo]
    _data_attributes: List[DataAttributeInfo]
    command_sources: List[CommandSourceInfo]
    data_attributes: List[DataAttributeInfo]
    l10n: LocalizationManager

    def __init__(self, bot: MiyuBot, master_name: str, name: str):
        self.name = name
        self.bot = bot
        self.master_name = master_name
        self.default_filter = defaultdict(lambda: FuzzyFilteredMap(self.is_released))
        self.unrestricted_filter = defaultdict(lambda: FuzzyFilteredMap())
        self.command_sources = [dataclasses.replace(c) for c in self._command_sources]
        self.data_attributes = [dataclasses.replace(c) for c in self._data_attributes]
        self.l10n = LocalizationManager(self.bot.fluent_loader, self.name + '.ftl')
        for d in self.data_attributes:
            if init_function := d.init_function:
                init_function(self, d)

        # Skips the more time consuming loading when generating docs
        if getattr(bot, 'gen_doc', False):
            return

        for server, manager in bot.assets.items():
            masters = manager.masters[self.master_name]
            for master in masters.values():
                alias = self.get_name(master)
                self.default_filter[server][alias] = master
                self.unrestricted_filter[server][alias] = master
        for server, manager in bot.assets.items():
            masters = manager.masters[self.master_name]
            for alias_source_server in bot.assets.keys():
                if alias_source_server == server:
                    continue
                for alias, alias_server_value in self.unrestricted_filter[alias_source_server].filtered_items:
                    if alias_server_value.id in manager.masters[self.master_name]:
                        self.default_filter[server][alias] = masters[alias_server_value.id]
                        self.unrestricted_filter[server][alias] = masters[alias_server_value.id]

    def get_asset_source(self, ctx: Optional[miyu_bot.bot.bot.PrefContext], server=None):
        if server is None:
            if ctx is None:
                server = Server.JP
            else:
                server = ctx.preferences.server
        return self.bot.assets[server][self.master_name]

    def get(self, name_or_id: Union[str, int], ctx: Optional[miyu_bot.bot.bot.PrefContext]):
        if ctx and ctx.preferences.leaks:
            try:
                return self.get_asset_source(ctx)[int(name_or_id)]
            except (KeyError, ValueError):
                if isinstance(name_or_id, int):
                    return None
                return self.unrestricted_filter[ctx.preferences.server][name_or_id]
        else:
            try:
                master = self.get_asset_source(ctx)[int(name_or_id)]
                if master not in self.default_filter[ctx.preferences.server].values():
                    master = self.default_filter[ctx.preferences.server][name_or_id]
                return master
            except (KeyError, ValueError):
                if isinstance(name_or_id, int):
                    return None
                return self.default_filter[ctx.preferences.server][name_or_id]

    def get_by_id(self, master_id: int, ctx: Optional[miyu_bot.bot.bot.PrefContext], server=None):
        if server is None:
            server = ctx.preferences.server
        if ctx and ctx.preferences.leaks:
            try:
                return self.get_asset_source(ctx, server)[master_id]
            except KeyError:
                return None
        else:
            try:
                master = self.get_asset_source(ctx, server)[master_id]
                if master not in self.default_filter[server].values():
                    return None
                return master
            except KeyError:
                return None

    def get_by_relevance(self, name: str, ctx: miyu_bot.bot.bot.PrefContext):
        try:
            master = self.get_asset_source(ctx)[int(name)]
            id_result = [master]
            if not ctx.preferences.leaks and master not in self.default_filter[ctx.preferences.server].values():
                if master not in self.default_filter[ctx.preferences.server].values():
                    id_result = []
        except (KeyError, ValueError):
            id_result = []

        if name:
            if ctx.preferences.leaks:
                return id_result + [v for v in self.unrestricted_filter[ctx.preferences.server].get_sorted(name)
                                    if v not in id_result]
            else:
                return id_result + [v for v in self.default_filter[ctx.preferences.server].get_sorted(name)
                                    if v not in id_result]
        else:
            if ctx.preferences.leaks:
                return list(self.unrestricted_filter[ctx.preferences.server].values())
            else:
                return list(self.default_filter[ctx.preferences.server].values())

    def values(self, ctx: Optional[miyu_bot.bot.bot.PrefContext]):
        if ctx is not None and ctx.preferences.leaks:
            return self.unrestricted_filter[ctx.preferences.server].values()
        elif ctx:
            return self.default_filter[ctx.preferences.server].values()
        else:
            return self.default_filter[Server.JP].values()

    @abstractmethod
    def get_name(self, value: TData) -> str:
        pass

    def get_select_name(self, value: TData) -> Tuple[str, str, Optional[AnyEmoji]]:
        return 'name', 'desc', None

    def is_released(self, value: TData) -> bool:
        return value.is_released

    def get_current(self, ctx) -> Optional[TData]:
        return None

    def get_commands(self, include_self_parameter: bool = False):
        def wrap(f):
            # Note how a default argument used, so that the error propagates properly
            async def wrapped(self, ctx, *, arg: ParsedArguments = None):
                return await f(ctx, arg=arg)

            return wrapped

        for cs in self.command_sources:
            if include_self_parameter:
                if args := cs.command_args:
                    yield commands.command(**{**args,
                                              'description': args.get('description',
                                                                      'No Description')})(
                        wrap(self.get_detail_command_function(cs)))
                if args := cs.list_command_args:
                    yield commands.command(**{**args,
                                              'description': args.get('description',
                                                                      'No Description')})(
                        wrap(self.get_list_command_function(cs)))
            else:
                if args := cs.command_args:
                    yield commands.command(**{**args,
                                              'description': args.get('description',
                                                                      'No Description')})(
                        self.get_detail_command_function(cs))
                if args := cs.list_command_args:
                    yield commands.command(**{**args,
                                              'description': args.get('description',
                                                                      'No Description')})(
                        self.get_list_command_function(cs))

    def get_detail_command_function(self, source):
        if hasattr(source, '_command_source_info'):
            source = source._command_source_info

        filter_processor = FilterProcessor(self, source)

        async def command(ctx, *, arg: Optional[ParsedArguments]):
            arg = arg or await ParsedArguments.convert(ctx, '')
            results = filter_processor.get(arg, ctx, is_list=False)
            view, embed = FilterDisplayManager(self, ctx, results, source).get_detail_view()
            await ctx.send(embed=embed, view=view)

        return command

    def get_list_command_function(self, source):
        if hasattr(source, '_command_source_info'):
            source = source._command_source_info

        if not source.list_formatter:
            raise ValueError('Command source does not have a list formatter.')

        filter_processor = FilterProcessor(self, source)

        async def command(ctx, *, arg: Optional[ParsedArguments]):
            arg = arg or await ParsedArguments.convert(ctx, '')
            results = filter_processor.get(arg, ctx, is_list=True)
            view, embed = FilterDisplayManager(self, ctx, results, source).get_list_view()
            await ctx.send(embed=embed, view=view)

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


class FilterProcessor:
    def __init__(self, master_filter: MasterFilter, source: CommandSourceInfo):
        self.master_filter = master_filter
        self.source = source
        data_attributes = master_filter.data_attributes
        self.flag_data_attributes = [a for a in data_attributes if a.is_flag]
        self.tag_data_attributes = [a for a in data_attributes if a.is_tag]
        self.keyword_data_attributes = [a for a in data_attributes if a.is_keyword]
        self.sortable_data_attributes = [a for a in data_attributes if a.is_sortable]
        self.comparable_data_attributes = [a for a in data_attributes if a.is_comparable]

        # is_comparable already includes eq behavior (and really, only one of the two should be used).
        self.eq_data_attributes = [a for a in data_attributes if a.is_eq and not a.is_comparable]

        sort_arguments = {}
        for info in self.sortable_data_attributes:
            sort_arguments[info.name] = info
            for alias in info.aliases:
                sort_arguments[alias] = info

        self.sort_arguments = sort_arguments

    def get(self, arg: ParsedArguments, ctx, is_list: bool) -> FilterResult:
        start_index = 0
        display = None
        sort = None
        reverse_sort = arg.tag('reverse')
        if self.sortable_data_attributes:
            sort, sort_op = arg.single_op('sort', None,
                                          allowed_operators=['<', '>', '='],
                                          converter=self.sort_arguments)
            if sort:
                reverse_sort ^= (sort_op == '<') ^ sort.reverse_sort
            display = arg.single(['display', 'disp'], sort if sort and sort.formatter else None,
                                 converter={**self.sort_arguments, 'none': None})
        tag_arguments = {a: arg.tags(a.value_mapping.keys()) for a in self.tag_data_attributes}
        inverse_tag_arguments = {a: arg.tags('!' + t for t in a.value_mapping.keys()) for a in self.tag_data_attributes}
        keyword_arguments = {a: arg.words(a.value_mapping.keys()) for a in self.keyword_data_attributes}
        flag_arguments = {a: bool(arg.tags([a.name, *a.aliases])) for a in self.flag_data_attributes}
        inverse_flag_arguments = {a: bool(arg.tags('!' + t for t in [a.name, *a.aliases]))
                                  for a in self.flag_data_attributes if not a.flag_callback}
        comparable_arguments = {
            a: arg.repeatable_op([a.name] + a.aliases, is_list=True,
                                 allowed_operators=['=', '==', '!=', '>', '<', '>=', '<='],
                                 converter=self.master_filter.wrap_compare_converter(ctx, a.compare_converter) or (
                                     lambda s: float(s))) for a in
            self.comparable_data_attributes}
        eq_arguments = {
            a: arg.repeatable_op([a.name] + a.aliases, is_list=True,
                                 allowed_operators=['=', '==', '!='],
                                 converter=self.master_filter.wrap_compare_converter(ctx,
                                                                                     a.compare_converter) or a.value_mapping or (
                                               lambda s: float(s)))
            for a in self.eq_data_attributes}
        text = arg.text()

        arg.require_all_arguments_used()

        current = self.master_filter.get_current(ctx)
        is_relative_only = re.fullmatch(r'[+-]\d+', arg.original.strip()) and current
        if is_relative_only:
            text = ''
        elif re.fullmatch(r'~\d+', text.strip()):
            start_index = int(text.strip()[1:]) - 1
            text = ''

        start_tab = self.source.default_tab
        if not is_list:
            start_tab = self.source.default_tab
            if self.source.suffix_tab_aliases:
                words = text.split()
                if len(words) >= 1 and words[-1].lower() in self.source.suffix_tab_aliases:
                    start_tab = self.source.suffix_tab_aliases[words[-1].lower()]
                    text = ' '.join(words[:-1])

        values = self.master_filter.get_by_relevance(text, ctx)

        for attr, tags in tag_arguments.items():
            if tags:
                targets = {attr.value_mapping[t] for t in tags}
                if attr.is_plural:
                    values = [v for v in values if targets.issubset(attr.accessor(self.master_filter, ctx, v))]
                else:
                    values = [v for v in values if attr.accessor(self.master_filter, ctx, v) in targets]
        for attr, tags in inverse_tag_arguments.items():
            if tags:
                targets = {attr.value_mapping[t[1:]] for t in tags}
                if attr.is_plural:
                    values = [v for v in values if not targets.intersection(attr.accessor(self.master_filter, ctx, v))]
                else:
                    values = [v for v in values if attr.accessor(self.master_filter, ctx, v) not in targets]
        for attr, tags in keyword_arguments.items():
            if tags:
                targets = {attr.value_mapping[t] for t in tags}
                if attr.is_plural:
                    values = [v for v in values if targets.issubset(attr.accessor(self.master_filter, ctx, v))]
                else:
                    values = [v for v in values if attr.accessor(self.master_filter, ctx, v) in targets]
        for attr, flag_present in flag_arguments.items():
            if flag_present:
                if attr.flag_callback:
                    callback_value = attr.flag_callback(self.master_filter, ctx, values)
                    if callback_value is not None:
                        values = callback_value
                else:
                    values = [v for v in values if attr.accessor(self.master_filter, ctx, v)]
        for attr, flag_present in inverse_flag_arguments.items():
            if flag_present:
                # Flags with callbacks are excluded
                values = [v for v in values if not attr.accessor(self.master_filter, ctx, v)]
        for attr, arguments in {**comparable_arguments, **eq_arguments}.items():
            for argument in arguments:
                argument_value, operation = argument
                if attr.is_plural:
                    operator = list_to_list_operator_for(operation)
                else:
                    operator = list_operator_for(operation)
                values = [v for v in values if operator(attr.accessor(self.master_filter, ctx, v), argument_value)]

        if self.source.default_sort and not text:
            values = sorted(values, key=lambda v: self.source.default_sort.accessor(self.master_filter, ctx, v))
            if self.source.default_sort.reverse_sort ^ bool(sort and reverse_sort):
                values = values[::-1]
        if sort:
            values = sorted(values, key=lambda v: sort.accessor(self.master_filter, ctx, v))
        if reverse_sort:
            values = values[::-1]

        display = display or self.source.default_display

        if is_relative_only and current in values:
            start_index = values.index(current)
            start_index -= int(arg.original.strip())

        start_index = min(len(values) - 1, max(0, start_index))

        return FilterResult(values, start_index, start_tab, display)


class FilterResult(NamedTuple):
    values: List
    start_index: int
    start_tab: int
    display: Optional[DataAttributeInfo]


DataAttributeAccessor = Callable[[MasterFilter, PrefContext, Any], Any]
ContextlessDataAttributeAccessor = Callable[[MasterFilter, Any], Any]
AnyDataAccessor = Union[DataAttributeAccessor, ContextlessDataAttributeAccessor]


def _get_accessor(f: Union[AnyDataAccessor]) -> DataAttributeAccessor:
    if len(getfullargspec(f).args) == 2:
        def accessor(self, ctx, value):
            return f(self, value)

        return accessor
    else:
        return f


EmbedSourceCallable = Union[
    Callable[[MasterFilter, PrefContext, Any, Server], discord.Embed], Callable[
        [MasterFilter, PrefContext, Any, int, Server], discord.Embed]]
ListFormatterCallable = AnyDataAccessor
AnyEmoji = Union[int, str, discord.Emoji]

ESC = TypeVar('ESC', bound=EmbedSourceCallable)


class AnnotatedEmbedSourceCallable(Protocol[ESC]):
    list_formatter: Callable

    def __call__(self, *args, **kwargs):
        pass


@dataclass
class CommandSourceInfo:
    embed_source: Optional[EmbedSourceCallable] = None
    command_args: Optional[Dict[str, Any]] = None
    list_command_args: Optional[Dict[str, Any]] = None
    default_sort: Optional[DataAttributeInfo] = None
    default_display: Optional[DataAttributeInfo] = None
    tabs: Optional[Sequence[AnyEmoji]] = None
    default_tab: int = 0
    suffix_tab_aliases: Optional[Dict[str, int]] = None
    list_name: Optional[str] = None
    list_formatter: Optional[ListFormatterCallable] = None


def command_source(
        *,
        command_args: Optional[Dict[str, Any]] = None,
        list_command_args: Optional[Dict[str, Any]] = None,
        default_sort: Optional[Union[DataAttributeInfo, Callable]] = None,
        default_display: Optional[Union[DataAttributeInfo, Callable]] = None,
        tabs: Optional[Sequence[AnyEmoji]] = None,
        default_tab: int = 0,
        suffix_tab_aliases: Optional[Dict[str, int]] = None,
        list_name: Optional[str] = None,
) -> Callable[[EmbedSourceCallable], AnnotatedEmbedSourceCallable]:
    """A decorator that marks a function as an command source.

    The function should have, apart from the self parameter, either two more parameters
    if ``tabs`` is not specified, one for the context and one for the master asset,
    or three more with an additional parameter for the tab index.

    Parameters
    ----------
    command_args
        A dict containing the arguments to supply to the Command constructor for the detail command.
        If this is not supplied, no detail command will be created.
    list_command_args
        A dict containing the arguments to supply to the Command constructor for the list command.
        If this is not supplied, no list command will be created.
    default_sort
        The default ``data_attribute`` to sort by, which should be sortable.
        If not supplied, default order is preserved.
    default_display
        The default ``data_attribute`` to display in lists, if any, which should have a formatter.
        If not supplied, defaults to no display.
    tabs
        A list of emoji and emoji ids to use for tab buttons.
    default_tab
        The default tab index if ``tabs`` is specified. Defaults to 0.
    suffix_tab_aliases
        A dict mapping potential final search term words with tab indexes.
    list_name
        The name to use in the header of the list command.
    """

    def decorator(func: EmbedSourceCallable) -> AnnotatedEmbedSourceCallable:
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


def list_formatter(
        *,
        name: str,
        list_command_args: Optional[Dict[str, Any]],
        default_sort: Optional[Union[DataAttributeInfo, Callable]] = None,
        default_display: Optional[Union[DataAttributeInfo, Callable]] = None,
) -> Callable[[Callable], Callable]:
    def decorator(func):
        info = CommandSourceInfo(
            list_formatter=_get_accessor(func),
            list_command_args=list_command_args,
            default_sort=getattr(default_sort, '_data_attribute_info', default_sort),
            default_display=getattr(default_display, '_data_attribute_info', default_display),
            list_name=name,
        )
        func._command_source_info = info

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
    is_plural: bool = False
    is_sortable: bool = False
    reverse_sort: bool = False
    is_comparable: bool = False
    is_eq: bool = False
    compare_converter: Optional[Callable] = None
    init_function: Optional[Callable] = None
    help_sample_argument: Optional[str] = None

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
        is_plural: bool = False,
        is_sortable: bool = False,
        reverse_sort: bool = False,
        is_comparable: bool = False,
        is_eq: bool = False,
        help_sample_argument: Optional[str] = None,
):
    """Marks a function as a data attribute.

    The function should have, apart from the self parameter, either one more parameter
    for the master asset, or two more with one for the context and one for the master asset,
    respectively.

    Parameters
    ----------
    name
        The name of this attribute.
    aliases
        A list of aliases for the attribute.
    description
        A description of the attribute for use in help.
    value_mapping
        A dict mapping strings to potential return values.
        Used for keywords, tags, and as eq.
    is_flag
        Marks the attribute as a flag.
        If a flag_callback is declared, it is called instead of using default behavior.
        Otherwise, filters based on truthiness of the return value.
    is_tag
        Marks the attribute as a tag.
        Uses the ``value_mapping`` to get tag values.
        If plural, filters for values that include all tags.
        Otherwise, filters for values that match any of the given tags.
    is_keyword
        Marks the attribute as a keyword.
        Functions identically to ``is_tag``.
    is_plural
        Marks the attribute as returning a collection of values rather than a single value.
    is_sortable
        Marks the attribute as returning an ordered value. Allows it to be used a sort argument.
    reverse_sort
        Whether to reverse sort by default.
    is_comparable
        Marks the attribute as comparable, and allows use as a named argument
        with comparison and equality operators. Usually combined with ``is_sortable``.
    is_eq
        Marks the attribute as support equality, and allows use as a named argument
        with equality operators. Should not be used with ``is_comparable``.
    help_sample_argument
        An example argument value to use in command help.
    """

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
            is_plural=is_plural,
            is_sortable=is_sortable,
            reverse_sort=reverse_sort,
            is_comparable=is_comparable,
            is_eq=is_eq,
            help_sample_argument=help_sample_argument,
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
