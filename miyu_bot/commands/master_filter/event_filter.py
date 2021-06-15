import datetime as dt
import re
from typing import Optional

import discord
from d4dj_utils.master.common_enums import EventType
from d4dj_utils.master.event_master import EventMaster, EventState

from miyu_bot.bot.bot import PrefContext
from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.common.emoji import unit_emoji_ids_by_unit_id, attribute_emoji_ids_by_attribute_id, \
    grey_emoji_id, event_point_emoji_id, parameter_bonus_emoji_ids_by_parameter_id
from miyu_bot.commands.master_filter.master_filter import MasterFilter, data_attribute, command_source, \
    DataAttributeInfo


class EventFilter(MasterFilter[EventMaster]):
    def get_name(self, value: EventMaster) -> str:
        return value.name

    def is_released(self, value: EventMaster) -> bool:
        return value.start_datetime < dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=3)

    def get_current(self, ctx) -> Optional[EventMaster]:
        """Returns the oldest event that has not ended or the newest event otherwise."""
        try:
            # NY event overlapped with previous event
            return min((v for v in self.values(ctx) if v.state() == EventState.Open),
                       key=lambda e: e.start_datetime)
        except ValueError:
            try:
                return min((v for v in self.values(ctx) if v.state() < EventState.Ended),
                           key=lambda e: e.start_datetime)
            except ValueError:
                return max(self.values(ctx), key=lambda v: v.start_datetime)

    get_latest_event = get_current

    @data_attribute('date',
                    aliases=['release', 'recent'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def date(self, ctx, value: EventMaster):
        return ctx.convert_tz(value.start_datetime).date()

    @date.formatter
    def format_date(self, ctx, value: EventMaster):
        dt = ctx.convert_tz(value.start_datetime)
        return f'{dt.year % 100:02}/{dt.month:02}/{dt.day:02}'

    @date.compare_converter
    def date_compare_converter(self, ctx: PrefContext, s):
        match = re.fullmatch(r'(\d+)/(\d+)/(\d+)', s)
        if not match:
            raise
        y, m, d = (int(n) for n in match.groups())
        if y < 100:
            y += ctx.localize(dt.datetime.now()).year // 100 * 100
        return ctx.localize(dt.datetime(year=y, month=m, day=d)).date()

    @data_attribute('character',
                    aliases=['char', 'chara'],
                    is_tag=True,
                    is_eq=True,
                    is_plural=True)
    def character(self, value: EventMaster):
        return {*value.bonus.character_ids}

    @character.init
    def init_character(self, info: DataAttributeInfo):
        info.value_mapping = {k: v.id for k, v in self.bot.aliases.characters_by_name.items()}

    @data_attribute('unit',
                    is_sortable=True,
                    is_tag=True,
                    is_eq=True)
    def unit(self, value: EventMaster):
        units = {c.unit_id for c in value.bonus.characters}
        if len(units) == 1:
            return next(iter(units))
        else:
            return -1

    @unit.init
    def init_unit(self, info: DataAttributeInfo):
        info.value_mapping = {**{k: v.id for k, v in self.bot.aliases.units_by_name.items()}, 'mixed': -1}

    @data_attribute('attribute',
                    is_sortable=True,
                    is_tag=True,
                    is_eq=True)
    def attribute(self, value: EventMaster):
        return value.bonus.attribute_id

    @attribute.init
    def init_attribute(self, info: DataAttributeInfo):
        info.value_mapping = {k: v.id for k, v in self.bot.aliases.attributes_by_name.items()}

    @data_attribute('type',
                    value_mapping={t.name.lower(): t for t in EventType},
                    is_sortable=True,
                    is_tag=True,
                    is_eq=True)
    def type(self, value: EventMaster):
        return value.event_type_id

    @type.formatter
    def format_type(self, value: EventMaster):
        return value.event_type.name.ljust(6)

    @data_attribute('parameter',
                    aliases=['param'],
                    value_mapping={'heart': 0,
                                   'technique': 1,
                                   'tech': 1,
                                   'physical': 2,
                                   'phys': 2,
                                   'no_parameter': 99,
                                   'noparameter': 99},
                    is_sortable=True,
                    is_tag=True,
                    is_eq=True)
    def parameter(self, value: EventMaster):
        return value.bonus.event_point_parameter_bonus_id if value.bonus.event_point_parameter_bonus_rate else 99

    @command_source(command_args=
                    dict(name='event',
                         description='Displays event info.',
                         help='!event cooking'),
                    list_command_args=
                    dict(name='events',
                         description='Lists events.',
                         help='!events'),
                    default_sort=date,
                    default_display=date,
                    list_name='event-search')
    def get_event_embed(self, ctx, event: EventMaster, server):
        l10n = self.l10n[ctx]

        timezone = ctx.preferences.timezone

        embed = discord.Embed(title=f'[{server.name}] {event.name}')

        embed.set_thumbnail(url=self.bot.asset_url + get_asset_filename(event.logo_path))

        duration_hour_part = round((event.duration.seconds / 3600), 2)
        duration_hour_part = duration_hour_part if not duration_hour_part.is_integer() else int(duration_hour_part)
        duration_hours = round((event.duration.days * 24 + event.duration.seconds / 3600), 2)
        duration_hours = duration_hours if not duration_hours.is_integer() else int(duration_hours)

        def fmt_date(date):
            return str(date)

        embed.add_field(name=l10n.format_value('info'),
                        value=l10n.format_value('info-desc', {
                            'duration-days': event.duration.days,
                            'duration-hours': duration_hour_part,
                            'duration-total-hours': duration_hours,
                            'start-date': fmt_date(event.start_datetime.astimezone(timezone)),
                            'close-date': fmt_date(event.reception_close_datetime.astimezone(timezone)),
                            'rank-fix-date': fmt_date(event.rank_fix_start_datetime.astimezone(timezone)),
                            'results-date': fmt_date(event.result_announcement_datetime.astimezone(timezone)),
                            'end-date': fmt_date(event.end_datetime.astimezone(timezone)),
                            'story-unlock-date': fmt_date(event.story_unlock_datetime.astimezone(timezone)),
                            'status': event.state().name,
                        }),
                        inline=False)
        embed.add_field(name=l10n.format_value('event-type'),
                        value=l10n.format_value('event-type-name', {'event-type': event.event_type.name}),
                        inline=True)
        embed.add_field(name=l10n.format_value('bonus-characters'),
                        value='\n'.join(
                            f'{self.bot.get_emoji(unit_emoji_ids_by_unit_id[char.unit_id])} {char.full_name_english}'
                            for char in event.bonus.characters
                        ),
                        inline=True)
        embed.add_field(name=l10n.format_value('bonus-attribute'),
                        value=f'{self.bot.get_emoji(attribute_emoji_ids_by_attribute_id[event.bonus.attribute_id])} '
                              f'{event.bonus.attribute.en_name.capitalize()}' if event.bonus.attribute else 'None',
                        inline=True)
        embed.add_field(name=l10n.format_value('parameter-point-bonus'),
                        value=l10n.format_value('parameter-point-bonus-description', {
                            'parameter-emoji': f'{self.bot.get_emoji(parameter_bonus_emoji_ids_by_parameter_id[event.bonus.event_point_parameter_bonus_id + 1])}',
                            'parameter-bonus-rate': event.bonus.event_point_parameter_bonus_rate
                        }) if event.bonus.event_point_parameter_bonus_rate else
                        l10n.format_value('no-parameter-point-bonus'),
                        inline=False)
        embed.add_field(name=l10n.format_value('point-bonus'),
                        value=l10n.format_value('bonus-description', {
                            'attribute': f'{self.bot.get_emoji(event_point_emoji_id)} +{event.bonus.attribute_match_point_bonus_value}%' if event.bonus.attribute_match_point_bonus_value else 'None',
                            'character': f'{self.bot.get_emoji(event_point_emoji_id)} +{event.bonus.character_match_point_bonus_value}%' if event.bonus.character_match_point_bonus_value else 'None',
                            'both': f'{self.bot.get_emoji(event_point_emoji_id)} +{event.bonus.all_match_point_bonus_value}%' if event.bonus.all_match_point_bonus_value else 'None',
                        }),
                        inline=True)
        embed.add_field(name=l10n.format_value('parameter-bonus'),
                        value=l10n.format_value('bonus-description', {
                            'attribute': f'{self.bot.get_emoji(parameter_bonus_emoji_ids_by_parameter_id[event.bonus.attribute_match_parameter_bonus_id])} +{event.bonus.attribute_match_parameter_bonus_value}%' if event.bonus.attribute_match_parameter_bonus_value else 'None',
                            'character': f'{self.bot.get_emoji(parameter_bonus_emoji_ids_by_parameter_id[event.bonus.character_match_parameter_bonus_id])} +{event.bonus.attribute_match_parameter_bonus_value}%' if event.bonus.attribute_match_parameter_bonus_value else 'None',
                            'both': f'{self.bot.get_emoji(parameter_bonus_emoji_ids_by_parameter_id[event.bonus.all_match_parameter_bonus_id])} +{event.bonus.all_match_parameter_bonus_value}%' if event.bonus.all_match_parameter_bonus_value else 'None',
                        }),
                        inline=True)
        embed.set_footer(text=l10n.format_value('event-id', {'event-id': event.id}))

        return embed

    @get_event_embed.list_formatter
    def format_event_name_for_list(self, ctx, event: EventMaster):
        bonuses = event.bonus.characters
        units = {character.unit.id for character in bonuses}
        if len(units) == 1:
            unit_emoji = self.bot.get_emoji(unit_emoji_ids_by_unit_id[next(iter(units))])
        else:
            unit_emoji = self.bot.get_emoji(grey_emoji_id)
        attribute_emoji = self.bot.get_emoji(
            attribute_emoji_ids_by_attribute_id.get(event.bonus.attribute_id, grey_emoji_id))
        if event.bonus.event_point_parameter_bonus_rate:
            parameter_emoji = self.bot.get_emoji(
                parameter_bonus_emoji_ids_by_parameter_id.get(event.bonus.event_point_parameter_bonus_id + 1,
                                                              grey_emoji_id))
        else:
            parameter_emoji = self.bot.get_emoji(grey_emoji_id)
        return f'`{unit_emoji}`+`{attribute_emoji}`+`{parameter_emoji}` {event.name}'
