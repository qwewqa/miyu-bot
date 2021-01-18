import asyncio
import enum
import logging

import discord
from d4dj_utils.master.card_master import CardMaster
from d4dj_utils.master.event_master import EventMaster
from d4dj_utils.master.event_specific_bonus_master import EventSpecificBonusMaster
from d4dj_utils.master.skill_master import SkillMaster
from discord.ext import commands

from main import masters, asset_manager
from miyu_bot.commands.common.argument_parsing import ParsedArguments, parse_arguments, ArgumentError
from miyu_bot.commands.common.emoji import rarity_emoji_ids, attribute_emoji_ids_by_attribute_id, \
    unit_emoji_ids_by_unit_id, parameter_bonus_emoji_ids_by_parameter_id
from miyu_bot.commands.common.event import get_latest_event
from miyu_bot.commands.common.formatting import format_info
from miyu_bot.commands.common.master_asset_manager import hash_master
from miyu_bot.commands.common.name_aliases import characters_by_name, attributes_by_name, units_by_name, unit_aliases
from miyu_bot.commands.common.reaction_message import run_tabbed_message, run_reaction_message, run_paged_message


class Card(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @property
    def rarity_emoji(self):
        return [self.bot.get_emoji(eid) for eid in rarity_emoji_ids.values()]

    @commands.command(name='card',
                      aliases=[],
                      description='Finds the card with the given name.',
                      help='!card secretcage')
    async def card(self, ctx: commands.Context, *, arg: commands.clean_content):
        self.logger.info(f'Searching for card "{arg}".')

        try:
            arguments = parse_arguments(arg)
            cards = self.get_cards(ctx, arguments)
        except ArgumentError as e:
            await ctx.send(str(e))
            return

        if not cards:
            await ctx.send(f'No results for card "{arg}"')
            return

        if len(cards) == 1 or arguments.text():
            embeds = self.get_card_embeds(cards[0])
            asyncio.ensure_future(run_tabbed_message(ctx, self.rarity_emoji, embeds, starting_index=1))
        else:
            message = await ctx.send(embed=self.get_card_embeds(cards[0])[1])

            emojis = self.rarity_emoji + ['◀', '▶']

            index = 0
            limit_break = 1

            async def callback(emoji, _ctx, _message):
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

        try:
            arguments = parse_arguments(arg)
            cards = self.get_cards(ctx, arguments)
            sort, sort_op = arguments.single('sort', None,
                                             allowed_operators=['<', '>', '='], converter=card_attribute_aliases)
            display, _ = arguments.single(['display', 'disp'], sort or CardAttribute.Power, allowed_operators=['='],
                                          converter=card_attribute_aliases)
        except ArgumentError as e:
            await ctx.send(str(e))
            return

        listing = []
        for card in cards:
            display_prefix = display.get_formatted_from_card(card)
            if display_prefix:
                listing.append(
                    f'{display_prefix} : {self.format_card_name(card)}')
            else:
                listing.append(self.format_card_name(card))

        embed = discord.Embed(title=f'Card Search "{arg}"' if arg else 'Cards')
        asyncio.ensure_future(run_paged_message(ctx, embed, listing))

    def get_cards(self, ctx, arguments: ParsedArguments):
        sort, sort_op = arguments.single('sort', None,
                                         allowed_operators=['<', '>', '='], converter=card_attribute_aliases)
        reverse_sort = sort_op == '<' or arguments.tag('reverse')
        # Not used, but here because it's a valid argument before running require_all_arguments_used.
        display, _ = arguments.single(['display', 'disp'], sort, allowed_operators=['='],
                                      converter=card_attribute_aliases)
        characters = {characters_by_name[c].id for c in arguments.words(characters_by_name.keys())}
        units = {units_by_name[unit].id
                 for unit in arguments.tags(names=units_by_name.keys(), aliases=unit_aliases)}
        rarities = {int(r[0]) for r in arguments.words(['4*', '3*', '2*', '1*', r'4\*', r'3\*', r'2\*', r'1\*'])}
        attributes = {attributes_by_name[a].id for a in arguments.words(attributes_by_name.keys())}

        event_bonus = bool(arguments.tags(['event', 'eventbonus', 'event_bonus']))

        if event_bonus:
            latest_event = get_latest_event(ctx)
            bonus: EventSpecificBonusMaster = latest_event.bonus

            if not characters:
                characters.update(bonus.character_ids)
            elif bonus.character_ids:
                characters = {char for char in characters if char in bonus.character_ids}

            if bonus.attribute_id:
                attributes = {bonus.attribute_id}

            if not arguments.has_named('sort'):
                sort = CardAttribute.Date

        arguments.require_all_arguments_used()

        cards = masters.cards.get_sorted(arguments.text(), ctx)
        if not (arguments.text() and sort is None):
            sort = sort or CardAttribute.Power
            cards = sorted(cards, key=lambda c: (sort.get_sort_key_from_card(c), c.max_power_with_limit_break))
            if sort in [CardAttribute.Power, CardAttribute.Date]:
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

        return cards

    def get_card_embed(self, card: CardMaster, limit_break):
        embed = discord.Embed(title=self.format_card_name(card))

        card_hash = hash_master(card)
        icon_path = card.icon_path(limit_break)
        thumb_url = f'https://qwewqa.github.io/d4dj-dumps/cards/icons/{icon_path.stem}_{card_hash}{icon_path.suffix}'
        art_path = card.art_path(limit_break)
        art_url = f'https://qwewqa.github.io/d4dj-dumps/cards/art/{art_path.stem}_{card_hash}{art_path.suffix}'

        embed.set_thumbnail(url=thumb_url)
        embed.set_image(url=art_url)

        embed.add_field(name='Info',
                        value=format_info({
                            'Rarity': f'{card.rarity_id}★',
                            'Character': f'{card.character.full_name_english}',
                            'Attribute': f'{self.bot.get_emoji(attribute_emoji_ids_by_attribute_id[card.attribute_id])} {card.attribute.en_name.capitalize()}',
                            'Unit': f'{self.bot.get_emoji(unit_emoji_ids_by_unit_id[card.character.unit_id])} {card.character.unit.name}',
                            'Release Date': f'{card.start_datetime}',
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
                            'Score Up': f'{skill.score_up_rate}%',
                            'Heal': (f'{skill.min_recovery_value}-{skill.max_recovery_value}'
                                     if skill.min_recovery_value != skill.max_recovery_value
                                     else str(skill.min_recovery_value))
                        }),
                        inline=True)

        return embed

    def format_card_name(self, card):
        return f'{card.rarity_id}★ {card.name} {card.character.full_name_english}'


class CardAttribute(enum.Enum):
    Name = enum.auto()
    Id = enum.auto()
    Power = enum.auto()
    Date = enum.auto()

    def get_sort_key_from_card(self, card: CardMaster):
        return {
            self.Name: card.name,
            self.Id: card.id,
            self.Power: card.max_power_with_limit_break,
            self.Date: card.start_datetime,
        }[self]

    def get_formatted_from_card(self, card: CardMaster):
        return {
            self.Name: None,
            self.Id: str(card.id).zfill(9),
            self.Power: str(card.max_power_with_limit_break).rjust(5),
            self.Date: str(card.start_datetime.date()),
        }[self]


card_attribute_aliases = {
    'name': CardAttribute.Name,
    'id': CardAttribute.Id,
    'power': CardAttribute.Power,
    'stats': CardAttribute.Power,
    'date': CardAttribute.Date,
}


def setup(bot):
    bot.add_cog(Card(bot))
