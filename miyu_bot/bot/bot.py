import datetime
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Optional, Union

import aiohttp
import pytz
from d4dj_utils.master.asset_manager import AssetManager
from discord.ext import commands
from discord.ext.commands import Context
from fluent.runtime import FluentResourceLoader
from pytz import BaseTzInfo
from pytz.tzinfo import StaticTzInfo, DstTzInfo
from tortoise import Tortoise

from miyu_bot.bot.common_aliases import CommonAliases
from miyu_bot.bot.tortoise_config import TORTOISE_ORM
from miyu_bot.commands.cogs.preferences import get_preferences
from miyu_bot.commands.common.asset_paths import clear_asset_filename_cache
from miyu_bot.commands.master_filter.master_filter_manager import MasterFilterManager


class D4DJBot(commands.Bot):
    assets: AssetManager
    master_filters: MasterFilterManager
    aliases: CommonAliases
    thread_pool: ThreadPoolExecutor

    asset_path: Path
    asset_url = 'https://qwewqa.github.io/d4dj-dumps/'

    config: dict
    scripts_path: Optional[Path]

    def __init__(self, asset_path, *args, **kwargs):
        self.asset_path = Path(asset_path)
        self.assets = AssetManager(self.asset_path, drop_extra_fields=True)
        self.fluent_loader = FluentResourceLoader("l10n/{locale}")
        self.aliases = CommonAliases(self.assets)
        self.master_filters = MasterFilterManager(self, self.assets)
        self.session = aiohttp.ClientSession()
        self.extension_names = set()
        self.thread_pool = ThreadPoolExecutor()
        self.scripts_path = None
        super().__init__(*args, **kwargs)

    def try_reload_assets(self):
        try:
            assets = AssetManager(self.asset_path, drop_extra_fields=True)
            aliases = CommonAliases(assets)
            master_filters = MasterFilterManager(self, assets)
        except:
            return False
        self.assets.db.close()
        self.assets = assets
        self.master_filters = master_filters
        self.aliases = aliases
        clear_asset_filename_cache()
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

    async def get_context(self, message, *, cls=None):
        ctx = await super().get_context(message, cls=PrefContext)
        if ctx.command and not getattr(ctx.command, 'no_preferences', False):
            ctx.preferences = SimpleNamespace(**(await get_preferences(ctx)))
        return ctx


class Preferences(SimpleNamespace):
    leaks: bool
    loop: Optional[int]
    prefix: str
    timezone: Union[BaseTzInfo, StaticTzInfo, DstTzInfo]


class PrefContext(Context):
    preferences: Optional[Preferences]

    def __init__(self, **kwargs):
        self.preferences = None
        super(PrefContext, self).__init__(**kwargs)

    def convert_tz(self, dt: datetime.datetime) -> datetime.datetime:
        if self.preferences:
            return dt.astimezone(self.preferences.timezone)
        else:
            return dt

    def localize(self, dt: datetime.datetime) -> datetime.datetime:
        if self.preferences:
            return self.preferences.timezone.localize(dt)
        else:
            return dt
