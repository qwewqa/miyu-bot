from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path

import aiohttp
from d4dj_utils.master.asset_manager import AssetManager
from discord.ext import commands
from tortoise import Tortoise

from miyu_bot.bot.master_asset_manager import MasterFilterManager
from miyu_bot.bot.name_aliases import NameAliases
from miyu_bot.bot.tortoise_config import TORTOISE_ORM


class D4DJBot(commands.Bot):
    assets: AssetManager
    asset_filters: MasterFilterManager
    aliases: NameAliases
    thread_pool: ThreadPoolExecutor

    asset_path: Path
    asset_url = 'https://qwewqa.github.io/d4dj-dumps/'

    def __init__(self, asset_path, *args, **kwargs):
        self.asset_path = Path(asset_path)
        self.assets = AssetManager(self.asset_path, drop_extra_fields=True)
        self.asset_filters = MasterFilterManager(self.assets)
        self.aliases = NameAliases(self.assets)
        self.session = aiohttp.ClientSession()
        self.extension_names = set()
        self.thread_pool = ThreadPoolExecutor()
        super().__init__(*args, **kwargs)

    def try_reload_assets(self):
        try:
            assets = AssetManager(self.asset_path, drop_extra_fields=True)
            asset_filters = MasterFilterManager(assets)
            aliases = NameAliases(assets)
        except:
            return False
        self.assets = assets
        self.asset_filters = asset_filters
        self.aliases = aliases
        return True

    async def login(self, token, *, bot=True):
        await Tortoise.init(TORTOISE_ORM)
        await super(D4DJBot, self).login(token, bot=bot)

    async def close(self):
        await self.session.close()
        await Tortoise.close_connections()
        await super(D4DJBot, self).close()

    def load_extension(self, name):
        self.extension_names.add(name)
        super(D4DJBot, self).load_extension(name)

    def unload_extension(self, name):
        self.extension_names.remove(name)
        super(D4DJBot, self).unload_extension(name)

    def reload_all_extensions(self):
        for name in self.extension_names:
            self.reload_extension(name)
