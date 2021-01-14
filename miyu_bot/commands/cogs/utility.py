import logging

from discord.ext import commands

from miyu_bot.commands.common.fuzzy_matching import romanize, FuzzyMatcher


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def romanize(self, ctx: commands.Context, *, arg: str):
        await ctx.send(romanize(arg))

    @commands.command(hidden=True, ignore_extra=False)
    @commands.is_owner()
    async def similarity_score(self, ctx: commands.Context, source: str, target: str):
        await ctx.send(str(FuzzyMatcher().score(romanize(source), romanize(target))))


def setup(bot):
    bot.add_cog(Utility(bot))
