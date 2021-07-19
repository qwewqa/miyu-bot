import random
from pathlib import Path
from typing import List, Iterable

from miyu_bot.bot.bot import MiyuBot
from miyu_bot.commands.docs.documentation_fluent_localization import DocumentationFluentLocalization
from miyu_bot.commands.docs.markdown import MarkdownDocument
from miyu_bot.commands.master_filter.locales import valid_locales
from miyu_bot.commands.master_filter.master_filter import MasterFilter, DataAttributeInfo, CommandSourceInfo

USAGE_PAGE = '../general_usage/'


def generate_info_command_docs(bot: MiyuBot, docs_path: Path, filters: List[MasterFilter]):
    for master_filter in filters:
        generate_master_filter_docs(bot, docs_path, master_filter)


def generate_master_filter_docs(bot: MiyuBot, docs_path: Path, master_filter: MasterFilter):
    for locale in valid_locales:
        # needed by mkdocs static i18n plugin
        locale_filename = {
            'en-US': 'en',
            'zh-TW': 'zh_TW',
            'ja': 'ja',
        }[locale]
        l10n = DocumentationFluentLocalization([*{locale, 'en-US'}],
                                               [f'docs/{master_filter.name}.ftl', 'docs/common.ftl'],
                                               bot.fluent_loader)
        md = MarkdownDocument()
        md.text('<!-- Generated Document: Do not edit -->')
        md.heading(1, l10n.format_value('name', fallback=master_filter.name))
        md.text(l10n.format_value('description', fallback=''))
        md.heading(2, l10n.format_value('heading-commands'))
        md.add_all(get_command_source_help_texts(master_filter, l10n))
        md.heading(2, l10n.format_value('heading-attributes'))
        md.add_all(get_attribute_help_text(attr, l10n) for attr in master_filter.data_attributes)
        filename = master_filter.name.replace('_filter', '').replace('_', '-')
        (docs_path / f'{filename}.{locale_filename}.md').write_text(md.get(), encoding='utf-8')


def get_command_source_help_texts(master_filter: MasterFilter,
                                  l10n: DocumentationFluentLocalization,
                                  heading_level=3) -> Iterable[MarkdownDocument]:
    for command in master_filter.command_sources:
        if command.command_args:
            md = MarkdownDocument()
            name = command.command_args["name"]
            localized_name = l10n.format_value(f'command-{name}', fallback=name)
            md.heading(heading_level,
                       f'{name}' +
                       (f' ({localized_name})' if name != localized_name else ''))
            md.text(f'*[{l10n.format_value("command-type-detail")}]({USAGE_PAGE}#detail-commands)*')
            if command.suffix_tab_aliases:
                md.admonition('note', l10n.format_value('command-tab-names'), ', '.join(command.suffix_tab_aliases))
            if desc := l10n.format_value(f'command-{command.command_args["name"]}-description', fallback=''):
                md.admonition('question', 'Description', desc)
            yield md
    if master_filter.list_formatter:
        md = MarkdownDocument()
        name = master_filter.list_formatter.command_args["name"]
        localized_name = l10n.format_value(f'command-{name}', fallback=name)
        md.heading(heading_level,
                   f'{name}' +
                   (f' ({localized_name})' if name != localized_name else ''))
        md.text(f'*[{l10n.format_value("command-type-list")}]({USAGE_PAGE}#list-commands)*')
        if desc := l10n.format_value(f'command-{master_filter.list_formatter.command_args["name"]}-description', fallback=''):
            md.admonition('question', 'Description', desc)
        yield md


def get_attribute_help_text(attr: DataAttributeInfo,
                            l10n: DocumentationFluentLocalization,
                            heading_level=3) -> MarkdownDocument:
    md = MarkdownDocument()
    name = attr.name
    localized_name = l10n.format_value(f'attr-{name}', fallback=name)
    md.heading(heading_level, attr.name + (f' ({localized_name})' if name != localized_name else ''))
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


def get_attribute_usage(attr: DataAttributeInfo, l10n: DocumentationFluentLocalization) -> str:
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
        if attr.regex:
            entries.append(f'sort={example_value}')
            entries.append(f'sort<{example_value}')
            if attr.formatter:
                entries.append(f'disp={example_value}')
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


def get_attribute_type_description(attr: DataAttributeInfo, l10n: DocumentationFluentLocalization):
    attr_types = []
    if attr.is_flag:
        if attr.flag_callback:
            attr_types.append(f'[{l10n.format_value("attr-type-special-flag")}]({USAGE_PAGE}#flag)')
        else:
            attr_types.append(f'[{l10n.format_value("attr-type-flag")}]({USAGE_PAGE}#flag)')
    if attr.is_sortable:
        if attr.is_default_sort:
            attr_types.append(f'[{l10n.format_value("attr-type-sortable-default")}]({USAGE_PAGE}#sortable)')
        else:
            attr_types.append(f'[{l10n.format_value("attr-type-sortable")}]({USAGE_PAGE}#sortable)')
    if attr.formatter:
        if attr.is_default_display:
            attr_types.append(f'[{l10n.format_value("attr-type-display-default")}]({USAGE_PAGE}#display)')
        else:
            attr_types.append(f'[{l10n.format_value("attr-type-display")}]({USAGE_PAGE}#display)')
    if attr.is_comparable:
        attr_types.append(f'[{l10n.format_value("attr-type-comparable")}]({USAGE_PAGE}#comparable)')
    if attr.is_eq:
        attr_types.append(f'[{l10n.format_value("attr-type-equality")}]({USAGE_PAGE}#equality)')
    if attr.is_tag:
        attr_types.append(f'[{l10n.format_value("attr-type-tag")}]({USAGE_PAGE}#tag)')
    if attr.is_keyword:
        attr_types.append(f'[{l10n.format_value("attr-type-keyword")}]({USAGE_PAGE}#keyword)')
    if attr.is_plural:
        attr_types.append(f'[{l10n.format_value("attr-type-plural")}]({USAGE_PAGE}#plural)')
    return attr_types
