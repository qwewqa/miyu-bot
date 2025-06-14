import asyncio
import datetime
import json
import logging
import sys
import traceback
from pathlib import Path

import discord
from discord import Intents
from discord.ext import commands
from discord.ext.commands import Cog, when_mentioned
from tortoise.expressions import F

from miyu_bot.bot import models
from miyu_bot.bot.bot import MiyuBot
from miyu_bot.bot.models import CommandUsageCount
from miyu_bot.commands.common.argument_parsing import ArgumentError

logging.basicConfig(level=logging.INFO)

with open("config.json") as f:
    config = json.load(f)
    bot_token = config["token"]


async def main():
    intents = Intents.default()
    bot = MiyuBot(
        "assets",
        command_prefix=when_mentioned,
        case_insensitive=True,
        activity=discord.Game(name="https://miyu-docs.qwewqa.xyz/"),
        owner_ids={169163991434788865,433089131158175765},
        allowed_mentions=discord.AllowedMentions.none(),
        intents=intents,
    )

    bot.config = config

    scripts_path = Path("scripts.yaml").resolve()
    if scripts_path.exists():
        bot.scripts_path = scripts_path

    await bot.load_extension("miyu_bot.commands.cogs.info")
    await bot.load_extension("miyu_bot.commands.cogs.card")
    await bot.load_extension("miyu_bot.commands.cogs.event")
    await bot.load_extension("miyu_bot.commands.cogs.music")
    await bot.load_extension("miyu_bot.commands.cogs.other")
    await bot.load_extension("miyu_bot.commands.cogs.preferences")
    await bot.load_extension("miyu_bot.commands.cogs.audio")
    await bot.load_extension("miyu_bot.commands.cogs.gacha")

    @bot.event
    async def on_ready():
        logging.getLogger(__name__).info(f"Current server count: {len(bot.guilds)}")

    @bot.listen()
    async def on_command_error(context: commands.Context, exception):
        error = getattr(exception, "original", exception)
        if isinstance(error, ArgumentError):
            await context.send(str(error))
            return

        if hasattr(context.command, "on_error"):
            return

        cog = context.cog
        if cog:
            if Cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        print(
            "Ignoring exception in command {}:".format(context.command), file=sys.stderr
        )
        traceback.print_exception(
            type(exception), exception, exception.__traceback__, file=sys.stderr
        )

    async def on_start():
        if config.get("sync"):
            await bot.tree.sync()
            for gid in [790033228600705044, 821445433276629053]:
                try:
                    await bot.tree.sync(guild=await bot.fetch_guild(gid))
                except discord.errors.NotFound:
                    pass

    bot.setup_tasks.append(on_start())

    @bot.listen()
    async def on_command(ctx: commands.Context):
        if not ctx.guild:
            return
        cnt, _ = await CommandUsageCount.get_or_create(
            guild_id=ctx.guild.id,
            name=ctx.command.qualified_name,
            date=datetime.datetime.utcnow().date(),
        )
        cnt.counter = F("counter") + 1
        await cnt.save()

    async with bot:
        await bot.start(bot_token)


asyncio.run(main())
