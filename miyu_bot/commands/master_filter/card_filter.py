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
from miyu_bot.commands.master_filter.master_filter import MasterFilter, data_attribute, command_source, \
    DataAttributeInfo, list_formatter


class CardFilter(MasterFilter[CardMaster]):
    def get_name(self, value: CardMaster) -> str:
        return f'{value.name} {value.character.first_name_english}'

    def get_select_name(self, value: CardMaster):
        emoji = attribute_emoji_ids_by_attribute_id[value.attribute_id]
        return value.character.full_name_english, value.name, emoji

    def is_released(self, value: CardMaster) -> bool:
        return value.is_available

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
                    is_default_display=True,
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True,
                    help_sample_argument='27649')
    def power(self, value: CardMaster):
        return value.max_power_with_limit_break

    @power.formatter
    def format_power(self, value: CardMaster):
        return str(value.max_power_with_limit_break).rjust(5)

    @data_attribute('heart',
                    aliases=['hrt'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True,
                    help_sample_argument='9082')
    def heart(self, value: CardMaster):
        return value.max_parameters_with_limit_break[0]

    @heart.formatter
    def format_heart(self, value: CardMaster):
        return str(value.max_parameters_with_limit_break[0]).rjust(5)

    @data_attribute('technique',
                    aliases=['tech', 'technical'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True,
                    help_sample_argument='9219')
    def technique(self, value: CardMaster):
        return value.max_parameters_with_limit_break[1]

    @technique.formatter
    def format_technique(self, value: CardMaster):
        return str(value.max_parameters_with_limit_break[1]).rjust(5)

    @data_attribute('physical',
                    aliases=['phys', 'physic', 'physics'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True,
                    help_sample_argument='9348')
    def physical(self, value: CardMaster):
        return value.max_parameters_with_limit_break[2]

    @physical.formatter
    def format_physical(self, value: CardMaster):
        return str(value.max_parameters_with_limit_break[2]).rjust(5)

    @data_attribute('date',
                    aliases=['release', 'recent'],
                    is_default_sort=True,
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True,
                    help_sample_argument='2020/12/31')
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
                                   r'2\*': 2,
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
                    reverse_sort=True,
                    help_sample_argument='50')
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

    @command_source(command_args=
                    dict(name='card',
                         description='Displays card info.',
                         help='!card secretcage'),
                    tabs=list(rarity_emoji_ids.values()),
                    default_tab=1,
                    suffix_tab_aliases={'untrained': 0, 'trained': 1})
    def get_card_embed(self, ctx, card: CardMaster, limit_break, server):
        l10n = self.l10n[ctx]

        if card.rarity_id <= 2:
            limit_break = 0

        color_code = card.character.color_code
        color = discord.Colour.from_rgb(*ImageColor.getcolor(color_code, 'RGB')) if color_code else discord.Embed.Empty

        embed = discord.Embed(title=f'[{server.name}] {self.format_card_name(card)}', color=color)

        thumb_url = ctx.bot.asset_url + get_asset_filename(card.icon_path(limit_break))
        art_url = ctx.bot.asset_url + get_asset_filename(card.art_path(limit_break))

        embed.set_thumbnail(url=thumb_url)
        embed.set_image(url=art_url)

        embed.add_field(name=l10n.format_value('info'),
                        value=l10n.format_value('info-desc', {
                            'rarity': f'{card.rarity_id}★',
                            'character': f'{card.character.full_name_english}',
                            'attribute': f'{attribute_emoji_ids_by_attribute_id[card.attribute_id]} {card.attribute.en_name.capitalize()}',
                            'unit': f'{unit_emoji_ids_by_unit_id[card.character.unit_id]} {card.character.unit.name}',
                            'release-date': discord.utils.format_dt(card.start_datetime),
                            'event': f'{card.event.name if card.event else "None"}',
                            'gacha': f'{card.gacha.name if card.gacha else "None"}',
                            'availability': card.availability.name,
                        }),
                        inline=False)
        embed.add_field(name=l10n.format_value('parameters'),
                        value=l10n.format_value('parameters-desc', {
                            'total': card.max_power_with_limit_break,
                            'heart': card.max_parameters_with_limit_break[0],
                            'technique': card.max_parameters_with_limit_break[1],
                            'physical': card.max_parameters_with_limit_break[2],
                            'heart-emoji': str(parameter_bonus_emoji_ids_by_parameter_id[1]),
                            'technique-emoji': str(parameter_bonus_emoji_ids_by_parameter_id[2]),
                            'physical-emoji': str(parameter_bonus_emoji_ids_by_parameter_id[3]),
                        }),
                        inline=True)
        skill: SkillMaster = card.skill
        embed.add_field(name=l10n.format_value('skill'),
                        value=l10n.format_value('skill-desc', {
                            'name': card.skill_name,
                            'duration': f'{skill.min_seconds}-{skill.max_seconds}s',
                            'score-up': f'{skill.score_up_rate}%' if not skill.perfect_score_up_rate else f'{skill.score_up_rate}% + {skill.perfect_score_up_rate}% perfect',
                            'heal': (f'{skill.min_recovery_value}-{skill.max_recovery_value}'
                                     if skill.min_recovery_value != skill.max_recovery_value
                                     else str(skill.min_recovery_value))
                        }),
                        inline=True)
        embed.set_footer(text=l10n.format_value('card-id', {'card-id': f'{card.id:0>8}'}))

        return embed

    def format_card_name(self, card):
        return f'{card.rarity_id}★ {card.name} {card.character.full_name_english}'

    @list_formatter(name='card-search',
                    command_args=
                    dict(name='cards',
                         description='Lists cards.',
                         help='!cards'))
    def format_card_name_for_list(self, card):
        unit_emoji = unit_emoji_ids_by_unit_id[card.character.unit_id]
        attribute_emoji = attribute_emoji_ids_by_attribute_id[card.attribute_id]
        return f'`{unit_emoji}`+`{attribute_emoji}` {card.rarity_id}★ {card.name} {card.character.first_name_english}'

    @get_card_embed.shortcut_button(name='Gacha')
    async def gacha_shortcut(self, ctx, card: CardMaster, server, interaction: discord.Interaction):
        f = ctx.bot.master_filters.gacha
        view, embed = f.get_simple_detail_view(ctx, [card.gacha], server, f.get_gacha_embed)
        await interaction.response.send_message(embed=embed, view=view)

    @gacha_shortcut.check
    def check_gacha_shortcut(self, card: CardMaster):
        return card.gacha is not None

    @get_card_embed.shortcut_button(name='Event')
    async def event_shortcut(self, ctx, card: CardMaster, server, interaction: discord.Interaction):
        f = ctx.bot.master_filters.events
        view, embed = f.get_simple_detail_view(ctx, [card.event], server, f.get_event_embed)
        await interaction.response.send_message(embed=embed, view=view)

    @event_shortcut.check
    def check_event_shortcut(self, card: CardMaster):
        return card.event is not None
