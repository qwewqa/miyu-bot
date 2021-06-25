import re
import textwrap
from pathlib import Path
from typing import List

from fluent.runtime import FluentLocalization

from miyu_bot.bot.bot import D4DJBot
from miyu_bot.commands.master_filter.locales import valid_locales
from miyu_bot.commands.master_filter.master_filter import MasterFilter, DataAttributeInfo


def generate_info_command_docs(bot: D4DJBot, docs_path: Path, filters: List[MasterFilter]):
    for master_filter in filters:
        generate_master_filter_docs(bot, docs_path, master_filter)


def generate_master_filter_docs(bot: D4DJBot, docs_path: Path, filter: MasterFilter):
    for locale in valid_locales:
        locale_filename = locale.replace('-', '_')  # needed by mkdocs static i18n plugin
        l10n = FluentLocalization([*{locale, 'en-US'}], [f'docs/{filter.name}.ftl', 'docs/common.ftl'], bot.fluent_loader)
        head = l10n.format_value(filter.name)
        if head == filter.name:
            head = ''
        body = '\n'.join(get_attribute_help_text(attr, l10n) for attr in filter.data_attributes)
        (docs_path / f'{filter.name}.{locale_filename}.md').write_text(f'<!-- Generated File -->\n'
                                                                       f'{head}\n{body}', encoding='utf-8')


def get_attribute_help_text(attr: DataAttributeInfo, l10n: FluentLocalization):
    text = f'## {attr.name}\n'
    if attr.aliases:
        text += f'!!! abstract "Aliases"\n    {", ".join(attr.aliases)}\n'
    attr_types = []
    if attr.is_flag:
        attr_types.append('Flag')
    if attr.is_sortable:
        attr_types.append('Sortable')
    if attr.formatter:
        attr_types.append('Display')
    if attr.is_comparable:
        attr_types.append('Comparable')
    if attr.is_eq:
        attr_types.append('Filterable')
    if attr.is_tag:
        attr_types.append('Tag')
    if attr.is_keyword:
        attr_types.append('Keyword')
    if attr.is_plural:
        attr_types.append('Plural')
    text += f'!!! info "Type"\n    {", ".join(attr_types)}\n'
    description_fluent_id = f'{attr.name}-desc'
    description = l10n.format_value(description_fluent_id)
    if description != description_fluent_id:
        text += f'!!! question "Description"\n{textwrap.indent(description, prefix="    ")}\n'
    if attr.value_mapping:
        text += '!!! note "Tags"\n'
        text += '    ' + escape_markdown(', '.join(attr.value_mapping.keys())) + '\n'
    if attr.is_comparable or attr.is_eq:
        text += '!!! example "Usage"\n'
        if attr.is_comparable:
            text += f'    {attr.name} (=, ==, !=, >, <, >=, <=) {attr.help_sample_argument or "[value]"}'
        if attr.is_eq:
            text += f'    {attr.name} (=, ==, !=) {attr.help_sample_argument or "[value]"}'
        text += '\n'
    return text.strip()


def escape_markdown(s):
    return re.sub(r'([|\\*])', r'\\\1', s)
