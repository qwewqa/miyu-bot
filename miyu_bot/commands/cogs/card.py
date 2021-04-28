import asyncio
import enum
import logging
from typing import Sequence

import discord
from PIL import ImageColor
from d4dj_utils.master.card_master import CardMaster
from d4dj_utils.master.event_specific_bonus_master import EventSpecificBonusMaster
from d4dj_utils.master.gacha_draw_master import GachaDrawMaster
from d4dj_utils.master.gacha_master import GachaMaster
from d4dj_utils.master.gacha_table_master import GachaTableMaster
from d4dj_utils.master.gacha_table_rate_master import GachaTableRateMaster
from d4dj_utils.master.skill_master import SkillMaster
from discord.ext import commands

from miyu_bot.bot.bot import D4DJBot
from miyu_bot.commands.common.argument_parsing import ParsedArguments, parse_arguments, list_operator_for, \
    full_operators
from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.common.emoji import rarity_emoji_ids, attribute_emoji_ids_by_attribute_id, \
    unit_emoji_ids_by_unit_id, parameter_bonus_emoji_ids_by_parameter_id, grey_emoji_id
from miyu_bot.commands.common.formatting import format_info
from miyu_bot.commands.common.reaction_message import run_tabbed_message, run_reaction_message, run_paged_message, \
    run_deletable_message, run_dynamically_paged_message


class Card(commands.Cog):
    bot: D4DJBot

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @property
    def rarity_emoji(self):
        return [self.bot.get_emoji(eid) for eid in rarity_emoji_ids.values()]

    @commands.command(name='card',
                      aliases=[],
                      description='Finds the card with the given name.',
                      help='!card secretcage')
    async def card(self, ctx: commands.Context, *, arg: ParsedArguments):
        cards = self.get_cards(ctx, arg)

        if not cards:
            await ctx.send(f'No results.')
            return

        if len(cards) == 1:
            embeds = self.get_card_embeds(cards[0])
            asyncio.ensure_future(run_tabbed_message(ctx, self.rarity_emoji, embeds, starting_index=1))
        else:
            message = await ctx.send(embed=self.get_card_embeds(cards[0])[1])

            emojis = self.rarity_emoji + ['◀', '▶']

            index = 0
            limit_break = 1

            async def callback(emoji):
                nonlocal index
                nonlocal limit_break
                try:
                    emoji_index = emojis.index(emoji)
                    if emoji_index == 0:
                        limit_break = 0
                    elif emoji_index == 1:
                        limit_break = 1
                    elif emoji_index == 2:
                        index -= 1
                    else:
                        index += 1

                    index = min(len(cards) - 1, max(0, index))

                    await message.edit(embed=self.get_card_embeds(cards[index])[limit_break])
                except ValueError:
                    pass

            asyncio.ensure_future(run_reaction_message(ctx, message, emojis, callback))

    def get_card_embeds(self, card):
        if card.rarity_id >= 3:
            return [self.get_card_embed(card, 0), self.get_card_embed(card, 1)]
        else:
            return [self.get_card_embed(card, 0)] * 2  # no actual awakened art for 1/2* cards

    @commands.command(name='cards',
                      aliases=[],
                      description='Lists cards matching the given search terms.',
                      help='!cards')
    async def cards(self, ctx: commands.Context, *, arg: commands.clean_content = ''):
        self.logger.info(f'Searching for cards "{arg}".')

        arguments = parse_arguments(arg)
        cards = self.get_cards(ctx, arguments)
        sort, sort_op = arguments.single_op('sort', None,
                                            allowed_operators=['<', '>', '='], converter=card_attribute_aliases)
        display, _op = arguments.single_op(['display', 'disp'], sort or CardAttribute.Power, allowed_operators=['='],
                                           converter=card_attribute_aliases)

        listing = []
        for card in cards:
            display_prefix = display.get_formatted_from_card(card)
            if display_prefix:
                listing.append(
                    f'{display_prefix} {self.format_card_name_for_list(card)}')
            else:
                listing.append(self.format_card_name_for_list(card))

        embed = discord.Embed(title=f'Card Search "{arg}"' if arg else 'Cards')
        asyncio.ensure_future(run_paged_message(ctx, embed, listing))

    @commands.command(name='cardexp',
                      aliases=['card_exp', 'cdexp'],
                      description='Displays card exp totals or the difference between levels.',
                      help='!cardexp 1-80')
    async def cardexp(self, ctx: commands.Context, *, arg: commands.clean_content = ''):
        assert isinstance(arg, str)
        exp = self.bot.assets.card_exp_master

        def comma_number(n):
            return '{:,}'.format(n)

        def format_exp(e):
            return comma_number(e.total_exp).rjust(9)

        if not arg:
            embed = discord.Embed(title='Card Exp',
                                  description='```' +
                                              '\n'.join(f'Lvl {n}: {format_exp(exp[n])}' for n in range(10, 90, 10)) +
                                              '```')
            await ctx.send(embed=embed)
        else:
            try:
                if arg.isnumeric():
                    level = int(arg)
                    level_total = exp[level].total_exp
                    desc = (f'```\n'
                            f'Total:  {comma_number(level_total)}\n'
                            f'Change: {comma_number(level_total - exp[level - 1].total_exp) if level > 1 else "N/A"}\n'
                            f'```')
                    await ctx.send(embed=discord.Embed(title=f'Card Exp Lvl {level}',
                                                       description=desc))
                else:
                    start, end = arg.split('-')
                    start = int(start)
                    end = int(end)
                    if start > end:
                        await ctx.send('End exp is greater than start exp.')
                        return
                    start_exp = exp[start]
                    end_exp = exp[end]
                    change_amount = end_exp.total_exp - start_exp.total_exp
                    embed = discord.Embed(title=f'Card Exp Lvl {start}-{end}',
                                          description=f'```\n'
                                                      f'Lvl {str(start).rjust(2)}: {format_exp(start_exp)}\n'
                                                      f'Lvl {str(end).rjust(2)}: {format_exp(end_exp)}\n'
                                                      f'Change: {comma_number(change_amount).rjust(9)}\n'
                                                      f'```')
                    await ctx.send(embed=embed)

            except Exception:
                await ctx.send(f'Invalid card exp {arg}')

    def get_cards(self, ctx, arguments: ParsedArguments):
        sort, sort_op = arguments.single_op('sort', None,
                                            allowed_operators=['<', '>', '='], converter=card_attribute_aliases)
        reverse_sort = sort_op == '<' or arguments.tag('reverse')
        # Not used, but here because it's a valid argument before running require_all_arguments_used.
        arguments.single_op(['display', 'disp'], sort, allowed_operators=['='],
                            converter=card_attribute_aliases)
        characters = {self.bot.aliases.characters_by_name[c].id
                      for c in arguments.words(self.bot.aliases.characters_by_name.keys()) |
                      arguments.tags(self.bot.aliases.characters_by_name.keys())}
        units = {self.bot.aliases.units_by_name[unit].id
                 for unit in arguments.tags(names=self.bot.aliases.units_by_name.keys(),
                                            aliases=self.bot.aliases.unit_aliases)}
        rarity_names = ['4*', '3*', '2*', '1*', r'4\*', r'3\*', r'2\*', r'1\*']
        rarities = {int(r[0]) for r in arguments.words(rarity_names) | arguments.tags(rarity_names)}
        attributes = {self.bot.aliases.attributes_by_name[a].id
                      for a in arguments.tags(self.bot.aliases.attributes_by_name.keys())}
        birthday = arguments.tag('birthday') | arguments.word('birthday')
        score_up_filters = arguments.repeatable_op(['skill', 'score_up', 'score'], allowed_operators=full_operators,
                                                   is_list=True, numeric=True)
        heal_filters = arguments.repeatable_op(['heal', 'recovery'], allowed_operators=full_operators, is_list=True,
                                               numeric=True)

        event_bonus = bool(arguments.tags(['event', 'eventbonus', 'event_bonus']))

        if event_bonus:
            latest_event = self.bot.asset_filters.events.get_latest_event(ctx)
            bonus: EventSpecificBonusMaster = latest_event.bonus

            if not characters:
                characters.update(bonus.character_ids)
            elif bonus.character_ids:
                characters = {char for char in characters if char in bonus.character_ids}

            if bonus.attribute_id:
                attributes = {bonus.attribute_id}

        arguments.require_all_arguments_used()

        cards = self.bot.asset_filters.cards.get_by_relevance(arguments.text(), ctx)
        if not (arguments.text() and sort is None):
            sort = sort or CardAttribute.Date
            cards = sorted(cards, key=lambda c: (sort.get_sort_key_from_card(c), c.max_power_with_limit_break))
            if sort in [CardAttribute.Power, CardAttribute.Date, CardAttribute.ScoreUp, CardAttribute.Heal]:
                cards = cards[::-1]
            if reverse_sort:
                cards = cards[::-1]

        if characters:
            cards = [card for card in cards if card.character.id in characters]
        if units:
            cards = [card for card in cards if card.character.unit.id in units]
        if rarities:
            cards = [card for card in cards if card.rarity_id in rarities]
        if attributes:
            cards = [card for card in cards if card.attribute.id in attributes]
        if birthday:
            cards = [card for card in cards if card.name == 'Birthday']

        for value, operation in score_up_filters:
            operator = list_operator_for(operation)
            cards = [card for card in cards if
                     operator(card.skill.score_up_rate + card.skill.perfect_score_up_rate, value)]
        for value, operation in heal_filters:
            operator = list_operator_for(operation)
            cards = [card for card in cards if operator(card.skill.max_recovery_value, value)]

        return cards

    def get_card_embed(self, card: CardMaster, limit_break):
        color_code = card.character.color_code
        color = discord.Colour.from_rgb(*ImageColor.getcolor(color_code, 'RGB')) if color_code else discord.Embed.Empty

        embed = discord.Embed(title=self.format_card_name(card), color=color)

        thumb_url = self.bot.asset_url + get_asset_filename(card.icon_path(limit_break))
        art_url = self.bot.asset_url + get_asset_filename(card.art_path(limit_break))

        embed.set_thumbnail(url=thumb_url)
        embed.set_image(url=art_url)

        embed.add_field(name='Info',
                        value=format_info({
                            'Rarity': f'{card.rarity_id}★',
                            'Character': f'{card.character.full_name_english}',
                            'Attribute': f'{self.bot.get_emoji(attribute_emoji_ids_by_attribute_id[card.attribute_id])} {card.attribute.en_name.capitalize()}',
                            'Unit': f'{self.bot.get_emoji(unit_emoji_ids_by_unit_id[card.character.unit_id])} {card.character.unit.name}',
                            'Release Date': f'{card.start_datetime}',
                            'Event': f'{card.event.name if card.event else "None"}',
                            'Gacha': f'{card.gacha.name if card.gacha else "None"}',
                            'Availability': f'{card.availability.name}',
                        }),
                        inline=False)
        embed.add_field(name='Parameters',
                        value=format_info({
                            f'Total': f'{"{:,}".format(card.max_power_with_limit_break)}',
                            f'{self.bot.get_emoji(parameter_bonus_emoji_ids_by_parameter_id[1])} Heart': f'{"{:,}".format(card.max_parameters_with_limit_break[0])}',
                            f'{self.bot.get_emoji(parameter_bonus_emoji_ids_by_parameter_id[2])} Technique': f'{"{:,}".format(card.max_parameters_with_limit_break[1])}',
                            f'{self.bot.get_emoji(parameter_bonus_emoji_ids_by_parameter_id[3])} Physical': f'{"{:,}".format(card.max_parameters_with_limit_break[2])}',
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

        return embed

    @commands.command(name='gacha',
                      aliases=['banner'],
                      description='Displays gacha info.',
                      help='!gacha Shiny Smily Scratch')
    async def gacha(self, ctx: commands.Context, *, arg: commands.clean_content = ''):
        self.logger.info(f'Searching for gacha "{arg}".')

        arguments = parse_arguments(arg)
        gachas = self.get_gachas(ctx, arguments)

        if not gachas:
            await ctx.send(f'No results.')
            return

        if len(gachas) == 1:
            embed = self.get_gacha_embed(gachas[0])
            asyncio.create_task(run_deletable_message(ctx, await ctx.send(embed=embed)))
        else:
            idx = 0

            def generator(n):
                nonlocal idx
                idx += n
                idx = max(0, min(idx, len(gachas) - 1))
                return self.get_gacha_embed(gachas[idx])

            asyncio.create_task(run_dynamically_paged_message(ctx, generator))

    @commands.command(name='gacha_tables',
                      aliases=['gacha_table', 'gachatable', 'gachatables'],
                      description='Displays gacha table info.',
                      help='!gacha_tables Shiny Smily Scratch')
    async def gacha_tables(self, ctx: commands.Context, *, arg: commands.clean_content = ''):
        self.logger.info(f'Searching for gacha "{arg}".')

        arguments = parse_arguments(arg)
        gachas = self.get_gachas(ctx, arguments)

        if not gachas:
            await ctx.send(f'No results.')
            return

        if len(gachas) == 1:
            embed = self.get_gacha_table_embed(gachas[0])
            asyncio.create_task(run_deletable_message(ctx, await ctx.send(embed=embed)))
        else:
            idx = 0

            def generator(n):
                nonlocal idx
                idx += n
                idx = max(0, min(idx, len(gachas) - 1))
                return self.get_gacha_table_embed(gachas[idx])

            asyncio.create_task(run_dynamically_paged_message(ctx, generator))

    @commands.command(name='gachas',
                      aliases=['banners'],
                      description='Lists gacha.',
                      help='!gachas')
    async def gachas(self, ctx: commands.Context, *, arg: commands.clean_content = ''):
        self.logger.info(f'Searching for gacha "{arg}".')

        arguments = parse_arguments(arg)
        gachas = self.get_gachas(ctx, arguments)
        embed = discord.Embed(title=f'Gacha List "{arg}"' if arg else 'Gacha List')
        asyncio.ensure_future(
            run_paged_message(ctx, embed, [self.format_gacha_name_for_list(gacha) for gacha in gachas]))

    def get_gachas(self, ctx, arguments: ParsedArguments):
        text = arguments.text()
        arguments.require_all_arguments_used()

        gacha = self.bot.asset_filters.gacha.get_by_relevance(text, ctx)

        if not text:
            gacha.sort(key=lambda g: (g.start_datetime, -g.ascending_sort_id))
            gacha.reverse()

        return gacha

    def get_gacha_embed(self, gacha: GachaMaster):
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
                            'Start Date': f'{gacha.start_datetime}',
                            'End Date': f'{gacha.end_datetime}',
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

        return embed

    def get_gacha_table_embed(self, gacha: GachaMaster):
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

    def format_card_name(self, card):
        return f'{card.rarity_id}★ {card.name} {card.character.full_name_english}'

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

    def format_gacha_name_for_list(self, gacha):
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


class CardAttribute(enum.Enum):
    Name = enum.auto()
    Character = enum.auto()
    Id = enum.auto()
    Power = enum.auto()
    Date = enum.auto()
    ScoreUp = enum.auto()
    Heal = enum.auto()

    def get_sort_key_from_card(self, card: CardMaster):
        return {
            self.Name: None,
            self.Character: card.character_id,
            self.Id: card.id,
            self.Power: card.max_power_with_limit_break,
            self.Date: card.start_datetime,
            self.ScoreUp: card.skill.score_up_rate + card.skill.perfect_score_up_rate,
            self.Heal: card.skill.max_recovery_value,
        }[self]

    def get_formatted_from_card(self, card: CardMaster):
        return {
            self.Name: None,
            self.Character: None,
            self.Id: str(card.id).zfill(9),
            self.Power: str(card.max_power_with_limit_break).rjust(5),
            self.Date: str(card.start_datetime.date()),
            self.ScoreUp: self.format_skill(card.skill),
            self.Heal: self.format_skill(card.skill),
        }[self]

    @staticmethod
    def format_skill(skill):
        return f'{str(skill.score_up_rate + skill.perfect_score_up_rate).rjust(2)}%,{str(skill.max_recovery_value).rjust(3)}hp'


card_attribute_aliases = {
    'name': CardAttribute.Name,
    'character': CardAttribute.Character,
    'char': CardAttribute.Character,
    'id': CardAttribute.Id,
    'power': CardAttribute.Power,
    'pow': CardAttribute.Power,
    'bp': CardAttribute.Power,
    'stats': CardAttribute.Power,
    'date': CardAttribute.Date,
    'skill': CardAttribute.ScoreUp,
    'score_up': CardAttribute.ScoreUp,
    'scoreup': CardAttribute.ScoreUp,
    'heal': CardAttribute.Heal,
    'recovery': CardAttribute.Heal,
}


def setup(bot):
    bot.add_cog(Card(bot))
