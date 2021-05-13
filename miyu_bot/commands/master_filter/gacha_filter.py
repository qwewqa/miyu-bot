import re
from datetime import datetime
from typing import Sequence

import discord
from d4dj_utils.master.gacha_draw_master import GachaDrawMaster
from d4dj_utils.master.gacha_master import GachaMaster
from d4dj_utils.master.gacha_table_master import GachaTableMaster
from d4dj_utils.master.gacha_table_rate_master import GachaTableRateMaster

from miyu_bot.bot.bot import PrefContext
from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.common.emoji import unit_emoji_ids_by_unit_id, attribute_emoji_ids_by_attribute_id, grey_emoji_id
from miyu_bot.commands.common.formatting import format_info
from miyu_bot.commands.master_filter.master_filter import MasterFilter, data_attribute, DataAttributeInfo, \
    command_source


class GachaFilter(MasterFilter[GachaMaster]):
    def get_name(self, value: GachaMaster) -> str:
        return f'{value.name} {value.id}'

    @data_attribute('name',
                    aliases=['title'],
                    is_sortable=True)
    def name(self, value: GachaMaster):
        return value.name

    @data_attribute('date',
                    aliases=['release', 'recent'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def date(self, ctx, value: GachaMaster):
        return ctx.convert_tz(value.start_datetime).date()

    @date.formatter
    def format_date(self, ctx, value: GachaMaster):
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

    @data_attribute('character',
                    aliases=['char', 'chara'],
                    is_tag=True,
                    is_eq=True,
                    is_plural=True)
    def character(self, value: GachaMaster):
        return {c.character_id for c in value.pick_up_cards}

    @character.init
    def init_character(self, info: DataAttributeInfo):
        info.value_mapping = {k: v.id for k, v in self.bot.aliases.characters_by_name.items()}

    @data_attribute('unit',
                    is_sortable=True,
                    is_tag=True,
                    is_eq=True)
    def unit(self, value: GachaMaster):
        units = {c.character.unit_id for c in value.pick_up_cards}
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
    def attribute(self, value: GachaMaster):
        attributes = {c.attribute_id for c in value.pick_up_cards}
        if len(attributes) == 1:
            return next(iter(attributes))
        else:
            return -1

    @attribute.init
    def init_attribute(self, info: DataAttributeInfo):
        info.value_mapping = {k: v.id for k, v in self.bot.aliases.attributes_by_name.items()}

    @data_attribute('id',
                    is_sortable=True,
                    is_comparable=True)
    def id(self, value: GachaMaster):
        return value.id

    @id.formatter
    def format_id(self, value: GachaMaster):
        return str(value.id).zfill(5)

    @command_source(command_args=
                    dict(name='banner',
                         aliases=['gacha'],
                         description='Displays gacha banner info.',
                         help='!banner Shiny Smily Scratch'),
                    list_command_args=
                    dict(name='banners',
                         aliases=['gachas'],
                         description='Lists gacha banners.',
                         help='!banners'),
                    default_sort=date,
                    default_display=date,
                    list_name='Banner Search')
    def get_gacha_embed(self, ctx, gacha: GachaMaster):
        embed = discord.Embed(title=gacha.name)

        thumb_url = self.bot.asset_url + get_asset_filename(gacha.banner_path)

        embed.set_thumbnail(url=thumb_url)

        featured_text = '\n'.join(self.format_card_name_with_emoji(card) for card in gacha.pick_up_cards) or 'None'

        if len(featured_text) > 1024:
            featured_text = '\n'.join(self.format_card_name_short(card) for card in gacha.pick_up_cards) or 'None'
        if len(featured_text) > 1024:
            featured_text = 'Too Many Entries'

        embed.add_field(name='Info',
                        value=format_info({
                            'Start Date': f'{ctx.convert_tz(gacha.start_datetime)}',
                            'End Date': f'{ctx.convert_tz(gacha.end_datetime)}',
                            'Event': f'{gacha.event.name if gacha.event else "None"}',
                            'Pity Requirement': gacha.bonus_max_value or 'None',
                            'Type': gacha.gacha_type.name,
                        }),
                        inline=False)
        embed.add_field(name='Summary',
                        value=gacha.summary,
                        inline=False)
        embed.add_field(name='Featured',
                        value=featured_text or 'None',
                        inline=False)
        embed.add_field(name='Costs',
                        value='\n'.join(self.format_draw_data(draw) for draw in gacha.draw_data))

        embed.set_footer(text=f'Gacha Id: {gacha.id:>05}')

        return embed

    @get_gacha_embed.list_formatter
    def format_gacha_name_for_list(self, ctx, gacha):
        pick_ups = gacha.pick_up_cards
        units = {card.character.unit.id for card in pick_ups}
        attributes = {card.attribute.id for card in pick_ups}
        if len(units) == 1:
            unit_emoji = self.bot.get_emoji(unit_emoji_ids_by_unit_id[next(iter(units))])
        else:
            unit_emoji = self.bot.get_emoji(grey_emoji_id)
        if len(attributes) == 1:
            attribute_emoji = self.bot.get_emoji(attribute_emoji_ids_by_attribute_id[next(iter(attributes))])
        else:
            attribute_emoji = self.bot.get_emoji(grey_emoji_id)
        return f'`{unit_emoji}`+`{attribute_emoji}` {gacha.name}'

    @command_source(command_args=
                    dict(name='banner_rates',
                         aliases=['bannerrates', 'gacha_rates', 'gacharates',
                                  'banner_tables', 'bannertables', 'gacha_tables', 'gachatables',
                                  'banner_rate', 'bannerrate', 'gacha_rate', 'gacharate',
                                  'banner_table', 'bannertable', 'gacha_table', 'gachatable'],
                         description='Displays gacha banner rate info.',
                         help='!banner_rates Shiny Smily Scratch'),
                    default_sort=date)
    def get_gacha_table_embed(self, ctx, gacha: GachaMaster):
        embed = discord.Embed(title=gacha.name)

        thumb_url = self.bot.asset_url + get_asset_filename(gacha.banner_path)

        embed.set_thumbnail(url=thumb_url)

        def add_table_field(table_rate: GachaTableRateMaster, tables: Sequence[Sequence[GachaTableMaster]]):
            body = ''
            body_short = ''

            for table_normalized_rate, table in zip(table_rate.normalized_rates, tables):
                if table_normalized_rate == 0:
                    continue
                rates = [t.rate for t in table]
                total_rate = sum(rates)
                rate_up_rate = max(rates)

                # Exclude tables with no rate up, except those with very few rate ups (mainly for pity pull)
                if rate_up_rate == min(rates) and rate_up_rate / total_rate < 0.05:
                    continue

                rate_up_card_entries = [t for t in table if t.rate == rate_up_rate]

                for entry in rate_up_card_entries:
                    body += f'`{table_normalized_rate * entry.rate / total_rate * 100: >6.3f}% {self.format_card_name_for_list(entry.card)}`\n'
                    body_short += f'`{table_normalized_rate * entry.rate / total_rate * 100: >6.3f}% {self.format_card_name_short(entry.card)}`\n'

            if len(body) == 0:
                embed.add_field(name=table_rate.tab_name,
                                value='`Too many or no entries`',
                                inline=False)
            elif len(body) <= 1000:
                embed.add_field(name=table_rate.tab_name,
                                value=body,
                                inline=False)
            elif len(body_short) <= 1000:
                embed.add_field(name=table_rate.tab_name,
                                value=body_short,
                                inline=False)
            else:
                embed.add_field(name=table_rate.tab_name,
                                value='`Too many entries`',
                                inline=False)

        for table_rate in gacha.table_rates:
            add_table_field(table_rate, gacha.tables)

        if gacha.bonus_tables:
            add_table_field(gacha.bonus_table_rate, gacha.bonus_tables)

        if not embed.fields:
            embed.description = "None or too many rate up cards."

        return embed

    stock_names = {
        1: 'Diamond',
        2: 'Paid Diamond',
        901: 'Single Ticket',
        902: 'Ten Pull Ticket',
        903: '4★ Ticket'
    }

    def format_draw_data(self, draw: GachaDrawMaster):
        name = self.stock_names.get(draw.stock_id, draw.stock.name)
        pull_count = sum(draw.draw_amounts)
        if draw.draw_limit:
            return f'{pull_count} Pull: {draw.stock_amount}x {name}, Limit: {draw.draw_limit}, Refresh: {draw.is_reset_limit_every_day}'
        else:
            return f'{pull_count} Pull: {draw.stock_amount}x {name}'

    def format_card_name_for_list(self, card):
        unit_emoji = self.bot.get_emoji(unit_emoji_ids_by_unit_id[card.character.unit_id])
        attribute_emoji = self.bot.get_emoji(attribute_emoji_ids_by_attribute_id[card.attribute_id])
        return f'`{unit_emoji}`+`{attribute_emoji}` {card.rarity_id}★ {card.name} {card.character.first_name_english}'
        
    def format_card_name_short(self, card):
        return f'{card.rarity_id}★ {card.name} {card.character.first_name_english}'

    def format_card_name_with_emoji(self, card):
        unit_emoji = self.bot.get_emoji(unit_emoji_ids_by_unit_id[card.character.unit_id])
        attribute_emoji = self.bot.get_emoji(attribute_emoji_ids_by_attribute_id[card.attribute_id])
        return f'{unit_emoji} {attribute_emoji} {card.rarity_id}★ {card.name} {card.character.first_name_english}'
