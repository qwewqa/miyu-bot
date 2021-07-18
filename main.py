import datetime
import json
import logging
import sys
import traceback
from pathlib import Path

import discord
from discord.ext import commands
from discord.ext.commands import Cog
from tortoise.expressions import F

from miyu_bot.bot import models
from miyu_bot.bot.bot import MiyuBot
from miyu_bot.bot.models import CommandUsageCount
from miyu_bot.commands.common.argument_parsing import ArgumentError

logging.basicConfig(level=logging.INFO)

with open('config.json') as f:
    config = json.load(f)
    bot_token = config['token']


async def get_prefix(bot: MiyuBot, message: discord.Message):
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


bot = MiyuBot('assets', command_prefix=get_prefix, case_insensitive=True,
              activity=discord.Game(name='https://discord.gg/TThMwrAZTR'),
              owner_ids={169163991434788865},
              allowed_mentions=discord.AllowedMentions.none())

bot.config = config

scripts_path = Path('scripts.yaml').resolve()
if scripts_path.exists():
    bot.scripts_path = scripts_path

bot.load_extension('miyu_bot.commands.cogs.info')
bot.load_extension('miyu_bot.commands.cogs.card')
bot.load_extension('miyu_bot.commands.cogs.event')
bot.load_extension('miyu_bot.commands.cogs.music')
bot.load_extension('miyu_bot.commands.cogs.other')
bot.load_extension('miyu_bot.commands.cogs.preferences')
bot.load_extension('miyu_bot.commands.cogs.audio')
bot.load_extension('miyu_bot.commands.cogs.gacha')


@bot.event
async def on_ready():
    logging.getLogger(__name__).info(f'Current server count: {len(bot.guilds)}')


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


@bot.listen()
async def on_command(ctx: commands.Context):
    if not ctx.guild:
        return
    cnt, _ = await CommandUsageCount.get_or_create(guild_id=ctx.guild.id, name=ctx.command.name,
                                                   date=datetime.datetime.utcnow().date())
    cnt.counter = F('counter') + 1
    await cnt.save()


bot.run(bot_token)
