from discord.ext import commands

from miyu_bot.commands.master_filter.master_filter_manager import MasterFilterManager


class Search(commands.Cog):
    def __init__(self, bot, master_filter_manager):
        master_filter_manager.reload()
        self.bot = bot
        self.commands = set()
        self.master_filters = master_filter_manager.filters
        for master_filter in self.master_filters:
            self.load_commands_from_filter(master_filter)

    def load_commands_from_filter(self, master_filter):
        for cmd in master_filter.get_commands(True):
            self.register_command(cmd)

    def register_command(self, command):
        command.cog = self
        self.__cog_commands__ = self.__cog_commands__ + (command,)


def setup(bot):
    bot.add_cog(Search(bot, MasterFilterManager(bot)))
