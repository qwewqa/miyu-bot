import json
import logging

import discord
from d4dj_utils.master.asset_manager import AssetManager
from discord.ext import commands
from tortoise import Tortoise

from miyu_bot.bot import models
from miyu_bot.bot.bot import D4DJBot
from miyu_bot.bot.master_asset_manager import MasterFilterManager
from miyu_bot.commands.common.argument_parsing import ArgumentError

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
bot.load_extension('miyu_bot.commands.cogs.preferences')


@bot.event
async def on_ready():
    logging.getLogger(__name__).info(f'Current server count: {len(bot.guilds)}')
    for guild in bot.guilds:
        await models.Guild.update_or_create(id=guild.id, name=guild.name)


@bot.listen()
async def on_guild_join(guild):
    await models.Guild.update_or_create(id=guild.id, name=guild.name)


@bot.listen()
async def on_guild_remove(guild):
    await (await models.Guild.get(id=guild.id)).delete()


@bot.listen()
async def on_guild_update(guild):
    await models.Guild.update_or_create(id=guild.id, name=guild.name)


@bot.listen()
async def on_command_error(ctx: commands.Context, error):
    error = getattr(error, 'original', error)
    if isinstance(error, ArgumentError):
        await ctx.send(str(error))


bot.run(bot_token)
