from d4dj_utils.manager.asset_manager import AssetManager
from discord.ext import commands

from miyu_bot.bot.master_asset_manager import MasterFilterManager
from miyu_bot.bot.name_aliases import NameAliases


class D4DJBot(commands.Bot):
    assets: AssetManager
    asset_filters: MasterFilterManager
    aliases: NameAliases

    def __init__(self, assets, asset_filters, *args, **kwargs):
        self.assets = assets
        self.asset_filters = asset_filters
        self.aliases = NameAliases(assets)
        super().__init__(*args, **kwargs)
