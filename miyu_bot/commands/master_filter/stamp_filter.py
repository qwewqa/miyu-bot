from d4dj_utils.master.stamp_master import StampMaster

from miyu_bot.commands.master_filter.master_filter import MasterFilter, command_source


class StampFilter(MasterFilter[StampMaster]):
    def get_name(self, value: StampMaster) -> str:
        return f'{value.name + " " + value.quote.replace("～", "ー") if value.quote else value.description}'

    @command_source(list_command_args=
                    dict(name='stamps',
                         aliases=['stickers'],
                         description='Lists stamps.',
                         help='!stamps'),
                    list_name='Stamp Search')
    def get_stamp_embed(self, ctx, stamp):
        pass

    @get_stamp_embed.list_formatter
    def format_stamp_name(self, stamp: StampMaster):
        return f'{stamp.name}: {stamp.quote}'
