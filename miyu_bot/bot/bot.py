from d4dj_utils.master.asset_manager import AssetManager
from discord.ext import commands
from tortoise import Tortoise

from miyu_bot.bot.master_asset_manager import MasterFilterManager
from miyu_bot.bot.models import TORTOISE_ORM
from miyu_bot.bot.name_aliases import NameAliases


class D4DJBot(commands.Bot):
    assets: AssetManager
    asset_filters: MasterFilterManager
    aliases: NameAliases

    asset_url = 'https://qwewqa.github.io/d4dj-dumps/'

    def __init__(self, assets, asset_filters, *args, **kwargs):
        self.assets = assets
        self.asset_filters = asset_filters
        self.aliases = NameAliases(assets)
        super().__init__(*args, **kwargs)

    async def login(self, token, *, bot=True):
        await Tortoise.init(TORTOISE_ORM)
        await super(D4DJBot, self).login(token, bot=bot)

    async def close(self):
        await Tortoise.close_connections()
        await super(D4DJBot, self).close()
