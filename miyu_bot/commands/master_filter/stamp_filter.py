from d4dj_utils.master.stamp_master import StampMaster

from miyu_bot.commands.master_filter.master_filter import MasterFilter, command_source, list_formatter


class StampFilter(MasterFilter[StampMaster]):
    def get_name(self, value: StampMaster) -> str:
        if value.quote in value.name:
            return value.name
        else:
            return f'{value.name + " " + value.quote.replace("～", "ー") if value.quote else value.description}'

    @list_formatter(name='stamp-search',
                    list_command_args=
                    dict(name='stamps',
                         aliases=['stickers'],
                         description='Lists stamps.',
                         help='!stamps'))
    def format_stamp_name(self, stamp: StampMaster):
        if stamp.quote in stamp.name:
            return stamp.name
        else:
            return f'{stamp.name}: {stamp.quote}'
