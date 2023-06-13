import re
from datetime import datetime

import discord
from d4dj_utils.master.login_bonus_master import LoginBonusMaster

from miyu_bot.bot.bot import PrefContext
from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.master_filter.master_filter import (
    MasterFilter,
    data_attribute,
    command_source,
    list_formatter,
)


class LoginBonusFilter(MasterFilter[LoginBonusMaster]):
    def get_name(self, value: LoginBonusMaster) -> str:
        return value.title

    def get_select_name(self, value: LoginBonusMaster):
        return value.title, value.login_bonus_type.name, None

    @data_attribute("name", aliases=["title"], is_sortable=True)
    def name(self, value: LoginBonusMaster):
        return value.title

    @data_attribute(
        "date",
        aliases=["release", "recent"],
        is_default_sort=True,
        is_default_display=True,
        is_sortable=True,
        is_comparable=True,
        reverse_sort=True,
    )
    def date(self, ctx, value: LoginBonusMaster):
        return ctx.convert_tz(value.start_datetime).date()

    @date.formatter
    def format_date(self, ctx, value: LoginBonusMaster):
        dt = ctx.convert_tz(value.start_datetime)
        return f"{dt.year % 100:02}/{dt.month:02}/{dt.day:02}"

    @date.compare_converter
    def date_compare_converter(self, ctx: PrefContext, s):
        match = re.fullmatch(r"(\d+)/(\d+)/(\d+)", s)
        if not match:
            raise
        y, m, d = (int(n) for n in match.groups())
        if y < 100:
            y += ctx.localize(datetime.now()).year // 100 * 100
        return ctx.localize(datetime(year=y, month=m, day=d)).date()

    @data_attribute("id", is_sortable=True, is_comparable=True)
    def id(self, value: LoginBonusMaster):
        return value.id

    @id.formatter
    def format_id(self, value: LoginBonusMaster):
        return str(value.id).zfill(4)

    @command_source(
        command_args=dict(
            name="login_bonus",
            aliases=["loginbonus"],
            description="Displays login bonus info.",
            help="!login_bonus",
        )
    )
    def get_login_bonus_embed(self, ctx, login_bonus: LoginBonusMaster, server):
        l10n = self.l10n[ctx]

        embed = discord.Embed(title=f"[{server.name}] {login_bonus.title}")

        embed.add_field(
            name=l10n.format_value("info"),
            value=l10n.format_value(
                "info-desc",
                {
                    "start-date": discord.utils.format_dt(login_bonus.start_datetime),
                    "end-date": discord.utils.format_dt(login_bonus.end_datetime),
                    "login-bonus-type": login_bonus.login_bonus_type.name,
                    "loop": login_bonus.loop,
                },
            ),
            inline=False,
        )

        def format_login_bonus(item):
            rewards = item.rewards
            if len(rewards) > 1:
                prefix = f"{item.sequence}. "
                return prefix + ("\n" + " " * len(prefix)).join(
                    reward.get_friendly_description() for reward in rewards
                )
            elif len(rewards) == 1:
                return f"{item.sequence}. {rewards[0].get_friendly_description()}"
            else:
                return l10n.format_value("none")

        reward_text = (
            "```"
            + (
                "\n".join(format_login_bonus(item) for item in login_bonus.items)
                or "None"
            )
            + "```"
        )

        if len(reward_text) > 1024:
            reward_text = l10n.format_value("too-many-results")

        embed.add_field(
            name=l10n.format_value("rewards"), value=reward_text, inline=False
        )

        embed.set_image(
            url=self.bot.asset_url + get_asset_filename(login_bonus.image_path)
        )

        embed.set_footer(
            text=l10n.format_value(
                "login-bonus-id", {"login-bonus-id": f"{login_bonus.id:>04}"}
            )
        )

        return embed

    @list_formatter(
        name="login-bonus-search",
        command_args=dict(
            name="login_bonuses",
            aliases=["loginbonuses"],
            description="Lists login bonuses.",
            help="!login_bonuses",
        ),
    )
    def format_login_bonus_title(self, login_bonus):
        return login_bonus.title
