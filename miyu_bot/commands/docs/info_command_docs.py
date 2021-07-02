import random
from pathlib import Path
from typing import List, Dict

from fluent.runtime import FluentLocalization

from miyu_bot.bot.bot import D4DJBot
from miyu_bot.commands.docs.markdown import MarkdownDocument
from miyu_bot.commands.master_filter.locales import valid_locales
from miyu_bot.commands.master_filter.master_filter import MasterFilter, DataAttributeInfo


def generate_info_command_docs(bot: D4DJBot, docs_path: Path, filters: List[MasterFilter]):
    for master_filter in filters:
        generate_master_filter_docs(bot, docs_path, master_filter)


def generate_master_filter_docs(bot: D4DJBot, docs_path: Path, master_filter: MasterFilter):
    for locale in valid_locales:
        locale_filename = locale.replace('-', '_')  # needed by mkdocs static i18n plugin
        l10n = FluentLocalization([*{locale, 'en-US'}], [f'docs/{master_filter.name}.ftl', 'docs/common.ftl'],
                                  bot.fluent_loader)
        md = MarkdownDocument()
        md.text('<!-- Generated -->')
        md.heading(1, l10n.format_value('name'))
        md.text(l10n.format_value('description'))
        md.add_all(get_attribute_help_text(attr, l10n) for attr in master_filter.data_attributes)
        filename = master_filter.name.replace('_filter', '')
        (docs_path / f'{filename}.{locale_filename}.md').write_text(md.get(), encoding='utf-8')


def get_attribute_help_text(attr: DataAttributeInfo, l10n: FluentLocalization) -> MarkdownDocument:
    md = MarkdownDocument()
    md.heading(2, attr.name)
    if attr.aliases:
        md.admonition('abstract', 'Aliases', ', '.join(attr.aliases))
    md.admonition('info', 'Type', ', '.join(get_attribute_type_description(attr, l10n)))
    description_fluent_id = f'{attr.name}-desc'
    description = l10n.format_value(description_fluent_id)
    if description != description_fluent_id:
        md.admonition('question', 'Description', description)
    if attr.value_mapping:
        tag_groups = get_tag_groups(attr.value_mapping)
        tag_group_lines = [' - ' + ', '.join(g) for g in tag_groups.values()]
        md.admonition('note', 'Tags', md.escape_markdown('\n'.join(tag_group_lines)), collapsible=True)
    elif attr.is_flag:
        md.admonition('note', 'Tags', md.escape_markdown(', '.join([attr.name, *attr.aliases])))
    if usage_text := get_attribute_usage(attr, l10n):
        md.admonition('example', 'Examples', usage_text, collapsible=True)
    return md


def get_tag_groups(tags: dict) -> dict:
    groups = {value: [] for value in tags.values()}
    for k, v in tags.items():
        groups[v].append(k)
    return groups


def get_attribute_usage(attr: DataAttributeInfo, l10n: FluentLocalization) -> str:
    entries = []
    if attr.is_flag:
        entries.append(f'${attr.name}')
        if not attr.flag_callback:
            entries.append(f'$!{attr.name}')
    if attr.is_sortable:
        entries.append(f'sort={attr.name}')
        entries.append(f'sort<{attr.name}')
    if attr.formatter:
        entries.append(f'disp={attr.name}')
    if attr.value_mapping:
        values = [*get_dict_keys_without_repeated_values(attr.value_mapping)]
        if len(values) < 2:
            example_value1 = random.choice(values)
            example_value2 = example_value1
        else:
            example_value1, example_value2 = random.sample(values, 2)
        example_values = random.sample(values, min(3, len(values)))
        if attr.is_comparable or attr.is_eq:
            entries.append(f'{attr.name}={example_value1}')
            entries.append(f'{attr.name}={",".join(example_values)}')
            entries.append(f'{attr.name}!={",".join(example_values)}')
            if attr.is_plural:
                entries.append(f'{attr.name}=={",".join(example_values)}')
        if attr.is_comparable:
            entries.append(f'{attr.name}>{example_value2}')
        if attr.is_tag:
            entries.append(' '.join(f'${t}' for t in example_values))
            entries.append(f'$!{example_value1} $!{example_value2}')
        if attr.is_keyword:
            entries.append(' '.join(f'{t}' for t in example_values))
    else:
        example_value = attr.help_sample_argument or '[value]'
        if attr.is_comparable or attr.is_eq:
            entries.append(f'{attr.name}={example_value}')
            entries.append(f'{attr.name}!={example_value}')
        if attr.is_comparable:
            entries.append(f'{attr.name}>{example_value}')
    return '\n'.join(f'`{e}`' for e in entries)


def get_dict_keys_without_repeated_values(d: dict):
    seen = set()
    for k, v in d.items():
        if v in seen:
            continue
        seen.add(v)
        yield k


def get_attribute_type_description(attr: DataAttributeInfo, l10n: FluentLocalization):
    attr_types = []
    usage_page = '../general_usage/'
    if attr.is_flag:
        if attr.flag_callback:
            attr_types.append(f'[{l10n.format_value("attr-type-special-flag")}]({usage_page}#flag)')
        else:
            attr_types.append(f'[{l10n.format_value("attr-type-flag")}]({usage_page}#flag)')
    if attr.is_sortable:
        attr_types.append(f'[{l10n.format_value("attr-type-sortable")}]({usage_page}#sortable)')
    if attr.formatter:
        attr_types.append(f'[{l10n.format_value("attr-type-display")}]({usage_page}#display)')
    if attr.is_comparable:
        attr_types.append(f'[{l10n.format_value("attr-type-comparable")}]({usage_page}#comparable)')
    if attr.is_eq:
        attr_types.append(f'[{l10n.format_value("attr-type-equality")}]({usage_page}#equality)')
    if attr.is_tag:
        attr_types.append(f'[{l10n.format_value("attr-type-tag")}]({usage_page}#tag)')
    if attr.is_keyword:
        attr_types.append(f'[{l10n.format_value("attr-type-keyword")}]({usage_page}#keyword)')
    if attr.is_plural:
        attr_types.append(f'[{l10n.format_value("attr-type-plural")}]({usage_page}#plural)')
    return attr_types
