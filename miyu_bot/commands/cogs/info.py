from discord.ext import commands


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.master_filters.reload()
        self.commands = set()
        self.master_filters = bot.master_filters.filters
        for master_filter in self.master_filters:
            self.load_commands_from_filter(master_filter)

    def load_commands_from_filter(self, master_filter):
        for cmd in master_filter.get_commands(True):
            cmd.master_filter = master_filter
            self.register_command(cmd)

    def register_command(self, command):
        command.cog = self
        self.__cog_commands__ = self.__cog_commands__ + (command,)


async def setup(bot):
    await bot.add_cog(Info(bot))
