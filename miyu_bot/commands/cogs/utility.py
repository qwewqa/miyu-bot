import logging
import textwrap

from discord.ext import commands
from tortoise import Tortoise

from miyu_bot.bot.bot import D4DJBot
from miyu_bot.commands.common.fuzzy_matching import romanize, FuzzyMatcher


class Utility(commands.Cog):
    bot: D4DJBot

    def __init__(self, bot):
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

    @commands.command(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx: commands.Context):
        await ctx.send('Shutting down.')
        await self.bot.logout()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload_extension(self, ctx: commands.Context, *, name: str = ''):
        try:
            if name:
                self.bot.reload_extension(name)
                await ctx.send('Successfully reloaded extension.')
            else:
                self.bot.reload_all_extensions()
                await ctx.send('Successfully reloaded all extensions.')
        except:
            await ctx.send('Failed to reload extension.')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload_assets(self, ctx: commands.Context):
        if self.bot.try_reload_assets():
            await ctx.send('Assets Reloaded.')
        else:
            await ctx.send('Failed to reload assets.')

    @commands.command(name='eval', hidden=True)
    @commands.is_owner()
    async def eval_cmd(self, ctx: commands.Context, *, body: str):
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'assets': self.bot.assets,
            'asset_filters': self.bot.asset_filters,
            **globals(),
        }

        if body and body[0] == '`' and body[-1] == '`':
            body = body[1:-1]

        try:
            value = eval(body, env)
            if value:
                await ctx.send(str(value))
            else:
                await ctx.send('Done')
        except Exception as e:
            await ctx.send(f'```{e.__class__.__name__}: {e}\n```')

    @commands.command(name='exec', hidden=True)
    @commands.is_owner()
    async def exec_cmd(self, ctx: commands.Context, *, body: str):
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'assets': self.bot.assets,
            'asset_filters': self.bot.asset_filters,
            **globals(),
        }

        if body and body[:9] == '```python' and body[-3:] == '```':
            body = body[9:-3]
        if body and body[:3] == '```' and body[-3:] == '```':
            body = body[3:-3]
        if body and body[:1] == '`' and body[-1:] == '`':
            body = body[1:-1]

        body = 'async def f():\n' + textwrap.indent(body, '  ')
        l = locals()
        exec(body, env, l)
        f = l['f']

        try:
            value = await f()
            if value:
                await ctx.send(str(value))
            else:
                await ctx.author.send('Done')
        except Exception as e:
            await ctx.send(f'```{e.__class__.__name__}: {e}\n```')

    @commands.command(name='invite',
                      aliases=[],
                      description='Sends the bot invite.',
                      help='!invite')
    async def invite(self, ctx: commands.Context):
        await ctx.send(
            'https://discord.com/api/oauth2/authorize?client_id=789314370999287808&permissions=388160&scope=bot')


def setup(bot):
    bot.add_cog(Utility(bot))
