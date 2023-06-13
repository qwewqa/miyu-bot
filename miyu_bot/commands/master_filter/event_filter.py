import datetime as dt
import functools
import re
from typing import Optional, Union

import discord
from d4dj_utils.master.common_enums import EventType
from d4dj_utils.master.event_master import EventMaster, EventState
from d4dj_utils.master.parameter_bonus_master import ParameterBonusMaster

from miyu_bot.bot.bot import PrefContext
from miyu_bot.bot.servers import Server
from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.common.emoji import (
    unit_emoji_ids_by_unit_id,
    attribute_emoji_ids_by_attribute_id,
    grey_emoji_id,
    event_point_emoji_id,
    parameter_bonus_emoji_ids_by_parameter_id,
)
from miyu_bot.commands.master_filter.master_filter import (
    MasterFilter,
    data_attribute,
    command_source,
    DataAttributeInfo,
    list_formatter,
)


class EventFilter(MasterFilter[EventMaster]):
    def get_name(self, value: EventMaster) -> str:
        return value.name

    def get_select_name(self, value: EventMaster):
        return value.name, value.event_type.name, None

    def is_released(self, value: EventMaster) -> bool:
        return value.start_datetime < dt.datetime.now(dt.timezone.utc) + dt.timedelta(
            hours=1
        )

    def get_current(
        self, ctx: Union[PrefContext, Server, None]
    ) -> Optional[EventMaster]:
        """Returns the oldest event that has not ended or the newest event otherwise."""
        try:
            # NY event overlapped with previous event
            return min(
                (v for v in self.values(ctx) if v.state() == EventState.Open),
                key=lambda e: e.start_datetime,
            )
        except ValueError:
            try:
                return min(
                    (v for v in self.values(ctx) if v.state() < EventState.Ended),
                    key=lambda e: e.start_datetime,
                )
            except ValueError:
                return max(self.values(ctx), key=lambda v: v.start_datetime)

    get_latest_event = get_current

    @data_attribute(
        "date",
        aliases=["release", "recent"],
        is_default_sort=True,
        is_default_display=True,
        is_sortable=True,
        is_comparable=True,
        reverse_sort=True,
    )
    def date(self, ctx, value: EventMaster):
        return ctx.convert_tz(value.start_datetime).date()

    @date.formatter
    def format_date(self, ctx, value: EventMaster):
        dt = ctx.convert_tz(value.start_datetime)
        return f"{dt.year % 100:02}/{dt.month:02}/{dt.day:02}"

    @date.compare_converter
    def date_compare_converter(self, ctx: PrefContext, s):
        match = re.fullmatch(r"(\d+)/(\d+)/(\d+)", s)
        if not match:
            raise
        y, m, d = (int(n) for n in match.groups())
        if y < 100:
            y += ctx.localize(dt.datetime.now()).year // 100 * 100
        return ctx.localize(dt.datetime(year=y, month=m, day=d)).date()

    @data_attribute(
        "character", aliases=["char", "chara"], is_tag=True, is_eq=True, is_plural=True
    )
    def character(self, value: EventMaster):
        return {*value.bonus.character_ids} if value.bonus else set()

    @character.init
    def init_character(self, info: DataAttributeInfo):
        info.value_mapping = {
            k: v.id for k, v in self.bot.aliases.characters_by_name.items()
        }

    @data_attribute("unit", is_sortable=True, is_tag=True, is_eq=True)
    def unit(self, value: EventMaster):
        units = {c.unit_id for c in value.bonus.characters} if value.bonus else set()
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
    def attribute(self, value: EventMaster):
        return value.bonus.attribute_id if value.bonus else -1

    @attribute.init
    def init_attribute(self, info: DataAttributeInfo):
        info.value_mapping = {
            k: v.id for k, v in self.bot.aliases.attributes_by_name.items()
        }

    @data_attribute(
        "type",
        value_mapping={t.name.lower(): t for t in EventType},
        is_sortable=True,
        is_tag=True,
        is_eq=True,
    )
    def type(self, value: EventMaster):
        return value.event_type_id

    @type.formatter
    def format_type(self, value: EventMaster):
        return value.event_type.name.ljust(6)

    @data_attribute(
        "parameter",
        aliases=["param"],
        value_mapping={
            "heart": 0,
            "technique": 1,
            "tech": 1,
            "physical": 2,
            "phys": 2,
            "no_parameter": 99,
            "noparameter": 99,
        },
        is_sortable=True,
        is_tag=True,
        is_eq=True,
    )
    def parameter(self, value: EventMaster):
        return (
            value.bonus.event_point_parameter_bonus_id
            if value.bonus and value.bonus.event_point_parameter_bonus_rate
            else 99
        )

    @data_attribute(
        "duration",
        aliases=["length", "time", "len"],
        is_sortable=True,
        is_comparable=True,
        is_eq=True,
    )
    def duration(self, value: EventMaster):
        return value.duration.total_seconds()

    @duration.formatter
    def format_duration(self, ctx, value: EventMaster):
        duration_hour_part = round((value.duration.seconds / 3600), 2)
        duration_hour_part = (
            duration_hour_part
            if not duration_hour_part.is_integer()
            else int(duration_hour_part)
        )
        unpadded = f"{value.duration.days}d {duration_hour_part}h"
        return unpadded.ljust(6)

    @duration.compare_converter
    def duration_compare_converter(self, ctx: PrefContext, s):
        time_units = {
            "d": 24 * 60 * 60,
            "h": 60 * 60,
            "m": 60,
            "s": 1,
        }

        total_seconds = 0
        time_parts = re.findall(r"(\d+)([dhms])", s)

        for part in time_parts:
            amount, unit = part
            total_seconds += int(amount) * time_units[unit]

        return total_seconds

    @command_source(
        command_args=dict(
            name="event", description="Displays event info.", help="!event cooking"
        )
    )
    def get_event_embed(self, ctx, event: EventMaster, server):
        l10n = self.l10n[ctx]

        timezone = ctx.preferences.timezone

        embed = discord.Embed(title=f"[{server.name}] {event.name}")

        embed.set_thumbnail(
            url=self.bot.asset_url + get_asset_filename(event.logo_path)
        )

        duration_hour_part = round((event.duration.seconds / 3600), 2)
        duration_hour_part = (
            duration_hour_part
            if not duration_hour_part.is_integer()
            else int(duration_hour_part)
        )
        duration_hours = round(
            (event.duration.days * 24 + event.duration.seconds / 3600), 2
        )
        duration_hours = (
            duration_hours if not duration_hours.is_integer() else int(duration_hours)
        )

        embed.add_field(
            name=l10n.format_value("info"),
            value=l10n.format_value(
                "info-desc",
                {
                    "duration-days": event.duration.days,
                    "duration-hours": duration_hour_part,
                    "duration-total-hours": duration_hours,
                    "start-date": discord.utils.format_dt(event.start_datetime),
                    "close-date": discord.utils.format_dt(
                        event.reception_close_datetime
                    ),
                    "rank-fix-date": discord.utils.format_dt(
                        event.rank_fix_start_datetime
                    ),
                    "results-date": discord.utils.format_dt(
                        event.result_announcement_datetime
                    ),
                    "end-date": discord.utils.format_dt(event.end_datetime),
                    "story-unlock-date": discord.utils.format_dt(
                        event.story_unlock_datetime
                    ),
                    "status": event.state().name,
                },
            ),
            inline=False,
        )

        def fmt_parameter_bonus(b: Optional[ParameterBonusMaster]):
            if not b or b.value == 0:
                return "None"
            return (
                f"{parameter_bonus_emoji_ids_by_parameter_id[b.target_id]} +{b.value}%"
            )

        embed.add_field(
            name=l10n.format_value("event-type"),
            value=l10n.format_value(
                "event-type-name", {"event-type": event.event_type.name}
            ),
            inline=True,
        )
        if event.bonus:
            embed.add_field(
                name=l10n.format_value("bonus-characters"),
                value="\n".join(
                    f"{unit_emoji_ids_by_unit_id[char.unit_id]} {char.full_name_english}"
                    for char in event.bonus.characters
                ),
                inline=True,
            )
            embed.add_field(
                name=l10n.format_value("bonus-attribute"),
                value=f"{attribute_emoji_ids_by_attribute_id[event.bonus.attribute_id]} "
                f"{event.bonus.attribute.en_name.capitalize()}"
                if event.bonus.attribute
                else "None",
                inline=True,
            )
            bonus_parameter_emoji = parameter_bonus_emoji_ids_by_parameter_id[
                event.bonus.event_point_parameter_bonus_id + 1
            ]
            param_bonus_unit = "%"
            if event.id <= 86:
                param_bonus_unit = ""
            embed.add_field(
                name=l10n.format_value("parameter-point-bonus"),
                value=f"{event.bonus.event_point_parameter_bonus_value}{param_bonus_unit} + {bonus_parameter_emoji} >{event.bonus.event_point_parameter_base_value}: 1{param_bonus_unit} / {event.bonus.event_point_parameter_bonus_rate}"
                if event.bonus.event_point_parameter_bonus_rate
                else l10n.format_value("no-parameter-point-bonus"),
                inline=False,
            )
            embed.add_field(
                name=l10n.format_value("point-bonus"),
                value=l10n.format_value(
                    "bonus-description",
                    {
                        "attribute": f"{event_point_emoji_id} +{event.bonus.attribute_match_point_bonus_value}%"
                        if event.bonus.attribute_match_point_bonus_value
                        else "None",
                        "character": f"{event_point_emoji_id} +{event.bonus.character_match_point_bonus_value}%"
                        if event.bonus.character_match_point_bonus_value
                        else "None",
                        "both": f"{event_point_emoji_id} +{event.bonus.all_match_point_bonus_value}%"
                        if event.bonus.all_match_point_bonus_value
                        else "None",
                    },
                ),
                inline=True,
            )
            embed.add_field(
                name=l10n.format_value("parameter-bonus"),
                value=l10n.format_value(
                    "bonus-description",
                    {
                        "attribute": fmt_parameter_bonus(
                            event.bonus.attribute_match_parameter_bonus
                        ),
                        "character": fmt_parameter_bonus(
                            event.bonus.character_match_parameter_bonus
                        ),
                        "both": fmt_parameter_bonus(
                            event.bonus.all_match_parameter_bonus
                        ),
                    },
                ),
                inline=True,
            )
        embed.set_footer(text=l10n.format_value("event-id", {"event-id": event.id}))

        return embed

    @list_formatter(
        name="event-search",
        command_args=dict(name="events", description="Lists events.", help="!events"),
    )
    def format_event_name_for_list(self, ctx, event: EventMaster):
        if not event.bonus:
            return f"`{grey_emoji_id}`+`{grey_emoji_id}`+`{grey_emoji_id}` {event.name}"
        bonuses = event.bonus.characters
        units = {character.unit.id for character in bonuses}
        if len(units) == 1:
            unit_emoji = unit_emoji_ids_by_unit_id.get(next(iter(units)), grey_emoji_id)
        else:
            unit_emoji = grey_emoji_id
        attribute_emoji = attribute_emoji_ids_by_attribute_id.get(
            event.bonus.attribute_id, grey_emoji_id
        )
        if event.bonus.event_point_parameter_bonus_rate:
            parameter_emoji = parameter_bonus_emoji_ids_by_parameter_id.get(
                event.bonus.event_point_parameter_bonus_id + 1, grey_emoji_id
            )
        else:
            parameter_emoji = grey_emoji_id
        return f"`{unit_emoji}`+`{attribute_emoji}`+`{parameter_emoji}` {event.name}"

    def get_event_banners(self, event: EventMaster, ctx):
        return tuple(
            gacha
            for gacha in self.bot.master_filters.gacha.values(ctx)
            if gacha.event == event
        )

    @get_event_embed.shortcut_button(name="Banners")
    async def banners_shortcut(
        self,
        ctx: PrefContext,
        event: EventMaster,
        server,
        interaction: discord.Interaction,
    ):
        f = ctx.bot.master_filters.gacha
        view, embed = f.get_simple_list_view(
            ctx, self.get_event_banners(event, ctx), server
        )
        await interaction.response.send_message(embed=embed, view=view)

    @banners_shortcut.check
    def check_banners_shortcut(self, event: EventMaster, ctx: PrefContext):
        return bool(self.get_event_banners(event, ctx))

    def get_event_cards(self, event: EventMaster, ctx):
        return tuple(
            card
            for card in self.bot.master_filters.cards.values(ctx)
            if card.event == event
        )

    @get_event_embed.shortcut_button(name="Cards")
    async def cards_shortcut(
        self,
        ctx: PrefContext,
        event: EventMaster,
        server,
        interaction: discord.Interaction,
    ):
        f = ctx.bot.master_filters.cards
        view, embed = f.get_simple_list_view(
            ctx, self.get_event_cards(event, ctx), server
        )
        await interaction.response.send_message(embed=embed, view=view)

    @cards_shortcut.check
    def check_cards_shortcut(self, event: EventMaster, ctx: PrefContext):
        return bool(self.get_event_cards(event, ctx))
