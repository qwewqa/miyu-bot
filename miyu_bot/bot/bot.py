import datetime
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Optional, Union, Dict

import aiohttp
import discord.ext.commands
import pytz
from d4dj_utils.master.asset_manager import AssetManager
from discord.ext import commands
from discord.ext.commands import Context
from fluent.runtime import FluentResourceLoader
from pytz import BaseTzInfo
from pytz.tzinfo import StaticTzInfo, DstTzInfo
from tortoise import Tortoise

from miyu_bot.bot.chart_scorer import ChartScorer
from miyu_bot.bot.common_aliases import CommonAliases
from miyu_bot.bot.servers import Server
from miyu_bot.bot.tortoise_config import TORTOISE_ORM
from miyu_bot.commands.cogs.preferences import get_preferences
from miyu_bot.commands.common.asset_paths import clear_asset_filename_cache
from miyu_bot.commands.master_filter.master_filter_manager import MasterFilterManager


class MiyuBot(commands.Bot):
    assets: Dict[Server, AssetManager]
    master_filters: MasterFilterManager
    aliases: CommonAliases
    thread_pool: ThreadPoolExecutor

    asset_path: Path
    asset_url = 'https://miyu-data.qwewqa.xyz/'

    config: dict
    scripts_path: Optional[Path]

    def __init__(self, asset_path, gen_doc: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_tasks = []
        self.gen_doc = gen_doc
        self.asset_path = Path(asset_path)
        self.assets = {
            Server.JP: AssetManager(self.asset_path / 'jp',
                                    timezone=pytz.timezone('Asia/Tokyo'),
                                    drop_extra_fields=True),
            Server.EN: AssetManager(self.asset_path / 'en',
                                    timezone=pytz.timezone('UTC'),
                                    drop_extra_fields=True),
        }
        self.fluent_loader = FluentResourceLoader('l10n/{locale}')
        self.aliases = CommonAliases(self.assets)
        self.master_filters = MasterFilterManager(self)
        self.session = aiohttp.ClientSession()
        self.extension_names = set()
        self.thread_pool = ThreadPoolExecutor()
        self.scripts_path = None
        self.chart_scorer = ChartScorer({**self.assets[Server.EN].chart_master, **self.assets[Server.JP].chart_master})
        self.help_command = MiyuHelp()

    async def setup_hook(self) -> None:
        for task in self.setup_tasks:
            await task

    def try_reload_assets(self):
        try:
            assets = {
                Server.JP: AssetManager(self.asset_path / 'assets_jp',
                                        timezone=pytz.timezone('Asia/Tokyo'),
                                        drop_extra_fields=True),
                Server.EN: AssetManager(self.asset_path / 'assets_en',
                                        timezone=pytz.timezone('UTC'),
                                        drop_extra_fields=True),
            }
            aliases = CommonAliases(assets)
            master_filters = MasterFilterManager(self)
        except:
            return False
        for a in self.assets.values():
            a.db.close()
        self.assets = assets
        self.master_filters = master_filters
        self.aliases = aliases
        clear_asset_filename_cache()
        return True

    async def login(self, token):
        await Tortoise.init(TORTOISE_ORM)
        await super(MiyuBot, self).login(token)

    async def close(self):
        await self.session.close()
        await Tortoise.close_connections()
        await super(MiyuBot, self).close()

    async def load_extension(self, name):
        self.extension_names.add(name)
        await super(MiyuBot, self).load_extension(name)

    async def unload_extension(self, name):
        self.extension_names.remove(name)
        await super(MiyuBot, self).unload_extension(name)

    async def reload_all_extensions(self):
        for name in self.extension_names:
            await self.reload_extension(name)

    async def get_context(self, message, *, cls=None):
        ctx = await super().get_context(message, cls=PrefContext)
        if ctx.command and not getattr(ctx.command, 'no_preferences', False):
            ctx.preferences = SimpleNamespace(**(await get_preferences(ctx)))
            ctx.assets = self.assets[ctx.preferences.server]
        else:
            ctx.preferences = None
            ctx.assets = None
        return ctx


class MiyuHelp(commands.DefaultHelpCommand):
    help_url = 'https://miyu-docs.qwewqa.xyz/'
    context: 'PrefContext'

    async def send_bot_help(self, mapping):
        channel = self.get_destination()
        language = {
            'en-US': '',
            'zh-TW': 'zh_TW/',
            'ja': 'ja/',
        }[self.context.preferences.language]
        url = f'{self.help_url}{language}'
        await channel.send(url)

    async def send_command_help(self, command: discord.ext.commands.Command):
        channel = self.get_destination()
        language = {
            'en-US': '',
            'zh-TW': 'zh_TW/',
            'ja': 'ja/',
        }[self.context.preferences.language]
        if command.hidden:
            return
        if command.cog_name == 'Info' and hasattr(command, 'master_filter'):
            master_filter = command.master_filter
            filter_name = master_filter.name.replace('_filter', '')
            url = f'{self.help_url}{language}commands/info/{filter_name}/#{command.name}'.replace(' ', '-')
            await channel.send(url)
        else:
            cog_name = command.cog.qualified_name.lower()
            url = f'{self.help_url}{language}commands/utility/{cog_name}/#{command.qualified_name}'.replace(' ', '-')
            await channel.send(url)

    async def send_group_help(self, group):
        await self.send_command_help(group)

    async def send_cog_help(self, cog):
        channel = self.get_destination()
        language = {
            'en-US': '',
            'zh-TW': 'zh_TW/',
            'ja': 'ja/',
        }[self.context.preferences.language]
        if cog.qualified_name == 'Info':
            url = f'{self.help_url}{language}commands/general-usage/'
            await channel.send(url)
        else:
            url = f'{self.help_url}{language}commands/utility/{cog.qualified_name.lower()}/'.replace(' ', '-')
            await channel.send(url)


class Preferences(SimpleNamespace):
    leaks: bool
    loop: Optional[int]
    prefix: str
    timezone: Union[BaseTzInfo, StaticTzInfo, DstTzInfo]
    language: str
    server: Server


class PrefContext(Context):
    preferences: Optional[Preferences]
    assets: Optional[AssetManager]

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
