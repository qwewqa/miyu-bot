import discord
from d4dj_utils.master.login_bonus_master import LoginBonusMaster

from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.common.formatting import format_info
from miyu_bot.commands.master_filter.master_filter import MasterFilter, data_attribute, command_source


class LoginBonusFilter(MasterFilter[LoginBonusMaster]):
    def get_name(self, value: LoginBonusMaster) -> str:
        return value.title

    @data_attribute('name',
                    aliases=['title'],
                    is_sortable=True)
    def name(self, value: LoginBonusMaster):
        return value.title

    @data_attribute('date',
                    aliases=['release', 'recent'],
                    is_sortable=True,
                    reverse_sort=True)
    def date(self, ctx, value: LoginBonusMaster):
        return value.start_datetime

    @date.formatter
    def format_date(self, ctx, value: LoginBonusMaster):
        return f'{value.start_datetime.month:>2}/{value.start_datetime.day:02}/{value.start_datetime.year % 100:02}'

    @data_attribute('id',
                    is_sortable=True,
                    is_comparable=True)
    def id(self, value: LoginBonusMaster):
        return value.id

    @id.formatter
    def format_id(self, value: LoginBonusMaster):
        return str(value.id).zfill(4)

    @command_source(command_args=
                    dict(name='login_bonus',
                         aliases=['loginbonus'],
                         description='Displays login bonus info.',
                         help='!login_bonus'),
                    list_command_args=
                    dict(name='login_bonuses',
                         aliases=['loginbonuses'],
                         description='Lists login bonuses.',
                         help='!login_bonuses'),
                    default_sort=date,
                    default_display=date,
                    list_name='Login Bonus Search')
    def get_login_bonus_embed(self, ctx, login_bonus: LoginBonusMaster):
        embed = discord.Embed(title=login_bonus.title)

        embed.add_field(name='Info',
                        value=format_info({
                            'Start Date': login_bonus.start_datetime,
                            'End Date': login_bonus.end_datetime,
                            'Type': login_bonus.login_bonus_type.name,
                            'Loop': login_bonus.loop,
                        }),
                        inline=False)

        def format_login_bonus(item):
            rewards = item.rewards
            if len(rewards) > 1:
                prefix = f'{item.sequence}. '
                return prefix + ('\n' + ' ' * len(prefix)).join(reward.get_friendly_description()
                                                                for reward in rewards)
            elif len(rewards) == 1:
                return f'{item.sequence}. {rewards[0].get_friendly_description()}'
            else:
                return 'None'

        reward_text = '```' + ('\n'.join(format_login_bonus(item) for item in login_bonus.items) or 'None') + '```'

        embed.add_field(name='Rewards',
                        value=reward_text,
                        inline=False)

        embed.set_image(url=self.bot.asset_url + get_asset_filename(login_bonus.image_path))

        embed.set_footer(text=f'Login Bonus Id: {login_bonus.id:>04}')

        return embed

    @get_login_bonus_embed.list_formatter
    def format_login_bonus_title(self, login_bonus):
        return login_bonus.title
