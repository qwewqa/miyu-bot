import functools
import itertools
import re
from datetime import datetime
from typing import Sequence, List, Dict

import discord
from d4dj_utils.master.card_master import CardMaster
from d4dj_utils.master.gacha_draw_master import GachaDrawMaster
from d4dj_utils.master.gacha_master import GachaMaster
from d4dj_utils.master.gacha_table_master import GachaTableMaster
from d4dj_utils.master.gacha_table_rate_master import GachaTableRateMaster

from miyu_bot.bot.bot import PrefContext
from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.common.emoji import (
    unit_emoji_ids_by_unit_id,
    attribute_emoji_ids_by_attribute_id,
    grey_emoji_id,
)
from miyu_bot.commands.master_filter.master_filter import (
    MasterFilter,
    data_attribute,
    DataAttributeInfo,
    command_source,
    list_formatter,
)


class GachaFilter(MasterFilter[GachaMaster]):
    def get_name(self, value: GachaMaster) -> str:
        return f"{value.name} {value.id}"

    def get_select_name(self, value: GachaMaster):
        return value.name, value.category.name, None

    @data_attribute("name", aliases=["title"], is_sortable=True)
    def name(self, value: GachaMaster):
        return value.name

    @data_attribute(
        "date",
        aliases=["release", "recent"],
        is_default_sort=True,
        is_default_display=True,
        is_sortable=True,
        is_comparable=True,
        reverse_sort=True,
    )
    def date(self, ctx, value: GachaMaster):
        return ctx.convert_tz(value.start_datetime).date()

    @date.formatter
    def format_date(self, ctx, value: GachaMaster):
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

    @data_attribute(
        "character", aliases=["char", "chara"], is_tag=True, is_eq=True, is_plural=True
    )
    def character(self, value: GachaMaster):
        return {c.character_id for c in value.pick_up_cards}

    @character.init
    def init_character(self, info: DataAttributeInfo):
        info.value_mapping = {
            k: v.id for k, v in self.bot.aliases.characters_by_name.items()
        }

    @data_attribute("unit", is_sortable=True, is_tag=True, is_eq=True)
    def unit(self, value: GachaMaster):
        units = {c.character.unit_id for c in value.pick_up_cards}
        if len(units) == 1:
            return next(iter(units))
        else:
            return -1

    @unit.init
    def init_unit(self, info: DataAttributeInfo):
        info.value_mapping = {
            **{k: v.id for k, v in self.bot.aliases.units_by_name.items()},
            "mixed": -1,
        }

    @data_attribute("attribute", is_sortable=True, is_tag=True, is_eq=True)
    def attribute(self, value: GachaMaster):
        attributes = {c.attribute_id for c in value.pick_up_cards}
        if len(attributes) == 1:
            return next(iter(attributes))
        else:
            return -1

    @attribute.init
    def init_attribute(self, info: DataAttributeInfo):
        info.value_mapping = {
            k: v.id for k, v in self.bot.aliases.attributes_by_name.items()
        }

    @data_attribute("id", is_sortable=True, is_comparable=True)
    def id(self, value: GachaMaster):
        return value.id

    @id.formatter
    def format_id(self, value: GachaMaster):
        return str(value.id).zfill(5)

    @command_source(
        command_args=dict(
            name="banner",
            aliases=["gacha"],
            description="Displays gacha banner info.",
            help="!banner Shiny Smily Scratch",
        )
    )
    def get_gacha_embed(self, ctx, gacha: GachaMaster, server):
        l10n = self.l10n[ctx]

        embed = discord.Embed(title=f"[{server.name}] {gacha.name}")

        thumb_url = self.bot.asset_url + get_asset_filename(gacha.banner_path)

        embed.set_thumbnail(url=thumb_url)

        def get_card_list_text(cards):
            t = (
                "\n".join(self.format_card_name_with_emoji(card) for card in cards)
                or "None"
            )
            if len(t) > 1024:
                t = (
                    "\n".join(self.format_card_name_short(card) for card in cards)
                    or "None"
                )
            if len(t) > 1024:
                t = l10n.format_value("too-many-results")
            return t

        featured_text = get_card_list_text(gacha.pick_up_cards)
        selectable_text = get_card_list_text(gacha.select_bonus_cards)

        embed.add_field(
            name=l10n.format_value("info"),
            value=l10n.format_value(
                "info-desc",
                {
                    "start-date": discord.utils.format_dt(gacha.start_datetime),
                    "end-date": discord.utils.format_dt(gacha.end_datetime),
                    "event-name": gacha.event.name if gacha.event else "None",
                    "pity-requirement": (gacha.bonus and gacha.bonus.max_value)
                    or "None",
                    "sub-pity-requirement": (
                        gacha.sub_bonus and gacha.sub_bonus.max_value
                    )
                    or "None",
                    "select-requirement": gacha.select_bonus_max_value or "None",
                    "gacha-type": gacha.gacha_type.name,
                    "category": gacha.category.name,
                },
            ),
            inline=False,
        )
        embed.add_field(
            name=l10n.format_value("summary"), value=gacha.summary, inline=False
        )
        embed.add_field(
            name=l10n.format_value("featured"),
            value=l10n.format_value(
                "featured-text", {"featured-text": featured_text or "None"}
            ),
            inline=False,
        )
        embed.add_field(
            name=l10n.format_value("selectable"),
            value=l10n.format_value(
                "selectable-text", {"selectable-text": selectable_text or "None"}
            ),
            inline=False,
        )
        embed.add_field(
            name=l10n.format_value("costs"),
            value="\n".join(
                self.format_draw_data(draw, l10n) for draw in gacha.draw_data
            ),
        )

        embed.set_footer(
            text=l10n.format_value("gacha-id", {"gacha-id": f"{gacha.id:>05}"})
        )

        return embed

    @command_source(
        command_args=dict(
            name="rates",
            aliases=[
                "banner_rates",
                "bannerrates",
                "gacha_rates",
                "gacharates",
                "banner_tables",
                "bannertables",
                "gacha_tables",
                "gachatables",
                "banner_rate",
                "bannerrate",
                "gacha_rate",
                "gacharate",
                "banner_table",
                "bannertable",
                "gacha_table",
                "gachatable",
            ],
            description="Displays gacha banner rate info.",
            help="!banner_rates Shiny Smily Scratch",
        )
    )
    def get_gacha_table_embed(self, ctx, gacha: GachaMaster, server):
        l10n = self.l10n[ctx]

        embed = discord.Embed(title=f"[{server.name}] {gacha.name}")

        thumb_url = self.bot.asset_url + get_asset_filename(gacha.banner_path)

        embed.set_thumbnail(url=thumb_url)

        def add_table_field(
            table_rate: GachaTableRateMaster,
            tables: Sequence[Sequence[GachaTableMaster]],
        ):
            body = ""
            body_short = ""

            for table_normalized_rate, table in zip(
                table_rate.normalized_rates, tables
            ):
                if table_normalized_rate == 0:
                    continue
                if not table:  # Just in case it's not in data yet
                    return
                rates = [t.rate for t in table]
                total_rate = sum(rates)

                rate_up_card_entries = [t for t in table if t.card]

                for entry in rate_up_card_entries:
                    body += f"`{table_normalized_rate * entry.rate / total_rate * 100: >6.3f}% {self.format_card_name_for_list(entry.card)}`\n"
                    body_short += f"`{table_normalized_rate * entry.rate / total_rate * 100: >6.3f}% {self.format_card_name_short(entry.card)}`\n"

            if len(body) == 0:
                embed.add_field(
                    name=table_rate.tab_name,
                    value=f'`{l10n.format_value("none-or-too-many")}`',
                    inline=False,
                )
            elif len(body) <= 1000:
                embed.add_field(name=table_rate.tab_name, value=body, inline=False)
            elif len(body_short) <= 1000:
                embed.add_field(
                    name=table_rate.tab_name, value=body_short, inline=False
                )
            else:
                embed.add_field(
                    name=table_rate.tab_name,
                    value=f'`{l10n.format_value("too-many")}`',
                    inline=False,
                )

        for table_rate in gacha.table_rates:
            add_table_field(table_rate, gacha.tables)

        if gacha.bonus and gacha.bonus.tables:
            add_table_field(gacha.bonus.table_rate, gacha.bonus.tables)

        if gacha.sub_bonus and gacha.sub_bonus.tables:
            add_table_field(gacha.sub_bonus.table_rate, gacha.sub_bonus.tables)

        if not embed.fields:
            embed.description = l10n.format_value("none-or-too-many")

        return embed

    @list_formatter(
        name="gacha-search",
        command_args=dict(
            name="banners",
            aliases=["gachas"],
            description="Lists gacha banners.",
            help="!banners",
        ),
    )
    def format_gacha_name_for_list(self, ctx, gacha):
        pick_ups = gacha.pick_up_cards
        units = {card.character.unit.id for card in pick_ups}
        attributes = {card.attribute.id for card in pick_ups}
        if len(units) == 1:
            unit_emoji = unit_emoji_ids_by_unit_id[next(iter(units))]
        else:
            unit_emoji = grey_emoji_id
        if len(attributes) == 1:
            attribute_emoji = attribute_emoji_ids_by_attribute_id[
                next(iter(attributes))
            ]
        else:
            attribute_emoji = grey_emoji_id
        return f"`{unit_emoji}`+`{attribute_emoji}` {gacha.name}"

    stock_names = {
        1: "diamond",
        2: "paid-diamond",
        901: "single-ticket",
        902: "ten-pull-ticket",
        903: "four-star-ticket",
    }

    def format_draw_data(self, draw: GachaDrawMaster, l10n):
        name = self.stock_names.get(draw.stock_id, draw.stock.name)
        pull_count = sum(draw.draw_amounts)

        if pull_count < 10:
            pull_count_category = "few"
        else:
            pull_count_category = "many"

        if draw.draw_limit:
            return l10n.format_value(
                "limit-draw-cost-desc",
                {
                    "pull-count": pull_count,
                    "pull-count-category": pull_count_category,
                    "draw-cost": draw.stock_amount,
                    "draw-item-name": name,
                    "draw-limit": draw.draw_limit,
                    "refresh": draw.is_reset_limit_every_day,
                },
            )
        else:
            return l10n.format_value(
                "draw-cost-desc",
                {
                    "pull-count": pull_count,
                    "pull-count-category": pull_count_category,
                    "draw-cost": draw.stock_amount,
                    "draw-item-name": name,
                },
            )

    def format_card_name_for_list(self, card):
        if not card:
            return "Unknown"
        unit_emoji = unit_emoji_ids_by_unit_id[card.character.unit_id]
        attribute_emoji = attribute_emoji_ids_by_attribute_id[card.attribute_id]
        return f"`{unit_emoji}`+`{attribute_emoji}` {card.rarity_id}★ {card.name} {card.character.first_name_english}"

    def format_card_name_short(self, card):
        if not card:
            return "Unknown"
        return f"{card.rarity_id}★ {card.name} {card.character.first_name_english}"

    def format_card_name_with_emoji(self, card):
        if not card:
            return "Unknown"
        unit_emoji = unit_emoji_ids_by_unit_id[card.character.unit_id]
        attribute_emoji = attribute_emoji_ids_by_attribute_id[card.attribute_id]
        return f"{unit_emoji} {attribute_emoji} {card.rarity_id}★ {card.name} {card.character.first_name_english}"

    @functools.lru_cache(maxsize=None)
    def get_gacha_rateup_card_set(self, gacha: GachaMaster) -> Dict[CardMaster, None]:
        results = set()

        def add_table(
            table_rate: GachaTableRateMaster,
            tables: Sequence[Sequence[GachaTableMaster]],
        ):
            for table in itertools.chain(*tables):
                if table.card_id:
                    results.add(table.card)

        for table_rate in gacha.table_rates:
            add_table(table_rate, gacha.tables)

        if gacha.bonus:
            add_table(gacha.bonus.table_rate, gacha.bonus.tables)

        if gacha.sub_bonus:
            add_table(gacha.sub_bonus.table_rate, gacha.sub_bonus.tables)

        # Use dict as an ordered set
        return {
            v: None
            for v in sorted(
                [result for result in results if result],
                key=lambda c: (-c.rarity_id, c.id),
            )
        }

    def get_gacha_rateup_cards(self, gacha: GachaMaster) -> List[CardMaster]:
        return list(self.get_gacha_rateup_card_set(gacha))

    @get_gacha_embed.shortcut_button(name="Cards")
    @get_gacha_table_embed.shortcut_button(name="Cards")
    async def cards_shortcut(
        self, ctx, gacha: GachaMaster, server, interaction: discord.Interaction
    ):
        f = ctx.bot.master_filters.cards
        view, embed = f.get_simple_list_view(
            ctx, self.get_gacha_rateup_cards(gacha), server
        )
        await interaction.response.send_message(embed=embed, view=view)

    @cards_shortcut.check
    def check_gacha_shortcut(self, gacha: GachaMaster, _ctx):
        return bool(self.get_gacha_rateup_cards(gacha))

    @get_gacha_embed.shortcut_button(name="Event")
    @get_gacha_table_embed.shortcut_button(name="Event")
    async def event_shortcut(
        self, ctx, gacha: GachaMaster, server, interaction: discord.Interaction
    ):
        f = ctx.bot.master_filters.events
        view, embed = f.get_simple_detail_view(
            ctx, [gacha.event], server, f.get_event_embed
        )
        await interaction.response.send_message(embed=embed, view=view)

    @event_shortcut.check
    def check_event_shortcut(self, gacha: GachaMaster, _ctx):
        return bool(gacha.event)
