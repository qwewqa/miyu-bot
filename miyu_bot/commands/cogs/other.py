import asyncio
import logging
import textwrap

import discord
import yaml
from discord import app_commands, Interaction
from discord.ext import commands
from tortoise.functions import Count, Sum

from miyu_bot.bot.bot import MiyuBot
from miyu_bot.bot.models import CommandUsageCount, GeneralUsageCount
from miyu_bot.commands.common.fuzzy_matching import romanize, FuzzyMatcher
from miyu_bot.commands.common.paged_message import run_paged_message
from miyu_bot.commands.master_filter.localization_manager import LocalizationManager


class Other(commands.Cog):
    bot: MiyuBot

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        bot.setup_tasks.append(self.run_scripts())
        self.l10n = LocalizationManager(self.bot.fluent_loader, "utility.ftl")

    async def run_scripts(self):
        if self.bot.scripts_path:
            with self.bot.scripts_path.open() as f:
                for k, v in yaml.safe_load(f.read()).items():
                    env = {
                        "bot": self.bot,
                        "assets": self.bot.assets,
                        "asset_filters": self.bot.master_filters,
                        "master_filters": self.bot.master_filters,
                        **globals(),
                    }
                    v = "async def f():\n" + textwrap.indent(v, "  ")
                    l = locals()
                    exec(v, env, l)
                    f = l["f"]

                    try:
                        await f()
                        self.logger.info(f"Script {k}: Successful")
                    except Exception as e:
                        self.logger.warning(
                            f"Script {k}: ```{e.__class__.__name__}: {e}\n```"
                        )

    @commands.command(name="run_scripts", aliases=["runscripts"], hidden=True)
    @commands.is_owner()
    async def run_scripts_cmd(self, ctx: commands.Context):
        await self.run_scripts()

    async def get_translation(self, text, language):
        async with self.bot.session.get(
            "https://api-free.deepl.com/v2/translate",
            params={
                "auth_key": self.bot.config["deepl"],
                "text": text,
                "target_lang": language,
            },
        ) as resp:
            return (await resp.json())["translations"][0]["text"]

    @commands.command(aliases=["t"], hidden=True)
    async def translate(self, ctx: commands.Context, *, arg: str):
        embed = discord.Embed(
            title="Translate", description=await self.get_translation(arg, "EN")
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["tjp"], hidden=True)
    async def translate_jp(self, ctx: commands.Context, *, arg: str):
        embed = discord.Embed(
            title="Translate", description=await self.get_translation(arg, "JA")
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["tzh"], hidden=True)
    async def translate_zh(self, ctx: commands.Context, *, arg: str):
        embed = discord.Embed(
            title="Translate", description=await self.get_translation(arg, "ZH")
        )
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def romanize(self, ctx: commands.Context, *, arg: str):
        await ctx.send(romanize(arg))

    @commands.command(hidden=True, ignore_extra=False)
    @commands.is_owner()
    async def similarity_score(self, ctx: commands.Context, source: str, target: str):
        await ctx.send(str(FuzzyMatcher().score(romanize(source), romanize(target))))

    async def is_owner(interaction: Interaction):
        return await interaction.client.is_owner(interaction.user)

    @app_commands.command()
    @app_commands.guilds(790033228600705044, 821445433276629053)
    @app_commands.check(is_owner)
    async def shutdown(self, interaction: Interaction):
        await interaction.response.send_message("Shutting down.")
        await self.bot.close()

    @app_commands.command()
    @app_commands.guilds(790033228600705044, 821445433276629053)
    @app_commands.check(is_owner)
    async def echo(self, interaction: Interaction, *, message: str):
        await interaction.response.defer()
        await interaction.channel.send(message)

    @commands.command(hidden=True, aliases=["rld"])
    @commands.is_owner()
    async def reload_extension(self, ctx: commands.Context, *, name: str = ""):
        try:
            if name:
                await self.bot.reload_extension(name)
                await ctx.send("Successfully reloaded extension.")
            else:
                await self.bot.reload_all_extensions()
                await ctx.send("Successfully reloaded all extensions.")
        except:
            await ctx.send("Failed to reload extension.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload_assets(self, ctx: commands.Context):
        if self.bot.try_reload_assets():
            await ctx.send("Assets Reloaded.")
        else:
            await ctx.send("Failed to reload assets.")

    @commands.command(name="eval", hidden=True)
    @commands.is_owner()
    async def eval_cmd(self, ctx: commands.Context, *, body: str):
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "assets": self.bot.assets,
            "asset_filters": self.bot.master_filters,
            "master_filters": self.bot.master_filters,
            **globals(),
        }

        if body and body[0] == "`" and body[-1] == "`":
            body = body[1:-1]

        try:
            value = eval(body, env)
            if value:
                await ctx.send(str(value))
            else:
                await ctx.send("Done")
        except Exception as e:
            await ctx.send(f"```{e.__class__.__name__}: {e}\n```")

    @commands.command(name="exec", hidden=True)
    @commands.is_owner()
    async def exec_cmd(self, ctx: commands.Context, *, body: str):
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "assets": self.bot.assets,
            "asset_filters": self.bot.master_filters,
            "master_filters": self.bot.master_filters,
            **globals(),
        }

        if body and body[:9] == "```python" and body[-3:] == "```":
            body = body[9:-3]
        if body and body[:3] == "```" and body[-3:] == "```":
            body = body[3:-3]
        if body and body[:1] == "`" and body[-1:] == "`":
            body = body[1:-1]

        body = "async def f():\n" + textwrap.indent(body, "  ")
        l = locals()
        exec(body, env, l)
        f = l["f"]

        try:
            value = await f()
            if value:
                await ctx.send(str(value))
            else:
                await ctx.author.send("Done")
        except Exception as e:
            await ctx.send(f"```{e.__class__.__name__}: {e}\n```")

    @commands.hybrid_command(
        name="info",
        aliases=["about", "invite"],
        description="Sends bot info.",
        help="!info",
    )
    async def info(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Miyu Bot", description="A utility bot for mobile rhythm game D4DJ."
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.add_field(name="Developer", value="qwewqa#3948", inline=False)
        embed.add_field(name="Donate", value="https://ko-fi.com/qwewqa", inline=False)
        embed.add_field(
            name="Documentation", value="https://miyu-docs.qwewqa.xyz/", inline=False
        )
        embed.add_field(
            name="Server", value="https://discord.gg/TThMwrAZTR", inline=False
        )
        embed.add_field(
            name="Bot Invite",
            value="https://discord.com/api/oauth2/authorize?client_id=789314370999287808&permissions=379968&scope=bot+applications.commands",
            inline=False,
        )
        embed.add_field(
            name="Acknowledgements",
            value="Farley#8054 (Mechanics Testing)\n"
            "sigonasr2#6262 (Leaderboard Data)\n"
            "AcerYue#3826 (TW Translation)\n"
            "かえる#1919 (JP Translation)\n"
            "HamP#4125 (JP Translation)\n"
            "うさみょん(myon2019)/mtripg6666tdr#4470 (JP Translation)",
            inline=False,
        )
        embed.add_field(
            name="Supporters",
            value="Hifumi-chan#0123\n"
            "marshmallowpan#1781\n"
            "oh_that_will#8488\n"
            "rainyfran#7450\n"
            "lizardhospital#9358\n"
            "winkip#0271\n"
            "Sora#2222\n"
            "Mirby#5516\n"
            "KomanoInu#7107",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(name="command_usage", aliases=["commandusage"], hidden=True)
    @commands.is_owner()
    async def command_usage(self, ctx: commands.Context):
        usage_counts = (
            await CommandUsageCount.all()
            .annotate(use_count=Sum("counter"))
            .order_by("name")
            .group_by("name")
            .values_list("name", "use_count")
        )
        embed = discord.Embed(title="Command Usage")
        asyncio.create_task(
            run_paged_message(
                ctx,
                embed,
                [f"{name}: {count}" for name, count in usage_counts]
                + [f"total: {sum(c for _, c in usage_counts)}"],
                page_size=40,
            )
        )

    @commands.command(name="getstat", hidden=True)
    @commands.is_owner()
    async def getstat(self, ctx: commands.Context, name: str):
        usage = (
            await GeneralUsageCount.filter(name=name)
            .annotate(total_count=Sum("counter"))
            .values("total_count")
        )[0]
        await ctx.send(f'{usage["total_count"]}')

    @commands.command(name="guild_usage", aliases=["guildusage"], hidden=True)
    @commands.is_owner()
    async def guild_usage(self, ctx: commands.Context):
        usage_counts = (
            await CommandUsageCount.all()
            .annotate(use_count=Sum("counter"))
            .order_by("guild_id")
            .group_by("guild_id")
            .values_list("guild_id", "use_count")
        )
        embed = discord.Embed(title="Guild Usage")
        asyncio.create_task(
            run_paged_message(
                ctx,
                embed,
                [f"{self.bot.get_guild(gid)}: {count}" for gid, count in usage_counts]
                + [f"total: {sum(c for _, c in usage_counts)}"],
                page_size=40,
            )
        )


async def setup(bot):
    await bot.add_cog(Other(bot))
