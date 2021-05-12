import asyncio
import logging
import textwrap

import discord
import yaml
from discord.ext import commands
from tortoise.functions import Count, Sum

from miyu_bot.bot.bot import D4DJBot
from miyu_bot.bot.models import CommandUsageCount
from miyu_bot.commands.common.fuzzy_matching import romanize, FuzzyMatcher
from miyu_bot.commands.common.reaction_message import run_paged_message


class Utility(commands.Cog):
    bot: D4DJBot

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        bot.loop.create_task(self.run_scripts())

    async def run_scripts(self):
        if self.bot.scripts_path:
            with self.bot.scripts_path.open() as f:
                for k, v in yaml.safe_load(f.read()).items():
                    env = {
                        'bot': self.bot,
                        'assets': self.bot.assets,
                        'asset_filters': self.bot.master_filters,
                        'master_filters': self.bot.master_filters,
                        **globals(),
                    }
                    v = 'async def f():\n' + textwrap.indent(v, '  ')
                    l = locals()
                    exec(v, env, l)
                    f = l['f']

                    try:
                        await f()
                        self.logger.info(f'Script {k}: Successful')
                    except Exception as e:
                        self.logger.warning(f'Script {k}: ```{e.__class__.__name__}: {e}\n```')

    @commands.command(name='run_scripts',
                      aliases=['runscripts'],
                      hidden=True)
    @commands.is_owner()
    async def run_scripts_cmd(self, ctx: commands.Context):
        await self.run_scripts()

    @commands.command(aliases=['t'], hidden=True)
    async def translate(self, ctx: commands.Context, *, arg: str):
        async with self.bot.session.get('https://api-free.deepl.com/v2/translate',
                                        params={'auth_key': self.bot.config['deepl'],
                                                'text': arg,
                                                'target_lang': 'EN'}) as resp:
            embed = discord.Embed(title='Translate', description=(await resp.json())['translations'][0]['text'])
        await ctx.send(embed=embed)

    @commands.command(aliases=['tjp'], hidden=True)
    async def translate_jp(self, ctx: commands.Context, *, arg: str):
        async with self.bot.session.get('https://api-free.deepl.com/v2/translate',
                                        params={'auth_key': self.bot.config['deepl'],
                                                'text': arg,
                                                'target_lang': 'JA'}) as resp:
            embed = discord.Embed(title='Translate JP', description=(await resp.json())['translations'][0]['text'])
        await ctx.send(embed=embed)

    @commands.command(aliases=['tt'], hidden=True)
    async def transtranslate(self, ctx: commands.Context, *, arg: str):
        async with self.bot.session.get('https://api-free.deepl.com/v2/translate',
                                        params={'auth_key': self.bot.config['deepl'],
                                                'text': arg,
                                                'target_lang': 'JA'}) as resp:
            arg = (await resp.json())['translations'][0]['text']
        async with self.bot.session.get('https://api-free.deepl.com/v2/translate',
                                        params={'auth_key': self.bot.config['deepl'],
                                                'text': arg,
                                                'target_lang': 'EN'}) as resp:
            embed = discord.Embed(title='Transtranslate', description=(await resp.json())['translations'][0]['text'])
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
        embed.add_field(name='Donate', value='https://ko-fi.com/qwewqa', inline=False)
        embed.add_field(name='Server', value='https://discord.gg/TThMwrAZTR', inline=False)
        embed.add_field(name='Bot Invite',
                        value='https://discord.com/api/oauth2/authorize?client_id=789314370999287808&permissions=388160&scope=bot',
                        inline=False)
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
                .order_by('name')
                .group_by('name')
                .values_list('name', 'use_count')
        )
        embed = discord.Embed(title='Command Usage')
        asyncio.create_task(run_paged_message(ctx, embed,
                                              [f'{name}: {count}' for name, count in usage_counts] +
                                              [f'total: {sum(c for _, c in usage_counts)}'],
                                              page_size=40))

    @commands.command(name='guild_usage',
                      aliases=['guildusage'],
                      hidden=True)
    @commands.is_owner()
    async def guild_usage(self, ctx: commands.Context):
        usage_counts = (
            await CommandUsageCount
                .all()
                .annotate(use_count=Sum('counter'))
                .order_by('guild_id')
                .group_by('guild_id')
                .values_list('guild_id', 'use_count')
        )
        embed = discord.Embed(title='Guild Usage')
        asyncio.create_task(run_paged_message(ctx, embed,
                                              [f'{self.bot.get_guild(gid)}: {count}' for gid, count in usage_counts] +
                                              [f'total: {sum(c for _, c in usage_counts)}'],
                                              page_size=40))


def setup(bot):
    bot.add_cog(Utility(bot))
