import dataclasses
import functools
import re
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING, Callable

from miyu_bot.bot.servers import Server
from miyu_bot.commands.common.argument_parsing import (
    list_to_list_operator_for,
    list_operator_for,
    ParsedArguments,
    ArgumentError,
)

if TYPE_CHECKING:
    from miyu_bot.commands.master_filter.master_filter import (
        DataAttributeInfo,
        MasterFilter,
        CommandSourceInfo,
    )


@dataclass
class FilterResults:
    master_filter: "MasterFilter"
    command_source_info: Optional["CommandSourceInfo"]
    values: List
    server: Server
    start_index: int = 0
    start_tab_name: Optional[str] = None
    display_formatter: Optional["Callable"] = None


class FilterProcessor:
    def __init__(
        self,
        master_filter: "MasterFilter",
        source: Optional["CommandSourceInfo"] = None,
    ):
        # source is None for the list command
        self.master_filter = master_filter
        self.source = source
        data_attributes = master_filter.data_attributes
        self.flag_data_attributes = [a for a in data_attributes if a.is_flag]
        self.tag_data_attributes = [a for a in data_attributes if a.is_tag]
        self.keyword_data_attributes = [a for a in data_attributes if a.is_keyword]
        self.sortable_data_attributes = [a for a in data_attributes if a.is_sortable]
        self.comparable_data_attributes = [
            a for a in data_attributes if a.is_comparable
        ]

        # is_comparable already includes eq behavior (and really, only one of the two should be used).
        self.eq_data_attributes = [
            a for a in data_attributes if a.is_eq and not a.is_comparable
        ]

        normal_sort_arguments = {}
        regex_sort_arguments = {}
        for info in self.sortable_data_attributes:
            if info.regex:
                regex_sort_arguments[info.regex] = info
            else:
                normal_sort_arguments[info.name] = info
                for alias in info.aliases:
                    normal_sort_arguments[alias] = info

        self.normal_sort_arguments = normal_sort_arguments
        self.regex_sort_arguments = regex_sort_arguments

    def convert_sort_argument(self, arg: str):
        if arg is None or arg.lower() == "none":
            return None
        if arg in self.normal_sort_arguments:
            return self.normal_sort_arguments[arg]
        for pattern, attr in self.regex_sort_arguments.items():
            if match := re.fullmatch(pattern, arg):
                attr = dataclasses.replace(
                    attr,
                    accessor=functools.partial(attr.accessor, match=match),
                    formatter=functools.partial(attr.formatter, match=match),
                )
                return attr
        raise ArgumentError(f"Invalid sort or display argument: {arg}.")

    def get(self, arg: ParsedArguments, ctx) -> FilterResults:
        start_index = 0
        display = None
        sort = None
        reverse_sort = arg.tag("reverse")
        if self.sortable_data_attributes:
            sort, sort_op = arg.single_op(
                "sort", None, allowed_operators=["<", ">", "="]
            )
            sort = self.convert_sort_argument(sort)
            if sort:
                reverse_sort ^= (sort_op == "<") ^ sort.reverse_sort
            display = arg.single(["display", "disp"], None)
            display = self.convert_sort_argument(display)
            if display is None:
                display = sort
        tag_arguments = {
            a: arg.tags(a.value_mapping.keys()) for a in self.tag_data_attributes
        }
        inverse_tag_arguments = {
            a: arg.tags("!" + t for t in a.value_mapping.keys())
            for a in self.tag_data_attributes
        }
        keyword_arguments = {
            a: arg.words(a.value_mapping.keys()) for a in self.keyword_data_attributes
        }
        flag_arguments = {
            a: bool(arg.tags([a.name, *a.aliases])) for a in self.flag_data_attributes
        }
        inverse_flag_arguments = {
            a: bool(arg.tags("!" + t for t in [a.name, *a.aliases]))
            for a in self.flag_data_attributes
            if not a.flag_callback
        }
        comparable_arguments = {
            a: arg.repeatable_op(
                [a.name] + a.aliases,
                is_list=True,
                allowed_operators=["=", "==", "!=", ">", "<", ">=", "<="],
                converter=self.master_filter.wrap_compare_converter(
                    ctx, a.compare_converter
                )
                or (lambda s: float(s)),
            )
            for a in self.comparable_data_attributes
        }
        eq_arguments = {
            a: arg.repeatable_op(
                [a.name] + a.aliases,
                is_list=True,
                allowed_operators=["=", "==", "!="],
                converter=self.master_filter.wrap_compare_converter(
                    ctx, a.compare_converter
                )
                or a.value_mapping
                or (lambda s: float(s)),
            )
            for a in self.eq_data_attributes
        }

        start = arg.single(["start"], None)

        text = arg.text()

        arg.require_all_arguments_used()

        current = self.master_filter.get_current(ctx)
        is_relative_only = re.fullmatch(r"[+-]\d+", arg.original.strip()) and current
        if is_relative_only:
            text = ""
        elif re.fullmatch(r"~\d+", text.strip()):
            start_index = int(text.strip()[1:]) - 1
            text = ""

        start_tab = None
        if self.source:
            start_tab = self.source.default_tab
            if self.source.suffix_tab_aliases:
                words = text.split()
                if (
                    len(words) >= 1
                    and words[-1].lower() in self.source.suffix_tab_aliases
                ):
                    start_tab = words[-1].lower()
                    text = " ".join(words[:-1])

        values = self.master_filter.get_by_relevance(text, ctx)

        for attr, tags in tag_arguments.items():
            if tags:
                targets = {attr.value_mapping[t] for t in tags}
                if attr.is_plural:
                    values = [
                        v
                        for v in values
                        if targets.issubset(attr.accessor(self.master_filter, ctx, v))
                    ]
                else:
                    values = [
                        v
                        for v in values
                        if attr.accessor(self.master_filter, ctx, v) in targets
                    ]
        for attr, tags in inverse_tag_arguments.items():
            if tags:
                targets = {attr.value_mapping[t[1:]] for t in tags}
                if attr.is_plural:
                    values = [
                        v
                        for v in values
                        if not targets.intersection(
                            attr.accessor(self.master_filter, ctx, v)
                        )
                    ]
                else:
                    values = [
                        v
                        for v in values
                        if attr.accessor(self.master_filter, ctx, v) not in targets
                    ]
        for attr, tags in keyword_arguments.items():
            if tags:
                targets = {attr.value_mapping[t] for t in tags}
                if attr.is_plural:
                    values = [
                        v
                        for v in values
                        if targets.issubset(attr.accessor(self.master_filter, ctx, v))
                    ]
                else:
                    values = [
                        v
                        for v in values
                        if attr.accessor(self.master_filter, ctx, v) in targets
                    ]
        for attr, flag_present in flag_arguments.items():
            if flag_present:
                if attr.flag_callback:
                    callback_value = attr.flag_callback(self.master_filter, ctx, values)
                    if callback_value is not None:
                        values = callback_value
                else:
                    values = [
                        v for v in values if attr.accessor(self.master_filter, ctx, v)
                    ]
        for attr, flag_present in inverse_flag_arguments.items():
            if flag_present:
                # Flags with callbacks are excluded
                values = [
                    v for v in values if not attr.accessor(self.master_filter, ctx, v)
                ]
        for attr, arguments in {**comparable_arguments, **eq_arguments}.items():
            for argument in arguments:
                argument_value, operation = argument
                if attr.is_plural:
                    operator = list_to_list_operator_for(operation)
                else:
                    operator = list_operator_for(operation)
                values = [
                    v
                    for v in values
                    if operator(
                        attr.accessor(self.master_filter, ctx, v), argument_value
                    )
                ]

        if self.master_filter.default_sort and not text:
            values = sorted(
                values,
                key=lambda v: self.master_filter.default_sort.accessor(
                    self.master_filter, ctx, v
                ),
            )
            if self.master_filter.default_sort.reverse_sort ^ bool(
                sort and reverse_sort
            ):
                values = values[::-1]
        if sort:
            values = sorted(
                values, key=lambda v: sort.accessor(self.master_filter, ctx, v)
            )
        if reverse_sort:
            values = values[::-1]

        display = display or self.master_filter.default_display
        if display:
            display = display.formatter

        if is_relative_only and current in values:
            start_index = values.index(current)
            start_index -= int(arg.original.strip())

        if start is not None:
            if text:
                raise ArgumentError(
                    "The start argument cannot be combined with a non-keyword text argument."
                )
            start_values = self.master_filter.get_by_relevance(start, ctx)
            if not start_values:
                raise ArgumentError("Starting value not found.")
            new_start_index = None
            for start_value in start_values[:5]:  # Limit to trying first 5 results
                try:
                    new_start_index = values.index(start_value)
                    break
                except ValueError:
                    continue
            if new_start_index is None:
                raise ArgumentError("Starting value not found in results.")
            else:
                start_index = new_start_index

        start_index = min(len(values) - 1, max(0, start_index))

        return FilterResults(
            master_filter=self.master_filter,
            command_source_info=self.source,
            values=values,
            server=ctx.preferences.server,
            start_index=start_index,
            start_tab_name=start_tab,
            display_formatter=display,
        )
