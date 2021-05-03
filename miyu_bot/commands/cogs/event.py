import asyncio
import datetime
import datetime as dt
import logging
import math
import textwrap

import dateutil.parser
import discord
import pytz
from d4dj_utils.master.event_master import EventMaster, EventState
from d4dj_utils.master.login_bonus_master import LoginBonusMaster
from discord.ext import commands, tasks
from pytz import UnknownTimeZoneError

from miyu_bot.bot import models
from miyu_bot.bot.bot import D4DJBot
from miyu_bot.bot.models import valid_loop_intervals
from miyu_bot.commands.common.argument_parsing import parse_arguments, ParsedArguments
from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.common.emoji import attribute_emoji_ids_by_attribute_id, unit_emoji_ids_by_unit_id, \
    parameter_bonus_emoji_ids_by_parameter_id, \
    event_point_emoji_id
from miyu_bot.commands.common.formatting import format_info
from miyu_bot.commands.common.fuzzy_matching import romanize
from miyu_bot.commands.common.reaction_message import run_paged_message, run_dynamically_paged_message, \
    run_deletable_message, run_tabbed_message


class Event(commands.Cog):
    bot: D4DJBot
    EPRATE_RESOLUTION = 2  # Resolution of the Rate/hr reported by endpoint in hours.

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.leaderboard_loop.start()

    def cog_unload(self):
        self.leaderboard_loop.cancel()

    @commands.command(name='login_bonus',
                      aliases=['loginbonus'],
                      description='Displays login bonus info.',
                      help='!loginbonus Happy Birthday')
    async def login_bonus(self, ctx: commands.Context, *, arg: commands.clean_content = ''):
        self.logger.info(f'Searching for login bonus "{arg}".')

        arguments = parse_arguments(arg)
        login_bonuses = self.get_login_bonuses(ctx, arguments)

        if not login_bonuses:
            await ctx.send(f'No results.')
            return

        if len(login_bonuses) == 1:
            embed = self.get_login_bonus_embed(login_bonuses[0])
            asyncio.create_task(run_deletable_message(ctx, await ctx.send(embed=embed)))
        else:
            idx = 0

            def generator(n):
                nonlocal idx
                idx += n
                idx = max(0, min(idx, len(login_bonuses) - 1))
                return self.get_login_bonus_embed(login_bonuses[idx])

            asyncio.create_task(run_dynamically_paged_message(ctx, generator))

    @commands.command(name='login_bonuses',
                      aliases=['loginbonuses'],
                      description='Displays login bonuses.',
                      help='!loginbonuses Happy Birthday')
    async def login_bonuses(self, ctx: commands.Context, *, arg: commands.clean_content = ''):
        self.logger.info(f'Searching for login bonus "{arg}".')

        arguments = parse_arguments(arg)
        login_bonuses = self.get_login_bonuses(ctx, arguments)
        embed = discord.Embed(title='Login Bonuses')
        asyncio.ensure_future(run_paged_message(ctx, embed, [l.title for l in login_bonuses]))

    def get_login_bonuses(self, ctx, arguments: ParsedArguments):
        text = arguments.text()
        arguments.require_all_arguments_used()

        login_bonuses = self.bot.asset_filters.login_bonuses.get_by_relevance(text, ctx)

        if not text:
            login_bonuses.sort(key=lambda l: (l.start_datetime, l.id))
            login_bonuses.reverse()

        return login_bonuses

    def get_login_bonus_embed(self, login_bonus: LoginBonusMaster):

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

        return embed

    @commands.command(name='time',
                      aliases=[],
                      description='Displays the current time',
                      help='!time')
    async def time(self, ctx: commands.Context, *, arg=''):
        embed = discord.Embed(title='Time')

        def format_time(t: dt.datetime):
            return str(t.replace(microsecond=0))

        embed.add_field(name='Asia/Tokyo', value=format_time(dt.datetime.now(pytz.timezone('Asia/Tokyo'))),
                        inline=False)

        if arg:
            try:
                embed.add_field(name=arg, value=format_time(dt.datetime.now(pytz.timezone(arg))), inline=False)
            except UnknownTimeZoneError:
                await ctx.send(content=f'Invalid timezone "{arg}".')
                return
        else:
            embed.add_field(name='UTC', value=format_time(dt.datetime.now(dt.timezone.utc)), inline=False)

        await ctx.send(embed=embed)

    @commands.command(name='timeleft',
                      aliases=['tl', 'time_left'],
                      description='Displays the time left in the current event',
                      help='!timeleft')
    async def time_left(self, ctx: commands.Context, *, arg: commands.clean_content = ''):
        event, timezone = await self.parse_event_argument(ctx, arg)

        state = event.state()

        embed = discord.Embed(title=event.name)

        embed.set_thumbnail(url=self.bot.asset_url + get_asset_filename(event.logo_path))

        progress = None

        now = dt.datetime.now(dt.timezone.utc)

        if state == EventState.Upcoming:
            time_delta_heading = 'Time Until Start'
            delta = event.start_datetime - now
            date_heading = 'Start Date'
            date_value = event.start_datetime
        elif state == EventState.Open:
            time_delta_heading = 'Time Until Close'
            delta = event.reception_close_datetime - now
            progress = 1 - (delta / (event.reception_close_datetime - event.start_datetime))
            date_heading = 'Close Date'
            date_value = event.reception_close_datetime
        elif state in (EventState.Closing, EventState.Ranks_Fixed):
            time_delta_heading = 'Time Until Results'
            delta = event.result_announcement_datetime - now
            date_heading = 'Results Date'
            date_value = event.result_announcement_datetime
        elif state == EventState.Results:
            time_delta_heading = 'Time Until End'
            delta = event.end_datetime - now
            date_heading = 'End Date'
            date_value = event.end_datetime
        else:
            time_delta_heading = 'Time Since End'
            delta = now - event.end_datetime
            date_heading = 'End Date'
            date_value = event.end_datetime

        date_value = date_value.astimezone(timezone)

        embed.add_field(name=time_delta_heading,
                        value=self.format_timedelta(delta),
                        inline=True)
        embed.add_field(name='Progress',
                        value=f'{round(progress * 100, 2)}%' if progress is not None else 'N/A',
                        inline=True)
        embed.add_field(name=date_heading,
                        value=str(date_value),
                        inline=True)

        await ctx.send(embed=embed)

    @staticmethod
    def format_timedelta(delta: datetime.timedelta):
        days = delta.days
        hours, rem = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return f'{days}d {hours}h {minutes}m'

    @commands.command(name='leaderboard',
                      aliases=['lb'],
                      description='Displays the full leaderboard',
                      help='!leaderboard')
    async def leaderboard(self, ctx: commands.Context):
        embed = await self.get_leaderboard_embed(self.bot.asset_filters.events.get_latest_event(ctx))
        message = await ctx.send(embed=embed)
        asyncio.ensure_future(run_deletable_message(ctx, message))

    @commands.command(name='detailed_leaderboard',
                      aliases=['dlb', 'llb', 'lbb', 'llbb'],
                      description='Displays a detailed leaderboard.',
                      help='!dlb')
    async def detailed_leaderboard(self, ctx: commands.Context):
        event = self.bot.asset_filters.events.get_latest_event(ctx)
        async with self.bot.session.get('http://www.projectdivar.com/eventdata/t20?chart=true') as resp:
            stats = [(int(k), v) for k, v in (await resp.json(encoding='utf-8'))['statistics'].items()]
        for _rank, stat in stats:
            stat['points'] = stat['points'] if isinstance(stat['points'], int) else 0
        embeds = []
        t20_stats = stats[:20]
        other_stats = stats[20:]
        if t20_stats:
            t20_embed = discord.Embed(title=f'{event.name} [t20]')
            for rank, stat in t20_stats:
                t20_embed.add_field(name=f't{rank}. {stat["name"]}',
                                    value=f'Points: {stat["points"]:,}\n'
                                          f'Rate: {stat["rate"]:,} pts/hr\n'
                                          f'Average Gain: {math.ceil(stat["rate"] * self.EPRATE_RESOLUTION / stat["count"]):,}\n'
                                          f'Update: {stat["lastUpdate"]}',
                                    inline=True)
            embeds.append(t20_embed)
        if other_stats:
            other_embed = discord.Embed(title=f'{event.name} [t50+]')
            for rank, stat in other_stats:
                other_embed.add_field(name=f't{rank}. {stat["name"]}',
                                      value=f'Points: {stat["points"]:,}\n'
                                            f'Rate: {stat["rate"]:,} pts/hr',
                                      inline=True)
            embeds.append(other_embed)
        if len(embeds) == 1:
            asyncio.create_task(run_deletable_message(ctx, await ctx.send(embed=embeds[0])))
        elif len(embeds) == 2:
            asyncio.create_task(run_tabbed_message(ctx, ['🏆', '🏅'], embeds))

    valid_tiers = [50, 100, 500, 1000, 2000, 5000, 10000, 20000, 30000, 50000]

    @tasks.loop(minutes=1)
    async def leaderboard_loop(self):
        # Storing this on the bot object allows it to persist past bot reloads
        if not hasattr(self.bot, 'last_leaderboard_loop_embeds'):
            self.bot.last_leaderboard_loop_embeds = {}
        try:
            event = self.bot.asset_filters.events.get_latest_event(None)
            now = datetime.datetime.now()
            minutes = now.minute + 60 * now.hour
            embed = await self.get_leaderboard_embed(event)
            for interval in valid_loop_intervals:
                if minutes % interval == 0:
                    if (interval in self.bot.last_leaderboard_loop_embeds and
                            self.bot.last_leaderboard_loop_embeds[interval].description == embed.description):
                        continue
                    self.bot.last_leaderboard_loop_embeds[interval] = embed
                    channels = await models.Channel.filter(loop=interval)
                    for channel_data in channels:
                        channel = self.bot.get_channel(channel_data.id)
                        if channel:
                            await channel.send(embed=embed)
                        else:
                            self.logger.warning(f'Failed to get channel for loop (id: {channel_data.id}).')
        except Exception as e:
            self.logger.warning(f'Error in leaderboard loop: {getattr(e, "message", repr(e))}')

    @leaderboard_loop.before_loop
    async def before_leaderboard_loop(self):
        await self.bot.wait_until_ready()
        # Sleep until the start of the next minute
        await asyncio.sleep(61 - datetime.datetime.now().second)

    @commands.command(name='cutoff',
                      aliases=['co', *[f't{i}' for i in range(1, 21)], 't50', 't100', 't500', 't1000', 't2000', 't5000',
                               't10000', 't20000', 't30000', 't50000',
                               't1k', 't2k', 't5k', 't10k', 't20k', 't30k', 't50k'],
                      description=f'Displays the cutoffs at different tiers.',
                      help='!cutoff 50')
    async def cutoff(self, ctx: commands.Context, tier: str = ''):
        if ctx.invoked_with.endswith('co') and tier == 'conut':
            await ctx.send('🥥')
            return

        def process_tier_arg(tier_arg):
            tier_arg = tier_arg.lower()
            if tier_arg[0] == 't':
                tier_arg = tier_arg[1:]
            if tier_arg[-1] == 'k':
                return str(round(1000 * float(tier_arg[:-1])))
            return tier_arg

        if ctx.invoked_with in ['cutoff', 'co']:
            tier = process_tier_arg(tier)
            if not tier.isnumeric():
                await ctx.send(f'Invalid tier: {tier}.')
                return
        else:
            tier = process_tier_arg(ctx.invoked_with)

        embed = await self.get_tier_embed(tier, self.bot.asset_filters.events.get_latest_event(ctx))

        if embed:
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'No data available for tier {tier}.')

    async def get_leaderboard_embed(self, event: EventMaster):
        async with self.bot.session.get('http://www.projectdivar.com/eventdata/t20') as resp:
            leaderboard = {entry['rank']: entry for entry in (await resp.json(encoding='utf-8'))}
        async with self.bot.session.get('http://www.projectdivar.com/eventdata/t20?chart=true') as resp:
            statistics = {int(k): v for k, v in (await resp.json(encoding='utf-8'))['statistics'].items()}
        max_points_digits = len(f'{statistics.get(1, {}).get("points", 1):,}')
        nl = "\n"
        header = f'Rank     {"Points":<{max_points_digits}}  Name'
        body = '\n'.join(
            f'{rank:<7,}  {stats["points"] if isinstance(stats["points"], int) else 0:>{max_points_digits},}  {leaderboard.get(rank, {}).get("name", "").replace(nl, "")}'
            for rank, stats in statistics.items())
        embed = discord.Embed(title=f'{event.name} Leaderboard', description=f'```{header}\n{body}```',
                              timestamp=datetime.datetime.now())
        embed.set_thumbnail(url=self.bot.asset_url + get_asset_filename(event.logo_path))
        return embed

    async def get_tier_embed(self, tier: str, event: EventMaster):
        async with self.bot.session.get('http://www.projectdivar.com/eventdata/t20?chart=true') as resp:
            leaderboard = await resp.json(encoding='utf-8')

        data = leaderboard['statistics'].get(tier)
        if not data:
            return None

        if event.state() == EventState.Open:
            delta = event.reception_close_datetime - dt.datetime.now(dt.timezone.utc)
            time_left = self.format_timedelta(delta)
            progress = f'{round(100 * (1 - (delta / (event.reception_close_datetime - event.start_datetime))), 2)}%'
        else:
            time_left = 'N/A'
            progress = 'N/A'

        embed = discord.Embed(title=f'{event.name} [t{tier}]', timestamp=dt.datetime.now(dt.timezone.utc))
        embed.set_thumbnail(url=self.bot.asset_url + get_asset_filename(event.logo_path))

        average_rate = "\n( +" + str(
            math.ceil((data['rate'] * self.EPRATE_RESOLUTION) / data['count'])) + " avg )" if int(
            tier) <= 20 else ""  # Only T20 is tracked in real-time, we can't guarantee <2hr intervals for other points so the rate returned is just overall rate.

        embed.add_field(name='Points',
                        value=str(data['points']) + average_rate,
                        inline=True)
        embed.add_field(name='Last Update',
                        value=data['lastUpdate'] or 'None',
                        inline=True)
        embed.add_field(name='Rate',
                        value=f'{data["rate"]} pts/hr',
                        inline=True)
        embed.add_field(name='Current Estimate',
                        value=data['estimate'],
                        inline=True)
        embed.add_field(name='Final Prediction',
                        value=data['prediction'],
                        inline=True)
        embed.add_field(name='\u200b',
                        value='\u200b',
                        inline=True)
        embed.add_field(name='Time Left',
                        value=time_left,
                        inline=True)
        embed.add_field(name='Progress',
                        value=progress,
                        inline=True)
        return embed


def setup(bot):
    bot.add_cog(Event(bot))
