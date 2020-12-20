import logging

from discord.ext import commands


class Card(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)



def setup(bot):
    bot.add_cog(Card(bot))
