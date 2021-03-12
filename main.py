import json
import logging
import sys
import traceback

import discord
from discord.ext import commands
from discord.ext.commands import Cog

from miyu_bot.bot import models
from miyu_bot.bot.bot import D4DJBot
from miyu_bot.commands.common.argument_parsing import ArgumentError

logging.basicConfig(level=logging.INFO)

with open('config.json') as f:
    bot_token = json.load(f)['token']


async def get_prefix(bot: D4DJBot, message: discord.Message):
    if message.guild:
        guild = await models.Guild.get_or_none(id=message.guild.id)
        guild_prefix = (guild.prefix or '!') if guild else '!'
    else:
        guild_prefix = '!'
    author = await models.User.get_or_none(id=message.author.id)
    author_prefix = author.prefix if author else None
    if author_prefix or guild_prefix:
        return (prefix for prefix in ['!miyu ', author_prefix, guild_prefix] if prefix)
    else:
        return '!miyu ', '!'


bot = D4DJBot('assets', command_prefix=get_prefix, case_insensitive=True,
              activity=discord.Game(name='https://discord.gg/TThMwrAZTR'))

bot.load_extension('miyu_bot.commands.cogs.card')
bot.load_extension('miyu_bot.commands.cogs.event')
bot.load_extension('miyu_bot.commands.cogs.music')
bot.load_extension('miyu_bot.commands.cogs.utility')
bot.load_extension('miyu_bot.commands.cogs.preferences')
bot.load_extension('miyu_bot.commands.cogs.audio')


@bot.event
async def on_ready():
    logging.getLogger(__name__).info(f'Current server count: {len(bot.guilds)}')
    for guild in bot.guilds:
        await models.Guild.update_or_create(id=guild.id, defaults={'name': guild.name})


@bot.listen()
async def on_guild_join(guild):
    await models.Guild.update_or_create(id=guild.id, defaults={'name': guild.name})


@bot.listen()
async def on_guild_remove(guild):
    await (await models.Guild.get(id=guild.id)).delete()


@bot.listen()
async def on_guild_update(_before, after):
    await models.Guild.update_or_create(id=after.id, defaults={'name': after.name})


@bot.listen()
async def on_command_error(context: commands.Context, exception):
    error = getattr(exception, 'original', exception)
    if isinstance(error, ArgumentError):
        await context.send(str(error))
        return

    if hasattr(context.command, 'on_error'):
        return

    cog = context.cog
    if cog:
        if Cog._get_overridden_method(cog.cog_command_error) is not None:
            return

    print('Ignoring exception in command {}:'.format(context.command), file=sys.stderr)
    traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)


bot.run(bot_token)
