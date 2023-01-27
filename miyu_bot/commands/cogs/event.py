import asyncio
import datetime
import datetime as dt
import itertools
import logging
import math
from collections import namedtuple
from typing import List, Optional, Union

import discord
import pytz
from d4dj_utils.master.event_master import EventMaster, EventState
from discord.ext import commands, tasks
from pytz import UnknownTimeZoneError

from miyu_bot.bot import models
from miyu_bot.bot.bot import MiyuBot, PrefContext
from miyu_bot.bot.models import valid_loop_intervals
from miyu_bot.bot.servers import Server
from miyu_bot.commands.common.argument_parsing import parse_arguments
from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.common.deletable_message import run_deletable_message
from miyu_bot.commands.common.reaction_message import run_tabbed_message
from miyu_bot.commands.master_filter.localization_manager import LocalizationManager


class Event(commands.Cog):
    bot: MiyuBot
    EPRATE_RESOLUTION = 2  # Resolution of the Rate/hr reported by endpoint in hours.

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.leaderboard_loop.start()
        self.l10n = LocalizationManager(self.bot.fluent_loader, "event.ftl")

    def cog_unload(self):
        self.leaderboard_loop.cancel()

    @commands.command(
        name="time", aliases=[], description="Displays the current time", help="!time"
    )
    async def time(self, ctx: commands.Context, *, arg=""):
        embed = discord.Embed(title="Time")

        def format_time(t: dt.datetime):
            return str(t.replace(microsecond=0))

        embed.add_field(
            name="Asia/Tokyo",
            value=format_time(dt.datetime.now(pytz.timezone("Asia/Tokyo"))),
            inline=False,
        )

        if arg:
            try:
                embed.add_field(
                    name=arg,
                    value=format_time(dt.datetime.now(pytz.timezone(arg))),
                    inline=False,
                )
            except UnknownTimeZoneError:
                await ctx.send(content=f'Invalid timezone "{arg}".')
                return
        else:
            embed.add_field(
                name="UTC",
                value=format_time(dt.datetime.now(dt.timezone.utc)),
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="timeleft",
        aliases=["tl", "time_left"],
        description="Displays the time left in the current event",
        help="!timeleft",
    )
    async def time_left(
        self, ctx: commands.Context, *, arg: commands.clean_content = ""
    ):
        event, timezone = await self.parse_event_argument(ctx, arg)

        state = event.state()

        embed = discord.Embed(title=event.name)

        embed.set_thumbnail(
            url=self.bot.asset_url + get_asset_filename(event.logo_path)
        )

        progress = None

        now = dt.datetime.now(dt.timezone.utc)

        if state == EventState.Upcoming:
            time_delta_heading = "Time Until Start"
            delta = event.start_datetime - now
            date_heading = "Start Date"
            date_value = event.start_datetime
        elif state == EventState.Open:
            time_delta_heading = "Time Until Close"
            delta = event.reception_close_datetime - now
            progress = 1 - (
                delta / (event.reception_close_datetime - event.start_datetime)
            )
            date_heading = "Close Date"
            date_value = event.reception_close_datetime
        elif state in (EventState.Closing, EventState.Ranks_Fixed):
            time_delta_heading = "Time Until Results"
            delta = event.result_announcement_datetime - now
            date_heading = "Results Date"
            date_value = event.result_announcement_datetime
        elif state == EventState.Results:
            time_delta_heading = "Time Until End"
            delta = event.end_datetime - now
            date_heading = "End Date"
            date_value = event.end_datetime
        else:
            time_delta_heading = "Time Since End"
            delta = now - event.end_datetime
            date_heading = "End Date"
            date_value = event.end_datetime

        date_value = discord.utils.format_dt(date_value)

        embed.add_field(
            name=time_delta_heading, value=self.format_timedelta(delta), inline=True
        )
        embed.add_field(
            name="Progress",
            value=f"{round(progress * 100, 2)}%" if progress is not None else "N/A",
            inline=True,
        )
        embed.add_field(name=date_heading, value=str(date_value), inline=True)

        await ctx.send(embed=embed)

    async def parse_event_argument(self, ctx, arg):
        arguments = parse_arguments(arg)
        await arguments.update_preferences(ctx)
        text = arguments.text()
        arguments.require_all_arguments_used()

        if text:
            # Allows relative id searches like `!event +1` for next event or `!event -2` for the event before last event
            if text[0] in ["-", "+"]:
                try:
                    latest = self.bot.master_filters.events.get_latest_event(ctx)
                    event = self.bot.master_filters.events.get(
                        str(latest.id + int(text)), ctx
                    )
                except ValueError:
                    event = self.bot.master_filters.events.get(text, ctx)
            else:
                event = self.bot.master_filters.events.get(text, ctx)
        else:
            event = self.bot.master_filters.events.get_latest_event(ctx)
        return event, ctx.preferences.timezone

    @staticmethod
    def format_timedelta(delta: datetime.timedelta):
        days = delta.days
        hours, rem = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{days}d {hours}h {minutes}m"

    def leaderboard_url(self, ctx: Union[PrefContext, Server]):
        if (
            isinstance(ctx, PrefContext) and ctx.preferences.server == Server.EN
        ) or ctx == Server.EN:
            return "http://www.projectdivar.com/eventdata/t20?chart=true&en=true"
        else:
            return "http://www.projectdivar.com/eventdata/t20?chart=true"

    @commands.hybrid_command(
        name="leaderboard",
        aliases=["lb"],
        description="Displays the full leaderboard",
        help="!leaderboard",
    )
    async def leaderboard(self, ctx: commands.Context, *, arg: str = ""):
        args = parse_arguments(arg)
        await args.update_preferences(ctx)
        args.require_all_arguments_used()
        text = self.get_leaderboard_text(
            self.bot.master_filters.events.get_latest_event(ctx),
            None,
            await self.get_leaderboard_data(ctx),
            None,
        )
        asyncio.ensure_future(run_deletable_message(ctx, content=text))

    @commands.hybrid_command(
        name="detailed_leaderboard",
        aliases=["dlb", "llb", "lbb", "llbb"],
        description="Displays a detailed leaderboard.",
        help="!dlb",
    )
    async def detailed_leaderboard(self, ctx: commands.Context, *, arg: str = ""):
        args = parse_arguments(arg)
        await args.update_preferences(ctx)
        args.require_all_arguments_used()
        event = self.bot.master_filters.events.get_latest_event(ctx)
        async with self.bot.session.get(self.leaderboard_url(ctx)) as resp:
            stats = [
                (int(k), v)
                for k, v in (await resp.json(encoding="utf-8"))["statistics"].items()
            ]
        for _rank, stat in stats:
            stat["points"] = stat["points"] if isinstance(stat["points"], int) else 0
        embeds = []
        t20_stats = stats[:20]
        other_stats = stats[20:]
        if t20_stats:
            t20_embed = discord.Embed(title=f"{event.name} [t20]")
            for rank, stat in t20_stats:
                t20_embed.add_field(
                    name=f't{rank}. {stat["name"]}',
                    value=f'Points: {stat["points"]:,}\n'
                    f'Rate: {stat["rate"]:,} pts/hr\n'
                    f'Average Gain: {math.ceil(stat["rate"] * self.EPRATE_RESOLUTION / stat["count"]):,}\n'
                    f'Update: {stat["lastUpdate"]}',
                    inline=True,
                )
            embeds.append(t20_embed)
        if other_stats:
            other_embed = discord.Embed(title=f"{event.name} [t50+]")
            for rank, stat in other_stats:
                other_embed.add_field(
                    name=f't{rank}. {stat["name"]}',
                    value=f'Points: {stat["points"]:,}\n'
                    f'Rate: {stat["rate"]:,} pts/hr',
                    inline=True,
                )
            embeds.append(other_embed)
        if len(embeds) == 1:
            asyncio.create_task(run_deletable_message(ctx, embed=embeds[0]))
        elif len(embeds) == 2:
            asyncio.create_task(run_tabbed_message(ctx, ["🏆", "🏅"], embeds))

    valid_tiers = [50, 100, 500, 1000, 2000, 5000, 10000, 20000, 30000, 50000]

    @tasks.loop(minutes=1)
    async def leaderboard_loop(self):
        # Storing this on the bot object allows it to persist past bot reloads
        if not hasattr(self.bot, "last_leaderboard_loop_data"):
            self.bot.last_leaderboard_loop_data = {Server.JP: {}, Server.EN: {}}
        try:
            for server in [Server.JP, Server.EN]:
                event = self.bot.master_filters.events.get_latest_event(server)
                now = datetime.datetime.now()
                minutes = now.minute + 60 * now.hour
                data = await self.get_leaderboard_data(server)
                last_loop_data = self.bot.last_leaderboard_loop_data[server]
                for interval in valid_loop_intervals:
                    if minutes % interval == 0:
                        if (
                            interval in last_loop_data
                            and last_loop_data[interval] == data
                        ):
                            continue
                        prev = last_loop_data.get(interval)
                        last_loop_data[interval] = data
                        channels = await models.Channel.filter(loop=interval)
                        for channel_data in channels:
                            try:
                                channel = self.bot.get_channel(channel_data.id)
                                if not channel:
                                    self.logger.warning(
                                        f"Failed to get channel for loop (id: {channel_data.id})."
                                    )
                                    continue
                                guild_data = await models.Channel.get_or_none(
                                    id=channel.guild.id
                                )
                                if channel_data.preference_set("server"):
                                    channel_server = channel_data.get_preference(
                                        "server"
                                    )
                                elif guild_data and guild_data.preference_set("server"):
                                    channel_server = guild_data.get_preference("server")
                                else:
                                    channel_server = Server.JP
                                if channel_server != server:
                                    continue
                                await channel.send(
                                    self.get_leaderboard_text(
                                        event, interval, data, prev
                                    )
                                )
                            except discord.Forbidden:
                                self.logger.warning(
                                    f"Failed send for loop (id: {channel_data.id})."
                                )
                                continue
        except Exception as e:
            self.logger.warning(
                f'Error in leaderboard loop: {getattr(e, "message", repr(e))}'
            )

    @leaderboard_loop.before_loop
    async def before_leaderboard_loop(self):
        if self.bot.gen_doc:
            return
        await self.bot.wait_until_ready()
        # Sleep until the start of the next minute
        await asyncio.sleep(61 - datetime.datetime.now().second)

    @commands.command(
        name="cutoff",
        aliases=[
            "co",
            *[f"t{i}" for i in range(1, 21)],
            "t50",
            "t100",
            "t500",
            "t1000",
            "t2000",
            "t5000",
            "t10000",
            "t20000",
            "t30000",
            "t50000",
            "t1k",
            "t2k",
            "t5k",
            "t10k",
            "t20k",
            "t30k",
            "t50k",
        ],
        description=f"Displays the cutoffs at different tiers.",
        help="!cutoff 50",
    )
    async def cutoff(self, ctx: PrefContext, *, tier: str = ""):
        if ctx.invoked_with.endswith("co") and tier == "conut":
            await ctx.send("🥥")
            return

        args = parse_arguments(tier)
        await args.update_preferences(ctx)
        tier = args.text()
        args.require_all_arguments_used()

        def process_tier_arg(tier_arg):
            tier_arg = tier_arg.lower()
            if tier_arg[0] == "t":
                tier_arg = tier_arg[1:]
            if tier_arg[-1] == "k":
                return str(round(1000 * float(tier_arg[:-1])))
            return tier_arg

        if ctx.invoked_with in ["cutoff", "co"]:
            tier = process_tier_arg(tier)
            if not tier.isnumeric():
                await ctx.send(f"Invalid tier: {tier}.")
                return
        else:
            tier = process_tier_arg(ctx.invoked_with)

        embed = await self.get_tier_embed(
            ctx.preferences.server,
            tier,
            self.bot.master_filters.events.get_latest_event(ctx),
        )

        if embed:
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"No data available for tier {tier}.")

    LBStatistic = namedtuple("LBStatistic", "rank points name")

    async def get_leaderboard_data(self, ctx: Union[PrefContext, Server]):
        async with self.bot.session.get(self.leaderboard_url(ctx)) as resp:
            return [
                self.LBStatistic(
                    int(k),
                    v["points"] if isinstance(v["points"], int) else 0,
                    v["name"],
                )
                for k, v in (await resp.json(encoding="utf-8"))["statistics"].items()
            ]

    def get_leaderboard_text(
        self,
        event: EventMaster,
        interval: Optional[int],
        data: List[LBStatistic],
        prev: Optional[List[LBStatistic]],
    ):
        if prev is None:
            prev = []
        if interval is not None:
            header = f"{event.name} [{interval} min]\n\nRank     Points      Change    Name\n"
        else:
            header = f"{event.name}\n\nRank     Points        Name\n"

        def get_change_text(d, p):
            if interval is None:
                return ""
            if p and d.points != p.points:
                t = f"+{d.points - p.points:,}"
                return f"{t:>8}"
            else:
                return f"     ---"

        body = "\n".join(
            f"{d.rank:<7,}  {d.points:>10,}  "
            f'{get_change_text(d, p)}  {d.name.replace("`", " ")}'
            for d, p in itertools.zip_longest(data, prev)
        )
        return f"```{header}{body}```"

    async def get_tier_embed(self, server, tier: str, event: EventMaster):
        async with self.bot.session.get(self.leaderboard_url(server)) as resp:
            leaderboard = await resp.json(encoding="utf-8")

        data = leaderboard["statistics"].get(tier)
        if not data:
            return None

        if event.state() == EventState.Open:
            delta = event.reception_close_datetime - dt.datetime.now(dt.timezone.utc)
            time_left = self.format_timedelta(delta)
            progress = f"{round(100 * (1 - (delta / (event.reception_close_datetime - event.start_datetime))), 2)}%"
        else:
            time_left = "N/A"
            progress = "N/A"

        embed = discord.Embed(
            title=f"{event.name} [t{tier}]", timestamp=dt.datetime.now(dt.timezone.utc)
        )
        embed.set_thumbnail(
            url=self.bot.asset_url + get_asset_filename(event.logo_path)
        )

        average_rate = (
            "\n( +"
            + str(math.ceil((data["rate"] * self.EPRATE_RESOLUTION) / data["count"]))
            + " avg )"
            if int(tier) <= 20
            else ""
        )  # Only T20 is tracked in real-time, we can't guarantee <2hr intervals for other points so the rate returned is just overall rate.

        embed.add_field(
            name="Points", value=str(data["points"]) + average_rate, inline=True
        )
        embed.add_field(
            name="Last Update", value=data["lastUpdate"] or "None", inline=True
        )
        embed.add_field(name="Rate", value=f'{data["rate"]} pts/hr', inline=True)
        embed.add_field(name="Current Estimate", value=data["estimate"], inline=True)
        embed.add_field(name="Final Prediction", value=data["prediction"], inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Time Left", value=time_left, inline=True)
        embed.add_field(name="Progress", value=progress, inline=True)
        return embed


async def setup(bot):
    await bot.add_cog(Event(bot))
