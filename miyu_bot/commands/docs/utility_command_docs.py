from pathlib import Path

import discord.ext.commands

from miyu_bot.bot.bot import MiyuBot
from miyu_bot.commands.docs.documentation_fluent_localization import DocumentationFluentLocalization
from miyu_bot.commands.docs.markdown import MarkdownDocument
from miyu_bot.commands.master_filter.locales import valid_locales


def generate_utility_command_docs(bot: MiyuBot, docs_path: Path):
    for name, cog in bot.cogs.items():
        if name != 'Info':
            generate_cog_docs(bot, docs_path, name, cog)


def generate_cog_docs(bot: MiyuBot, docs_path: Path, name: str, cog: discord.ext.commands.Cog):
    for locale in valid_locales:
        # needed by mkdocs static i18n plugin
        locale_filename = {
            'en-US': 'en',
            'zh-TW': 'zh_TW',
            'ja': 'ja',
        }[locale]
        l10n = DocumentationFluentLocalization([*{locale, 'en-US'}],
                                               [f'docs/{name.lower()}.ftl', 'docs/common.ftl'],
                                               bot.fluent_loader)
        md = MarkdownDocument()
        md.text('<!-- Generated Document: Do not edit -->')
        md.heading(1, l10n.format_value('name', fallback=name))
        md.text(l10n.format_value('description', fallback=''))
        command: discord.ext.commands.Command
        for command in cog.get_commands():
            md.add(get_command_docs(l10n, command))
        filename = name.lower()
        (docs_path / f'{filename}.{locale_filename}.md').write_text(md.get(), encoding='utf-8')


def get_command_docs(l10n: DocumentationFluentLocalization,
                     command: discord.ext.commands.Command,
                     heading_level=2) -> MarkdownDocument:
    if isinstance(command, discord.ext.commands.Group):
        return get_group_docs(l10n, command, heading_level=heading_level)
    md = MarkdownDocument()
    if command.hidden:
        return md
    md.heading(heading_level, command.qualified_name)
    if command.aliases:
        md.admonition('abstract', 'Aliases', ', '.join(command.aliases))
    return md


def get_group_docs(l10n: DocumentationFluentLocalization,
                   group: discord.ext.commands.Group,
                   heading_level=2) -> MarkdownDocument:
    md = MarkdownDocument()
    md.heading(heading_level, group.qualified_name)
    for command in group.commands:
        md.add(get_command_docs(l10n, command, heading_level=heading_level + 1))
    return md
