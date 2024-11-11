from typing import Tuple

import discord
from d4dj_utils.master.stamp_master import StampMaster

from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.master_filter.master_filter import (
    MasterFilter,
    data_attribute,
    command_source,
    list_formatter,
)


class StampFilter(MasterFilter[StampMaster]):
    def get_name(self, value: StampMaster) -> str:
        if value.quote is not None and value.quote in value.name:
            return value.name
        else:
            return f'{value.name + " " + value.quote.replace("～", "ー") if value.quote else value.description}'
        
    def get_select_name(self, value: StampMaster) -> Tuple[str, str, None]:
        return f"{value.name}", f'{value.quote.replace("～", "ー") if value.quote else value.description}', None

    @data_attribute("id", is_sortable=True, is_comparable=True)
    def id(self, value: StampMaster):
        return value.id

    @id.formatter
    def format_id(self, value: StampMaster):
        return f"{value.id:>05}"
    
    @data_attribute("name", aliases=["title"], is_sortable=True)
    def name(self, value: StampMaster) -> str:
        return value.name

    @command_source()
    def get_stamp_embed(self, ctx, stamp: StampMaster, server):
        l10n = self.l10n[ctx]
        embed = discord.Embed(title=self.format_stamp_name(stamp))

        embed.set_image(url=self.bot.asset_url + get_asset_filename(stamp.stamp_path))

        embed.set_footer(text=l10n.format_value("stamp-id", {"stamp-id": f"{stamp.id:>05}"}))
        return embed

    @list_formatter(
        name="stamp-search",
        command_args=dict(
            name="stamps",
            aliases=["stickers"],
            description="Lists stamps.",
            help="!stamps",
        ),
    )
    def format_stamp_name(self, stamp: StampMaster):
        if stamp.quote is not None and stamp.quote in stamp.name:
            return stamp.name
        else:
            return f"{stamp.name}: {stamp.quote}"
