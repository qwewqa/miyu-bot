import asyncio
import logging

import discord
from d4dj_utils.master.card_master import CardMaster
from discord.ext import commands

from main import masters
from miyu_bot.commands.common.emoji import rarity_emoji_ids
from miyu_bot.commands.common.master_asset_manager import hash_master
from miyu_bot.commands.common.reaction_message import run_tabbed_message


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
        card = masters.cards.get(arg, ctx)

        embeds = [self.get_card_embed(card, 0), self.get_card_embed(card, 1)]
        asyncio.ensure_future(run_tabbed_message(ctx, self.rarity_emoji, embeds, starting_index=1))

    def get_card_embed(self, card: CardMaster, limit_break):
        embed = discord.Embed(title=f'{card.rarity_id}★ {card.name} {card.character.full_name_english}')

        card_hash = hash_master(card)
        icon_path = card.icon_path(limit_break)
        thumb_url = f'https://qwewqa.github.io/d4dj-dumps/cards/icons/{icon_path.stem}_{card_hash}{icon_path.suffix}'
        art_path = card.art_path(limit_break)
        art_url = f'https://qwewqa.github.io/d4dj-dumps/cards/art/{art_path.stem}_{card_hash}{art_path.suffix}'

        embed.set_thumbnail(url=thumb_url)
        embed.set_image(url=art_url)

        return embed


def setup(bot):
    bot.add_cog(Card(bot))
