import logging
import textwrap

import discord
from discord.ext import commands
from tortoise.functions import Count, Sum

from miyu_bot.bot.bot import D4DJBot
from miyu_bot.bot.models import CommandUsageCount
from miyu_bot.commands.common.fuzzy_matching import romanize, FuzzyMatcher


class Utility(commands.Cog):
    bot: D4DJBot

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(aliases=['t'], hidden=True)
    async def translate(self, ctx: commands.Context, *, arg: str):
        async with self.bot.session.get('https://api-free.deepl.com/v2/translate',
                                        params={'auth_key': self.bot.config['deepl'],
                                                'text': arg,
                                                'target_lang': 'EN'}) as resp:
            embed = discord.Embed(title='Translate', description=(await resp.json())['translations'][0]['text'])
        await ctx.send(embed=embed)

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
            'asset_filters': self.bot.master_filters,
            'master_filters': self.bot.master_filters,
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
            'asset_filters': self.bot.master_filters,
            'master_filters': self.bot.master_filters,
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

    @commands.command(name='info',
                      aliases=['about', 'invite'],
                      description='Sends bot info.',
                      help='!info')
    async def info(self, ctx: commands.Context):
        embed = discord.Embed(title='Miyu Bot', description='A utility bot for mobile rhythm game D4DJ.')
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.add_field(name='Developer', value='qwewqa#3948', inline=False)
        embed.add_field(name='Server', value='https://discord.gg/TThMwrAZTR', inline=False)
        embed.add_field(name='Bot Invite', value='https://discord.com/api/oauth2/authorize?client_id=789314370999287808&permissions=388160&scope=bot', inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='command_usage',
                      aliases=['commandusage'],
                      hidden=True)
    @commands.is_owner()
    async def command_usage(self, ctx: commands.Context):
        usage_counts = (
            await CommandUsageCount
            .all()
            .annotate(use_count=Sum('counter'))
            .group_by('name')
            .values_list('name', 'use_count')
        )
        await ctx.send('\n'.join(f'{name}: {count}' for name, count in usage_counts)
                       + f'\ntotal: {sum(c for _, c in usage_counts)}')

    @commands.command(name='guild_usage',
                      aliases=['guildusage'],
                      hidden=True)
    @commands.is_owner()
    async def guild_usage(self, ctx: commands.Context):
        usage_counts = (
            await CommandUsageCount
            .all()
            .annotate(use_count=Sum('counter'))
            .group_by('guild_id')
            .values_list('guild_id', 'use_count')
        )
        await ctx.send('\n'.join(f'{self.bot.get_guild(gid) or "Unknown"}: {count}' for gid, count in usage_counts)
                       + f'\ntotal: {sum(c for _, c in usage_counts)}')


def setup(bot):
    bot.add_cog(Utility(bot))
