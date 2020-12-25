import json
import logging

import discord
from d4dj_utils.manager.asset_manager import AssetManager
from discord.ext import commands

logging.basicConfig(level=logging.INFO)

with open('config.json') as f:
    bot_token = json.load(f)['token']

bot = commands.Bot(command_prefix='!', case_insensitive=True)

asset_manager = AssetManager('assets')

bot.load_extension('miyu_bot.commands.cogs.card')
bot.load_extension('miyu_bot.commands.cogs.event')
bot.load_extension('miyu_bot.commands.cogs.music')
bot.load_extension('miyu_bot.commands.cogs.utility')


@bot.event
async def on_ready():
    logging.getLogger(__name__).info(f'Current server count: {len(bot.guilds)}')
    await bot.change_presence(activity=discord.Game(name='test'))


bot.run(bot_token)
