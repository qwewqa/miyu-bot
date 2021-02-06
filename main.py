import json
import logging

import discord
from d4dj_utils.master.asset_manager import AssetManager

from miyu_bot.bot.bot import D4DJBot
from miyu_bot.bot.master_asset_manager import MasterFilterManager

logging.basicConfig(level=logging.INFO)

with open('config.json') as f:
    bot_token = json.load(f)['token']

asset_manager = AssetManager('assets')
bot = D4DJBot(asset_manager, MasterFilterManager(asset_manager), command_prefix='?', case_insensitive=True,
              activity=discord.Game(name='https://discord.gg/TThMwrAZTR'))

bot.load_extension('miyu_bot.commands.cogs.card')
bot.load_extension('miyu_bot.commands.cogs.event')
bot.load_extension('miyu_bot.commands.cogs.music')
bot.load_extension('miyu_bot.commands.cogs.utility')


@bot.event
async def on_ready():
    logging.getLogger(__name__).info(f'Current server count: {len(bot.guilds)}')


bot.run(bot_token)
