"""
Master filter class and related functions.
"""

from __future__ import annotations

import dataclasses
import functools
import typing
from abc import abstractmethod, ABCMeta
from collections import defaultdict
from dataclasses import dataclass
from inspect import getfullargspec
from typing import Any, Optional, Union, Callable, List, Sequence, Protocol, Tuple, Awaitable
from typing import TypeVar, Generic, Dict

import discord
from d4dj_utils.master.master_asset import MasterAsset
from discord.ext import commands

import miyu_bot.bot.bot
from miyu_bot.bot.bot import MiyuBot, PrefContext
from miyu_bot.bot.servers import Server
from miyu_bot.commands.common.argument_parsing import ParsedArguments
from miyu_bot.commands.common.fuzzy_matching import FuzzyFilteredMap
from miyu_bot.commands.master_filter.filter_detail_view import FilterDetailView
from miyu_bot.commands.master_filter.filter_list_view import FilterListView
from miyu_bot.commands.master_filter.filter_result import FilterProcessor, FilterResults
from miyu_bot.commands.master_filter.localization_manager import LocalizationManager


class MasterFilterMeta(ABCMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        # Doesn't support subclassing
        if bases == (typing.Generic,):
            # Skip for base class
            return super().__new__(mcs, name, bases, namespace, **kwargs)
        command_sources = []
        data_attributes = []
        list_formatters = []
        for k, v in namespace.items():
            if data_info := getattr(v, '_data_attribute_info', False):
                data_attributes.append(data_info)
            if command_info := getattr(v, '_command_source_info', False):
                command_sources.append(command_info)
            if command_info := getattr(v, '_list_formatter_info', False):
                list_formatters.append(command_info)
        namespace['_data_attributes'] = data_attributes
        if not command_sources:
            raise ValueError('No command sources found.')
        namespace['_command_sources'] = command_sources
        if len(list_formatters) > 1:
            raise ValueError('Multiple list formatters found.')
        if not list_formatters:
            raise ValueError('No list formatter found.')
        namespace['_list_formatter'] = list_formatters[0]
        return super().__new__(mcs, name, bases, namespace, **kwargs)


TData = TypeVar('TData', bound=MasterAsset)


class MasterFilter(Generic[TData], metaclass=MasterFilterMeta):
    # Note: only works for masters that have an id field

    _command_sources: List[CommandSourceInfo]
    command_sources: List[CommandSourceInfo]
    _data_attributes: List[DataAttributeInfo]
    data_attributes: List[DataAttributeInfo]
    _list_formatter: ListFormatterInfo
    list_formatter: ListFormatterInfo
    default_sort: Optional[DataAttributeInfo]
    default_display: Optional[DataAttributeInfo]
    l10n: LocalizationManager

    def __init__(self, bot: MiyuBot, master_name: str, name: str):
        self.name = name
        self.bot = bot
        self.master_name = master_name
        self.default_filter = defaultdict(lambda: FuzzyFilteredMap(self.is_released))
        self.unrestricted_filter = defaultdict(lambda: FuzzyFilteredMap())
        self.command_sources = [dataclasses.replace(c) for c in self._command_sources]
        self.data_attributes = [dataclasses.replace(c) for c in self._data_attributes]
        self.list_formatter = dataclasses.replace(self._list_formatter)
        self.default_sort = next((da for da in self.data_attributes if da.is_default_sort), None)
        self.default_display = next((da for da in self.data_attributes if da.is_default_display), None)
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
            if args := cs.command_args:
                if include_self_parameter:
                    yield commands.command(**{**args,
                                              'description': args.get('description',
                                                                      'No Description')})(
                        wrap(self.get_detail_command_function(cs)))
                else:
                    yield commands.command(**{**args,
                                              'description': args.get('description',
                                                                      'No Description')})(
                        self.get_detail_command_function(cs))
        if self.list_formatter:
            cs = self.list_formatter
            if args := cs.command_args:
                if include_self_parameter:
                    yield commands.command(**{**args,
                                              'description': args.get('description',
                                                                      'No Description')})(
                        wrap(self.get_list_command_function()))
                else:

                    yield commands.command(**{**args,
                                              'description': args.get('description',
                                                                      'No Description')})(
                        wrap(self.get_list_command_function()))

    def get_detail_command_function(self, source):
        if hasattr(source, '_list_formatter_info'):
            source = source._list_formatter_info

        filter_processor = FilterProcessor(self, source)

        async def command(ctx, *, arg: Optional[ParsedArguments]):
            arg = arg or await ParsedArguments.convert(ctx, '')
            results = filter_processor.get(arg, ctx)
            view = FilterDetailView(self, ctx, results)
            await ctx.send(embed=view.active_embed, view=view)

        return command

    def get_simple_detail_view(self, ctx, values, server, source) -> Tuple[discord.ui.View, discord.Embed]:
        if hasattr(source, '_command_source_info'):
            source = source._command_source_info
        results = FilterResults(master_filter=self,
                                command_source_info=source,
                                values=values)
        view = FilterDetailView(self, ctx, results)
        view.target_server = server
        return view, view.active_embed

    def get_list_command_function(self):
        filter_processor = FilterProcessor(self)

        async def command(ctx, *, arg: Optional[ParsedArguments]):
            arg = arg or await ParsedArguments.convert(ctx, '')
            results = filter_processor.get(arg, ctx)
            view = FilterListView(self, ctx, results)
            await ctx.send(embed=view.active_embed, view=view)

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
ShortcutButtonCallable = Callable[[MasterFilter, PrefContext, Any, Server, discord.Interaction], Awaitable]
ListFormatterCallable = AnyDataAccessor
AnyEmoji = Union[int, str, discord.Emoji]

ESC = TypeVar('ESC', bound=EmbedSourceCallable)


class AnnotatedEmbedSourceCallable(Protocol[ESC]):
    shortcut_button: Callable

    def __call__(self, *args, **kwargs):
        pass


@dataclass
class ShortcutButtonInfo:
    function: ShortcutButtonCallable
    emoji: Optional[Union[str, discord.Emoji]] = None
    name: Optional[str] = None
    check: Callable[[MasterFilter, Any], bool] = lambda self, value: True


@dataclass
class CommandSourceInfo:
    embed_source: Optional[EmbedSourceCallable] = None
    command_args: Optional[Dict[str, Any]] = None
    tabs: Optional[Sequence[AnyEmoji]] = None
    default_tab: int = 0
    suffix_tab_aliases: Optional[Dict[str, int]] = None
    shortcut_buttons: List[ShortcutButtonInfo] = dataclasses.field(default_factory=lambda: [])

    def __call__(self, *args, **kwargs):
        return self.embed_source(*args, **kwargs)


@dataclass
class ListFormatterInfo:
    formatter: Optional[ListFormatterCallable]
    name: Optional[str] = None
    command_args: Optional[Dict[str, Any]] = None

    def __call__(self, *args, **kwargs):
        return self.formatter(*args, **kwargs)


def command_source(
        *,
        command_args: Optional[Dict[str, Any]] = None,
        tabs: Optional[Sequence[AnyEmoji]] = None,
        default_tab: int = 0,
        suffix_tab_aliases: Optional[Dict[str, int]] = None,
) -> Callable[[EmbedSourceCallable], AnnotatedEmbedSourceCallable]:
    """A decorator that marks a function as an command source.

    The function should have, apart from the self parameter, either two more parameters
    if ``tabs`` is not specified, one for the context and one for the master asset,
    or three more with an additional parameter for the tab index.
    """

    def decorator(func: EmbedSourceCallable) -> AnnotatedEmbedSourceCallable:
        info = CommandSourceInfo(
            command_args=command_args,
            embed_source=func,
            tabs=tabs,
            default_tab=default_tab,
            suffix_tab_aliases=suffix_tab_aliases,
        )
        func._command_source_info = info

        def shortcut_button(*, name: Optional[str] = None, emoji: Optional[Union[str, discord.Emoji]] = None):
            def decorator(func: ShortcutButtonCallable):
                shortcut_info = ShortcutButtonInfo(function=func, emoji=emoji, name=name)
                info.shortcut_buttons.append(shortcut_info)

                def check(f):
                    shortcut_info.check = f
                    return f

                func.check = check

                return func

            return decorator

        func.shortcut_button = shortcut_button

        return func

    return decorator


def list_formatter(
        *,
        name: str,
        command_args: Optional[Dict[str, Any]],
) -> Callable[[Callable], Callable]:
    def decorator(func):
        info = ListFormatterInfo(
            formatter=_get_accessor(func),
            name=name,
            command_args=command_args,
        )
        func._list_formatter_info = info

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
    is_default_sort: bool = False
    is_default_display: bool = False
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
        is_default_sort: bool = False,
        is_default_display: bool = False,
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
    is_default_sort
        Whether this attribute is the default for sort order.
        Should only be true for one or no attribute.
    is_default_display
        Whether this attribute is the default for list display.
        Should only be true for one or no attribute.
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
            is_default_sort=is_default_sort,
            is_default_display=is_default_display,
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
