import functools
import logging
from io import BytesIO
from pathlib import Path
from typing import List, Optional

import discord
from PIL import Image
from d4dj_utils.master.card_master import CardMaster
from discord.ext import commands

from miyu_bot.bot.bot import D4DJBot
from miyu_bot.commands.common.argument_parsing import ParsedArguments
from miyu_bot.commands.common.emoji import rarity_emoji_ids


class Gacha(commands.Cog):
    bot: D4DJBot

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.images = []
        self.base_path = Path('card_icon')
        self.rarity_frames = {
            2: self.load_image('CharaIcon_2_Frame.png'),
            3: self.load_image('CharaIcon_3_Frame.png'),
            4: self.load_image('CharaIcon_4_Frame.png'),
        }
        self.unit_icons = {
            1: self.load_image('CharaIcon_DjUnitIcon_HA.png'),
            2: self.load_image('CharaIcon_DjUnitIcon_PP.png'),
            3: self.load_image('CharaIcon_DjUnitIcon_PM.png'),
            4: self.load_image('CharaIcon_DjUnitIcon_MMD.png'),
            5: self.load_image('CharaIcon_DjUnitIcon_LND.png'),
            6: self.load_image('CharaIcon_DjUnitIcon_LL.png'),
            30: self.load_image('CharaIcon_DjUnitIcon_Common.png'),
            50: self.load_image('CharaIcon_DjUnitIcon_Common.png'),
        }
        self.attribute_icons = {
            1: self.load_image('CharaIcon_TypeIcon_Street.png'),
            2: self.load_image('CharaIcon_TypeIcon_Party.png'),
            3: self.load_image('CharaIcon_TypeIcon_Cute.png'),
            4: self.load_image('CharaIcon_TypeIcon_Cool.png'),
            5: self.load_image('CharaIcon_TypeIcon_Elegant.png'),
        }
        self.rarity_icons = {
            0: self.load_image('CharaIcon_RarityIcon_Normal.png'),
            1: self.load_image('CharaIcon_RarityIcon_Evolution.png'),
        }

        for card in self.bot.assets.card_master.values():
            self.images.append(self.get_card_icon(card))

    def load_image(self, path):
        image = Image.open(self.base_path / path)
        self.images.append(image)
        return image

    def create_pull_image(self, cards: List[CardMaster], bonus: Optional[CardMaster] = None):
        if bonus:
            img = Image.new('RGBA', (259 * 6, 259 * 2), (255, 255, 255, 0))
        else:
            img = Image.new('RGBA', (259 * 5, 259 * 2), (255, 255, 255, 0))

        for i in range(5):
            for j in range(2):
                card = cards[i + j * 5]
                icon = self.get_card_icon(card)
                img.paste(icon, (259 * i, 259 * j), icon)

        if bonus:
            icon = self.get_card_icon(bonus)
            img.paste(icon, (259 * 5, 259 * 1), icon)

        return img

    def get_card_icon(self, card: CardMaster):
        # Just to avoid caching nonexistent icons, since an asset update may add them
        if not card.icon_path(0).exists():
            return Image.new('RGBA', (259, 259), (255, 255, 255, 0))
        else:
            return self._get_card_icon(card.id)

    @functools.lru_cache(None)
    def _get_card_icon(self, card_id: int):
        card = self.bot.assets.card_master[card_id]
        img = Image.new('RGBA', (259, 259), (255, 255, 255, 0))
        with Image.open(card.icon_path(0)) as icon:
            img.paste(icon.crop((11, 11, 247, 247)), (12, 12))

        # 1 star frames shouldn't really be needed for gacha anyways
        # 1 star cards have per-attribute frames so they'd need to be handled a bit differently
        if card.rarity_id >= 2:
            img.paste(self.rarity_frames[card.rarity_id], (0, 0), self.rarity_frames[card.rarity_id])
        img.paste(self.unit_icons[card.character.unit_id], (2, 2), self.unit_icons[card.character.unit_id])
        img.paste(self.attribute_icons[card.attribute_id], (194, 2), self.attribute_icons[card.attribute_id])
        for i in range(card.rarity_id):
            img.paste(self.rarity_icons[0], (3, 211 - i * 39), self.rarity_icons[0])
        return img

    def cog_unload(self):
        for image in self.images:
            image.close()

    @commands.command(name='card_icon',
                      aliases=['cardicon'],
                      hidden=True)
    async def card_icon(self, ctx: commands.Context, *, arg: ParsedArguments):
        tile = arg.tag('tile')
        bonus = arg.tag('bonus')
        name = arg.text()
        arg.require_all_arguments_used()
        card = self.bot.master_filters.cards.get(name, ctx)

        if tile:
            if bonus:
                img = await self.bot.loop.run_in_executor(self.bot.thread_pool,
                                                          functools.partial(self.create_pull_image, [card] * 10, card))
            else:
                img = await self.bot.loop.run_in_executor(self.bot.thread_pool,
                                                          functools.partial(self.create_pull_image, [card] * 10))
        else:
            img = await self.bot.loop.run_in_executor(self.bot.thread_pool, functools.partial(self.get_card_icon, card))

        buffer = BytesIO()
        img.save(buffer, 'png')
        buffer.seek(0)

        await ctx.send(file=discord.File(fp=buffer, filename='cardicon.png'))


def setup(bot):
    bot.add_cog(Gacha(bot))
