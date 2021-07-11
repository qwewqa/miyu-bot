import logging

import discord
from discord.ext import commands

from miyu_bot.bot.bot import MiyuBot
from miyu_bot.bot.servers import Server
from miyu_bot.commands.common.emoji import rarity_emoji_ids
from miyu_bot.commands.master_filter.localization_manager import LocalizationManager


class Card(commands.Cog):
    bot: MiyuBot

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.l10n = LocalizationManager(self.bot.fluent_loader, 'card.ftl')

    @commands.command(name='cardexp',
                      aliases=['card_exp', 'cdexp'],
                      description='Displays card exp totals or the difference between levels.',
                      help='!cardexp 1-80')
    async def cardexp(self, ctx: commands.Context, *, arg: commands.clean_content = ''):
        assert isinstance(arg, str)
        exp = self.bot.assets[Server.JP].card_exp_master

        def comma_number(n):
            return '{:,}'.format(n)

        def format_exp(e):
            return comma_number(e.total_exp).rjust(9)

        if not arg:
            embed = discord.Embed(title='Card Exp',
                                  description='```' +
                                              '\n'.join(f'Lvl {n}: {format_exp(exp[n])}' for n in range(10, 90, 10)) +
                                              '```')
            await ctx.send(embed=embed)
        else:
            try:
                if arg.isnumeric():
                    level = int(arg)
                    level_total = exp[level].total_exp
                    desc = (f'```\n'
                            f'Total:  {comma_number(level_total)}\n'
                            f'Change: {comma_number(level_total - exp[level - 1].total_exp) if level > 1 else "N/A"}\n'
                            f'```')
                    await ctx.send(embed=discord.Embed(title=f'Card Exp Lvl {level}',
                                                       description=desc))
                else:
                    start, end = arg.split('-')
                    start = int(start)
                    end = int(end)
                    if start > end:
                        await ctx.send('End exp is greater than start exp.')
                        return
                    start_exp = exp[start]
                    end_exp = exp[end]
                    change_amount = end_exp.total_exp - start_exp.total_exp
                    embed = discord.Embed(title=f'Card Exp Lvl {start}-{end}',
                                          description=f'```\n'
                                                      f'Lvl {str(start).rjust(2)}: {format_exp(start_exp)}\n'
                                                      f'Lvl {str(end).rjust(2)}: {format_exp(end_exp)}\n'
                                                      f'Change: {comma_number(change_amount).rjust(9)}\n'
                                                      f'```')
                    await ctx.send(embed=embed)

            except Exception:
                await ctx.send(f'Invalid card exp {arg}')


def setup(bot):
    bot.add_cog(Card(bot))
