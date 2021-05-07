import re
from datetime import datetime
from typing import List

import discord
from PIL import ImageColor
from d4dj_utils.master.card_master import CardMaster
from d4dj_utils.master.event_specific_bonus_master import EventSpecificBonusMaster
from d4dj_utils.master.skill_master import SkillMaster

from miyu_bot.bot.bot import PrefContext
from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.common.emoji import attribute_emoji_ids_by_attribute_id, unit_emoji_ids_by_unit_id, \
    parameter_bonus_emoji_ids_by_parameter_id, rarity_emoji_ids
from miyu_bot.commands.common.formatting import format_info
from miyu_bot.commands.master_filter.master_filter import MasterFilter, data_attribute, command_source, \
    DataAttributeInfo


class CardFilter(MasterFilter[CardMaster]):
    def get_name(self, value: CardMaster) -> str:
        return f'{value.name} {value.character.first_name_english}'

    @data_attribute('name',
                    aliases=['title'],
                    is_sortable=True)
    def name(self, value: CardMaster):
        return value.name

    @data_attribute('character',
                    aliases=['char', 'chara'],
                    is_sortable=True,
                    is_keyword=True,
                    is_tag=True,
                    is_eq=True)
    def character(self, value: CardMaster):
        return value.character_id

    @character.init
    def init_character(self, info: DataAttributeInfo):
        info.value_mapping = {k: v.id for k, v in self.bot.aliases.characters_by_name.items()}

    @data_attribute('unit',
                    is_sortable=True,
                    is_tag=True,
                    is_eq=True)
    def unit(self, value: CardMaster):
        return value.character.unit_id

    @unit.init
    def init_unit(self, info: DataAttributeInfo):
        info.value_mapping = {k: v.id for k, v in self.bot.aliases.units_by_name.items()}

    @data_attribute('attribute',
                    is_sortable=True,
                    is_tag=True,
                    is_eq=True)
    def attribute(self, value: CardMaster):
        return value.attribute_id

    @attribute.init
    def init_attribute(self, info: DataAttributeInfo):
        info.value_mapping = {k: v.id for k, v in self.bot.aliases.attributes_by_name.items()}

    @data_attribute('id',
                    is_sortable=True,
                    is_comparable=True)
    def id(self, value: CardMaster):
        return value.id

    @id.formatter
    def format_id(self, value: CardMaster):
        return str(value.id).zfill(8)

    @data_attribute('power',
                    aliases=['pow', 'bp'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def power(self, value: CardMaster):
        return value.max_power_with_limit_break

    @power.formatter
    def format_power(self, value: CardMaster):
        return str(value.max_power_with_limit_break).rjust(5)

    @data_attribute('date',
                    aliases=['release', 'recent'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def date(self, ctx, value: CardMaster):
        return ctx.convert_tz(value.start_datetime).date()

    @date.formatter
    def format_date(self, ctx, value: CardMaster):
        dt = ctx.convert_tz(value.start_datetime)
        return f'{dt.year % 100:02}/{dt.month:02}/{dt.day:02}'

    @date.compare_converter
    def date_compare_converter(self, ctx: PrefContext, s):
        match = re.fullmatch(r'(\d+)/(\d+)/(\d+)', s)
        if not match:
            raise
        y, m, d = (int(n) for n in match.groups())
        if y < 100:
            y += ctx.localize(datetime.now()).year // 100 * 100
        return ctx.localize(datetime(year=y, month=m, day=d)).date()


    @data_attribute('rarity',
                    aliases=['stars'],
                    is_keyword=True,
                    value_mapping={r'4*': 4,
                                   r'4\*': 4,
                                   r'3*': 3,
                                   r'3\*': 3,
                                   r'2*': 2,
                                   r'2\*': 1,
                                   r'1*': 1,
                                   r'1\*': 1},
                    is_sortable=True,
                    reverse_sort=True)
    def rarity(self, value: CardMaster):
        return value.rarity_id

    @data_attribute('skill',
                    aliases=['score_up', 'score'],
                    is_comparable=True,
                    is_sortable=True,
                    reverse_sort=True)
    def skill(self, value: CardMaster):
        skill = value.skill
        return skill.score_up_rate + skill.perfect_score_up_rate

    @skill.formatter
    def skill_formatter(self, value: CardMaster):
        skill = value.skill
        if skill.perfect_score_up_rate:
            return f'{skill.score_up_rate + skill.perfect_score_up_rate:>2} ({skill.perfect_score_up_rate:>2}p)'
        else:
            return f'{skill.score_up_rate + skill.perfect_score_up_rate:>2}      '

    @data_attribute('event',
                    aliases=['event_bonus', 'eventbonus', 'bonus'],
                    is_comparable=True,
                    is_sortable=True,
                    is_flag=True,
                    reverse_sort=True)
    def event(self, value: CardMaster):
        return value.event.id if value.event else -1

    @event.flag_callback
    def event_flag_callback(self, ctx, values: List[CardMaster]):
        latest_event = self.bot.master_filters.events.get_latest_event(ctx)
        bonus: EventSpecificBonusMaster = latest_event.bonus
        character_ids = {*bonus.character_ids}
        return [v for v in values if v.character_id in character_ids and v.attribute_id == bonus.attribute_id]

    @command_source(command_args=
                    dict(name='card',
                         description='Displays card info.',
                         help='!card secretcage'),
                    list_command_args=
                    dict(name='cards',
                         description='Lists cards.',
                         help='!cards'),
                    default_sort=date,
                    default_display=power,
                    tabs=list(rarity_emoji_ids.values()),
                    default_tab=1,
                    suffix_tab_aliases={'untrained': 0, 'trained': 1},
                    list_name='Card Search')
    def get_card_embed(self, ctx, card: CardMaster, limit_break):
        if card.rarity_id <= 2:
            limit_break = 0

        color_code = card.character.color_code
        color = discord.Colour.from_rgb(*ImageColor.getcolor(color_code, 'RGB')) if color_code else discord.Embed.Empty

        embed = discord.Embed(title=self.format_card_name(card), color=color)

        thumb_url = ctx.bot.asset_url + get_asset_filename(card.icon_path(limit_break))
        art_url = ctx.bot.asset_url + get_asset_filename(card.art_path(limit_break))

        embed.set_thumbnail(url=thumb_url)
        embed.set_image(url=art_url)

        embed.add_field(name='Info',
                        value=format_info({
                            'Rarity': f'{card.rarity_id}★',
                            'Character': f'{card.character.full_name_english}',
                            'Attribute': f'{ctx.bot.get_emoji(attribute_emoji_ids_by_attribute_id[card.attribute_id])} {card.attribute.en_name.capitalize()}',
                            'Unit': f'{ctx.bot.get_emoji(unit_emoji_ids_by_unit_id[card.character.unit_id])} {card.character.unit.name}',
                            'Release Date': f'{ctx.convert_tz(card.start_datetime)}',
                            'Event': f'{card.event.name if card.event else "None"}',
                            'Gacha': f'{card.gacha.name if card.gacha else "None"}',
                            'Availability': f'{card.availability.name}',
                        }),
                        inline=False)
        embed.add_field(name='Parameters',
                        value=format_info({
                            f'Total': f'{"{:,}".format(card.max_power_with_limit_break)}',
                            f'{ctx.bot.get_emoji(parameter_bonus_emoji_ids_by_parameter_id[1])} Heart': f'{"{:,}".format(card.max_parameters_with_limit_break[0])}',
                            f'{ctx.bot.get_emoji(parameter_bonus_emoji_ids_by_parameter_id[2])} Technique': f'{"{:,}".format(card.max_parameters_with_limit_break[1])}',
                            f'{ctx.bot.get_emoji(parameter_bonus_emoji_ids_by_parameter_id[3])} Physical': f'{"{:,}".format(card.max_parameters_with_limit_break[2])}',
                        }),
                        inline=True)
        skill: SkillMaster = card.skill
        embed.add_field(name='Skill',
                        value=format_info({
                            'Name': card.skill_name,
                            'Duration': f'{skill.min_seconds}-{skill.max_seconds}s',
                            'Score Up': f'{skill.score_up_rate}%' if not skill.perfect_score_up_rate else f'{skill.score_up_rate}% + {skill.perfect_score_up_rate}% perfect',
                            'Heal': (f'{skill.min_recovery_value}-{skill.max_recovery_value}'
                                     if skill.min_recovery_value != skill.max_recovery_value
                                     else str(skill.min_recovery_value))
                        }),
                        inline=True)
        embed.set_footer(text=f'Card Id: {card.id:0>8}')

        return embed

    def format_card_name(self, card):
        return f'{card.rarity_id}★ {card.name} {card.character.full_name_english}'

    @get_card_embed.list_formatter
    def format_card_name_for_list(self, card):
        unit_emoji = self.bot.get_emoji(unit_emoji_ids_by_unit_id[card.character.unit_id])
        attribute_emoji = self.bot.get_emoji(attribute_emoji_ids_by_attribute_id[card.attribute_id])
        return f'`{unit_emoji}`+`{attribute_emoji}` {card.rarity_id}★ {card.name} {card.character.first_name_english}'
