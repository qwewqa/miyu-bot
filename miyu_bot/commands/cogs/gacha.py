import asyncio
import functools
import itertools
import logging
import math
import random
import typing
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple, Union

import discord
from PIL import Image
from d4dj_utils.master.asset_manager import AssetManager
from d4dj_utils.master.card_master import CardMaster
from d4dj_utils.master.gacha_draw_master import GachaDrawMaster
from d4dj_utils.master.gacha_master import GachaMaster
from discord.ext import commands
from tortoise import BaseDBAsyncClient
from tortoise.expressions import F
from tortoise.transactions import in_transaction

from miyu_bot.bot.bot import MiyuBot, PrefContext
from miyu_bot.bot.models import GachaState, CollectionEntry
from miyu_bot.bot.servers import Server
from miyu_bot.commands.common.argument_parsing import ParsedArguments
from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.master_filter.localization_manager import LocalizationManager


class Gacha(commands.Cog):
    bot: MiyuBot

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

        for card in self.bot.assets[Server.JP].card_master.values():
            self.images.append(self.get_card_icon(card))

        self.l10n = LocalizationManager(self.bot.fluent_loader, 'gacha.ftl')
        self.pull_locks = defaultdict(lambda: asyncio.Lock())

    def load_image(self, path):
        image = Image.open(self.base_path / path)
        self.images.append(image)
        return image

    async def create_pull_image(self,
                                cards: List[CardMaster],
                                bonus: Optional[CardMaster] = None,
                                sub_bonus: Optional[CardMaster] = None):
        if bonus:
            cards = cards + [bonus]
        if sub_bonus:
            cards = cards + [sub_bonus]
        row_size = min(15, max(5, (len(cards) - 1) // 5 + 4))
        return await self.create_card_image_grid_async(cards, row_size)

    async def create_card_image_grid_async(self, cards: List[CardMaster], row_size: int = 16):
        return await self.bot.loop.run_in_executor(
            self.bot.thread_pool,
            functools.partial(self.create_card_image_grid, cards, row_size),
        )

    def create_card_image_grid(self, cards: List[CardMaster], row_size: int = 20):
        column_count = math.ceil(len(cards) / row_size)
        img = Image.new('RGBA', (259 * row_size, max(1, 259 * column_count)), (255, 255, 255, 0))

        for i, card in enumerate(cards):
            icon = self.get_card_icon(card)
            img.paste(icon, (259 * (i % row_size), 259 * (i // row_size)), icon)

        return img

    def get_card_icon(self, card: CardMaster):
        # Just to avoid caching nonexistent icons, since an asset update may add them
        if not card.icon_path(0).exists():
            return Image.new('RGBA', (259, 259), (255, 255, 255, 0))
        else:
            return self._get_card_icon(card.id)

    @functools.lru_cache(None)
    def _get_card_icon(self, card_id: int):
        card = self.bot.assets[Server.JP].card_master[card_id]
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

    @commands.command(name='pull',
                      aliases=['gachasim', 'roll'],
                      description='Simulates gacha given the gacha id (can be found using the !banner command and checking the footer).',
                      help='!pull 1')
    async def pull(self, ctx: PrefContext, *, arg: Optional[ParsedArguments]):
        if not arg:
            await ctx.send('A gacha id must be given (can be found using the !banner command and checking the footer).')
            return
        name = arg.text()
        arg.require_all_arguments_used()
        if not name.isnumeric():
            await ctx.send('A gacha id must be given (can be found using the !banner command and checking the footer).')
            return
        gacha: GachaMaster = self.bot.master_filters.gacha.get_by_id(int(name), ctx)
        if not gacha:
            await ctx.send('Unknown banner.')
            return
        draw_data = [d for d in gacha.draw_data
                     if (d.stock_id == 902) or (d.stock_id in (1, 2) and d.stock_amount == 3000)]
        if len(draw_data) != 1:
            await ctx.send('Unsupported banner.')
            return
        draw_data = draw_data[0]
        view, embed, file = await self.do_gacha_draw_and_get_message_data(ctx.author, gacha, draw_data, ctx.assets)

        await ctx.send(view=view, embed=embed, file=file)

    @commands.command(name='pullstats',
                      aliases=['rollstats'],
                      description='Returns information about pulled cards.',
                      help='!pullstats')
    async def pullstats(self, ctx: PrefContext, banner: Optional[int] = None):
        if banner is None:
            await self.send_overall_pulls_message(ctx, ctx.author.id)
        else:
            await self.send_banner_pulls_message(ctx, ctx.author.id, banner)

    async def send_banner_pulls_message(self, ctx: PrefContext, user_id: int, gacha_id: int):
        gacha: GachaMaster = self.bot.master_filters.gacha.get(gacha_id, ctx)

        if not gacha:
            await ctx.send('Banner not found.')
            return

        entries = await CollectionEntry.filter(user_id=user_id, gacha_id=gacha_id)
        card_ids = {e.card_id for e in entries}
        cards = [self.bot.assets[Server.JP].card_master[cid] for cid in card_ids]
        cards = sorted(cards, key=lambda card: (-card.rarity_id, -card.start_datetime.timestamp(), card.id))

        img = await self.create_card_image_grid_async(cards)

        buffer = BytesIO()
        img.save(buffer, 'png')
        buffer.seek(0)

        embed = discord.Embed(title=f'{gacha.name}')
        embed.set_image(url='attachment://cards.png')

        await ctx.send(embed=embed, file=discord.File(fp=buffer, filename='cards.png'))

    async def send_overall_pulls_message(self, ctx: PrefContext, user_id: int):
        entries = await CollectionEntry.filter(user_id=user_id)
        card_ids = {e.card_id for e in entries}
        cards = [self.bot.assets[Server.JP].card_master[cid] for cid in card_ids]
        cards = sorted(cards, key=lambda card: (-card.rarity_id, -card.start_datetime.timestamp(), card.id))

        img = await self.create_card_image_grid_async(cards)

        buffer = BytesIO()
        img.save(buffer, 'png')
        buffer.seek(0)

        embed = discord.Embed(title='Pull Stats')
        embed.set_image(url='attachment://cards.png')

        await ctx.send(embed=embed, file=discord.File(fp=buffer, filename='cards.png'))

    async def do_gacha_draw_and_get_message_data(self,
                                                 user: Union[discord.User, discord.Member],
                                                 gacha: GachaMaster,
                                                 draw_data: GachaDrawMaster,
                                                 assets: AssetManager,
                                                 ) -> Tuple[discord.ui.View, discord.Embed, discord.File]:
        draw_result = await self.do_gacha_draw(user, gacha, draw_data, assets)
        img = await self.create_pull_image(draw_result.cards, draw_result.bonus, draw_result.sub_bonus)

        buffer = BytesIO()
        img.save(buffer, 'png')
        buffer.seek(0)

        embed = discord.Embed(title=gacha.name)
        thumb_url = self.bot.asset_url + get_asset_filename(gacha.banner_path)
        embed.set_thumbnail(url=thumb_url)
        embed.set_image(url='attachment://pull.png')
        embed.set_footer(text=str(gacha.id))

        desc = f'{user.mention}\n'
        if draw_result.pity_count is not None:
            desc += f'Pity: {draw_result.pity_count}/{gacha.bonus_max_value}\n'
        if draw_result.pity_count is not None and gacha.sub_bonus_max_value:
            desc += f'Sub-Pity: {draw_result.pity_count}/{gacha.sub_bonus_max_value}\n'
        if desc:
            embed.description = desc

        view = GachaPullView(self, GachaPullInvokeData(user, gacha, draw_data, assets))

        return view, embed, discord.File(fp=buffer, filename='pull.png')

    async def do_gacha_draw(self,
                            user: Union[discord.User, discord.Member],
                            gacha: GachaMaster,
                            draw_data: GachaDrawMaster,
                            assets: AssetManager) -> 'GachaPullResult':
        async with self.pull_locks[user.id], in_transaction() as conn:
            tables = gacha.tables
            tables_rates = [list(itertools.accumulate(t.rate for t in table)) for table in tables]

            state, _ = await GachaState.get_or_create(user_id=user.id, gacha_id=gacha.id, using_db=conn)
            state.total_roll_counter += 1

            cards = []
            for draw_amount, table_rate in zip(draw_data.draw_amounts, gacha.table_rates):
                rates = list(itertools.accumulate(table_rate.rates))
                for _i in range(draw_amount):
                    state.total_counter += 1
                    rng = random.randint(1, rates[-1])
                    table_index = next(i for i, s in enumerate(rates) if rng <= s)
                    table_rates = tables_rates[table_index]
                    rng = random.randint(1, table_rates[-1])
                    result_index = next(i for i, s in enumerate(table_rates) if rng <= s)
                    card = assets.card_master[tables[table_index][result_index].card_id]
                    await self.register_card_pulled(user.id, gacha.id, table_rate.id, card.id,
                                                    state.total_counter, state.total_roll_counter, conn)
                    cards.append(card)

            bonus = None
            sub_bonus = None
            current_pity = None

            if gacha.bonus_max_value:
                prev_pity = state.pity_counter
                state.pity_counter += 10
                current_pity = state.pity_counter
                if prev_pity < gacha.sub_bonus_max_value and current_pity >= gacha.sub_bonus_max_value:
                    state.total_counter += 1
                    sub_bonus_tables = gacha.sub_bonus_tables
                    rates = list(itertools.accumulate(gacha.sub_bonus_table_rate.rates))
                    rng = random.randint(1, rates[-1])
                    table_index = next(i for i, s in enumerate(rates) if rng <= s)
                    table_rates = list(itertools.accumulate(t.rate for t in sub_bonus_tables[table_index]))
                    rng = random.randint(1, table_rates[-1])
                    result_index = next(i for i, s in enumerate(table_rates) if rng <= s)
                    sub_bonus = assets.card_master[sub_bonus_tables[table_index][result_index].card_id]
                    await self.register_card_pulled(user.id, gacha.id, gacha.sub_bonus_table_rate.id, sub_bonus.id,
                                                    state.total_counter, state.total_roll_counter, conn)
                if current_pity >= gacha.bonus_max_value:
                    state.total_counter += 1
                    bonus_tables = gacha.bonus_tables
                    state.pity_counter -= gacha.bonus_max_value
                    current_pity = state.pity_counter
                    rates = list(itertools.accumulate(gacha.bonus_table_rate.rates))
                    rng = random.randint(1, rates[-1])
                    table_index = next(i for i, s in enumerate(rates) if rng <= s)
                    table_rates = list(itertools.accumulate(t.rate for t in bonus_tables[table_index]))
                    rng = random.randint(1, table_rates[-1])
                    result_index = next(i for i, s in enumerate(table_rates) if rng <= s)
                    bonus = assets.card_master[bonus_tables[table_index][result_index].card_id]
                    await self.register_card_pulled(user.id, gacha.id, gacha.bonus_table_rate.id, bonus.id,
                                                    state.total_counter, state.total_roll_counter, conn)

            await state.save(using_db=conn)

            return GachaPullResult(cards, bonus, sub_bonus, current_pity)

    async def register_card_pulled(self, user_id: int, gacha_id: int, table_rate_id: int, card_id: int,
                                   pulled_at: int, pulled_at_roll: int, using_db: BaseDBAsyncClient):
        entry, _created = await CollectionEntry.get_or_create(user_id=user_id,
                                                              gacha_id=gacha_id,
                                                              table_rate_id=table_rate_id,
                                                              card_id=card_id,
                                                              using_db=using_db)
        entry.counter = F('counter') + 1
        if entry.first_pulled <= 0:
            entry.first_pulled = pulled_at
            entry.first_pulled_roll = pulled_at_roll
        await entry.save()


class GachaPullResult(typing.NamedTuple):
    cards: List[CardMaster]
    bonus: Optional[CardMaster]
    sub_bonus: Optional[CardMaster]
    pity_count: Optional[int]


class GachaPullInvokeData(typing.NamedTuple):
    user: Union[discord.User, discord.Member]
    gacha: GachaMaster
    draw_data: GachaDrawMaster
    assets: AssetManager


class GachaPullAgainButton(discord.ui.Button['GachaPullView']):
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        invoke_data = self.view.data._replace(user=interaction.user)
        view, embed, file = await self.view.cog.do_gacha_draw_and_get_message_data(*invoke_data)
        await interaction.channel.send(view=view, embed=embed, file=file)


class GachaPullView(discord.ui.View):
    def __init__(self, cog: Gacha, data: GachaPullInvokeData, *args, **kwargs):
        self.cog = cog
        self.data = data
        super(GachaPullView, self).__init__(*args, **kwargs)
        self.add_item(GachaPullAgainButton(label='Pull Again', style=discord.ButtonStyle.success))


def setup(bot):
    bot.add_cog(Gacha(bot))
