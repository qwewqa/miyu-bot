from pathlib import Path
from typing import List

from fluent.runtime import FluentLocalization

from miyu_bot.bot.bot import D4DJBot
from miyu_bot.commands.docs.markdown import MarkdownDocument
from miyu_bot.commands.master_filter.locales import valid_locales
from miyu_bot.commands.master_filter.master_filter import MasterFilter, DataAttributeInfo


def generate_info_command_docs(bot: D4DJBot, docs_path: Path, filters: List[MasterFilter]):
    for master_filter in filters:
        generate_master_filter_docs(bot, docs_path, master_filter)


def generate_master_filter_docs(bot: D4DJBot, docs_path: Path, filter: MasterFilter):
    for locale in valid_locales:
        locale_filename = locale.replace('-', '_')  # needed by mkdocs static i18n plugin
        l10n = FluentLocalization([*{locale, 'en-US'}], [f'docs/{filter.name}.ftl', 'docs/common.ftl'],
                                  bot.fluent_loader)
        md = MarkdownDocument()
        md.text('<!-- Generated -->')
        md.heading(1, l10n.format_value('name'))
        md.text(l10n.format_value('description'))
        md.add_all(get_attribute_help_text(attr, l10n) for attr in filter.data_attributes)
        (docs_path / f'{filter.name}.{locale_filename}.md').write_text(md.get(), encoding='utf-8')


def get_attribute_help_text(attr: DataAttributeInfo, l10n: FluentLocalization) -> MarkdownDocument:
    md = MarkdownDocument()
    md.heading(2, attr.name)
    md.admonition('abstract', 'Aliases', ', '.join(attr.aliases))
    md.admonition('info', 'Type', ', '.join(get_attribute_type_description(attr, l10n)))
    description_fluent_id = f'{attr.name}-desc'
    description = l10n.format_value(description_fluent_id)
    if description != description_fluent_id:
        md.admonition('question', 'Description', description)
    if attr.value_mapping:
        md.admonition('note', 'Tags', md.escape_markdown(', '.join(attr.value_mapping.keys())))
    return md


def get_attribute_type_description(attr: DataAttributeInfo, l10n: FluentLocalization):
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
    return attr_types
