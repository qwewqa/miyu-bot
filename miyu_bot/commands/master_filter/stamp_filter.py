import discord
from d4dj_utils.master.stamp_master import StampMaster

from miyu_bot.commands.master_filter.master_filter import MasterFilter, command_source, list_formatter


class StampFilter(MasterFilter[StampMaster]):
    def get_name(self, value: StampMaster) -> str:
        if value.quote is not None and value.quote in value.name:
            return value.name
        else:
            return f'{value.name + " " + value.quote.replace("～", "ー") if value.quote else value.description}'

    @command_source()
    def get_stamp_embed(self, ctx, stamp: StampMaster, server):
        embed = discord.Embed(title=self.format_stamp_name(stamp), description='N/A')
        return embed

    @list_formatter(name='stamp-search',
                    command_args=
                    dict(name='stamps',
                         aliases=['stickers'],
                         description='Lists stamps.',
                         help='!stamps'))
    def format_stamp_name(self, stamp: StampMaster):
        if stamp.quote is not None and stamp.quote in stamp.name:
            return stamp.name
        else:
            return f'{stamp.name}: {stamp.quote}'
