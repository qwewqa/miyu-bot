import re
from datetime import datetime
from typing import Tuple

import discord
from d4dj_utils.master.comic_master import ComicMaster

from miyu_bot.bot.bot import PrefContext
from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.master_filter.master_filter import (
    MasterFilter,
    data_attribute,
    command_source,
    list_formatter,
)


class ComicFilter(MasterFilter[ComicMaster]):
    def get_name(self, value: ComicMaster) -> str:
        return value.title

    def get_select_name(self, value: ComicMaster) -> Tuple[str, str, None]:
        return value.title, value.episode_number, None

    def is_released(self, value: ComicMaster) -> bool:
        return value.is_released

    @data_attribute("name", aliases=["title"], is_sortable=True)
    def name(self, value: ComicMaster) -> str:
        return value.title

    @data_attribute(
        "date",
        aliases=["release", "recent"],
        is_sortable=True,
        is_default_sort=True,
        is_comparable=True,
        reverse_sort=True,
    )
    def date(self, ctx, value: ComicMaster):
        return ctx.convert_tz(value.start_datetime).date()

    @date.formatter
    def format_date(self, ctx, value: ComicMaster):
        dt = ctx.convert_tz(value.start_datetime)
        return f"{dt.year % 100:02}/{dt.month:02}/{dt.day:02}"

    @date.compare_converter
    def date_compare_converter(self, ctx: PrefContext, s):
        match = re.fullmatch(r"(\d+)/(\d+)/(\d+)", s)
        if not match:
            raise
        y, m, d = (int(n) for n in match.groups())
        if y < 100:
            y += ctx.localize(datetime.now()).year // 100 * 100
        return ctx.localize(datetime(year=y, month=m, day=d)).date()

    @data_attribute("id", is_sortable=True, is_comparable=True)
    def id(self, value: ComicMaster):
        return value.id

    @id.formatter
    def format_id(self, value: ComicMaster):
        return f"{value.id:>08}"

    @command_source(
        command_args=dict(
            name="comic",
            description="Displays comics.",
        )
    )
    def get_comic_embed(self, ctx, comic: ComicMaster, server):
        l10n = self.l10n[ctx]

        embed = discord.Embed(
            title=comic.title,
            description=l10n.format_value(
                "comic-desc",
                {
                    "episode-number": comic.episode_number,
                    "start-date": discord.utils.format_dt(comic.start_datetime),
                },
            ),
        )

        embed.set_image(url=self.bot.asset_url + get_asset_filename(comic.comic_path))

        embed.set_footer(text=l10n.format_value("comic-id", {"comic-id": f"{comic.id:>07}"}))

        return embed

    @list_formatter(
        name="comic-search",
        command_args=dict(
            name="comics",
            description="Lists comics.",
        ),
    )
    def format_comic_name(self, comic: ComicMaster):
        return comic.title
