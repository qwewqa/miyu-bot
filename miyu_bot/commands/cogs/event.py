import asyncio
import datetime as dt
import logging

import aiohttp
import dateutil.parser
import discord
import pytz
from d4dj_utils.master.event_master import EventMaster, EventState
from discord.ext import commands
from pytz import UnknownTimeZoneError

from main import asset_manager, masters
from miyu_bot.commands.common.emoji import attribute_emoji_ids_by_attribute_id, unit_emoji_ids_by_unit_id, \
    parameter_bonus_emoji_ids_by_parameter_id, \
    event_point_emoji_id
from miyu_bot.commands.common.formatting import format_info
from miyu_bot.commands.common.fuzzy_matching import romanize
from miyu_bot.commands.common.master_asset_manager import MasterFilter
from miyu_bot.commands.common.reaction_message import run_paged_message


class Event(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(name='event',
                      aliases=['ev'],
                      description='Finds the event with the given name.',
                      help='!event pkcooking')
    async def event(self, ctx: commands.Context, *, arg: commands.clean_content = ''):
        self.logger.info(f'Searching for event "{arg}".')

        event: EventMaster
        if arg:
            if arg[0] in ['-', '+']:
                try:
                    latest = self.get_latest_event(ctx)
                    event = masters.events.get(str(latest.id + int(arg)), ctx)
                except ValueError:
                    event = masters.events.get(arg, ctx)
            else:
                event = masters.events.get(arg, ctx)
        else:
            event = self.get_latest_event(ctx)

        if not event:
            msg = f'Failed to find event "{arg}".'
            await ctx.send(msg)
            self.logger.info(msg)
            return
        self.logger.info(f'Found event "{event}" ({romanize(event.name)}).')

        try:
            logo = discord.File(event.logo_path, filename='logo.png')
        except FileNotFoundError:
            # Just a fallback
            logo = discord.File(asset_manager.path / 'ondemand/stamp/stamp_10006.png', filename='logo.png')

        embed = discord.Embed(title=event.name)
        embed.set_thumbnail(url=f'attachment://logo.png')

        duration_hour_part = round((event.duration.seconds / 3600), 2)
        duration_hour_part = duration_hour_part if not duration_hour_part.is_integer() else int(duration_hour_part)
        duration_hours = round((event.duration.days * 24 + event.duration.seconds / 3600), 2)
        duration_hours = duration_hours if not duration_hours.is_integer() else int(duration_hours)

        embed.add_field(name='Dates',
                        value=format_info({
                            'Duration': f'{event.duration.days} days, {duration_hour_part} hours '
                                        f'({duration_hours} hours)',
                            'Start': event.start_datetime,
                            'Close': event.reception_close_datetime,
                            'Rank Fix': event.rank_fix_start_datetime,
                            'Results': event.result_announcement_datetime,
                            'End': event.end_datetime,
                            'Story Unlock': event.story_unlock_datetime,
                            'Status': event.state().name,
                        }),
                        inline=False)
        embed.add_field(name='Event Type',
                        value=event.event_type.name,
                        inline=True)
        embed.add_field(name='Bonus Characters',
                        value='\n'.join(
                            f'{self.bot.get_emoji(unit_emoji_ids_by_unit_id[char.unit_id])} {char.full_name_english}'
                            for char in event.bonus.characters
                        ),
                        inline=True)
        embed.add_field(name='Bonus Attribute',
                        value=f'{self.bot.get_emoji(attribute_emoji_ids_by_attribute_id[event.bonus.attribute_id])} '
                              f'{event.bonus.attribute.en_name.capitalize()}' if event.bonus.attribute else 'None',
                        inline=True)
        embed.add_field(name='Point Bonus',
                        value=format_info({
                            'Attribute': f'{self.bot.get_emoji(event_point_emoji_id)} +{event.bonus.attribute_match_point_bonus_value}%' if event.bonus.attribute_match_point_bonus_value else 'None',
                            'Character': f'{self.bot.get_emoji(event_point_emoji_id)} +{event.bonus.character_match_point_bonus_value}%' if event.bonus.character_match_point_bonus_value else 'None',
                            'Both': f'{self.bot.get_emoji(event_point_emoji_id)} +{event.bonus.all_match_point_bonus_value}%' if event.bonus.all_match_point_bonus_value else 'None',
                        }),
                        inline=True)
        embed.add_field(name='Parameter Bonus',
                        value=format_info({
                            'Attribute': f'{self.bot.get_emoji(parameter_bonus_emoji_ids_by_parameter_id[event.bonus.attribute_match_parameter_bonus_id])} +{event.bonus.attribute_match_parameter_bonus_value}%' if event.bonus.attribute_match_parameter_bonus_value else 'None',
                            'Character': f'{self.bot.get_emoji(parameter_bonus_emoji_ids_by_parameter_id[event.bonus.character_match_parameter_bonus_id])} +{event.bonus.attribute_match_parameter_bonus_value}%' if event.bonus.attribute_match_parameter_bonus_value else 'None',
                            'Both': f'{self.bot.get_emoji(parameter_bonus_emoji_ids_by_parameter_id[event.bonus.all_match_parameter_bonus_id])} +{event.bonus.all_match_parameter_bonus_value}%' if event.bonus.all_match_parameter_bonus_value else 'None',
                        }),
                        inline=True)
        embed.set_footer(text=f'Event Id: {event.id}')

        await ctx.send(files=[logo], embed=embed)

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
    async def time_left(self, ctx: commands.Context):
        latest = self.get_latest_event(ctx)

        state = latest.state()

        logo = discord.File(latest.logo_path, filename='logo.png')

        embed = discord.Embed(title=latest.name)
        embed.set_thumbnail(url=f'attachment://logo.png')

        progress = None

        if state == EventState.Upcoming:
            time_delta_heading = 'Time Until Start'
            time_delta = latest.start_datetime - dt.datetime.now(dt.timezone.utc)
            date_heading = 'Start Date'
            date_value = latest.start_datetime
        elif state == EventState.Open:
            time_delta_heading = 'Time Until Close'
            time_delta = latest.reception_close_datetime - dt.datetime.now(dt.timezone.utc)
            progress = 1 - (time_delta / (latest.reception_close_datetime - latest.start_datetime))
            date_heading = 'Close Date'
            date_value = latest.reception_close_datetime
        elif state in (EventState.Closing, EventState.Ranks_Fixed):
            time_delta_heading = 'Time Until Results'
            time_delta = latest.result_announcement_datetime - dt.datetime.now(dt.timezone.utc)
            date_heading = 'Results Date'
            date_value = latest.result_announcement_datetime
        elif state == EventState.Results:
            time_delta_heading = 'Time Until End'
            time_delta = latest.end_datetime - dt.datetime.now(dt.timezone.utc)
            date_heading = 'End Date'
            date_value = latest.end_datetime
        else:
            time_delta_heading = 'Time Since End'
            time_delta = dt.datetime.now(dt.timezone.utc) - latest.end_datetime
            date_heading = 'End Date'
            date_value = latest.end_datetime

        days = time_delta.days
        hours, rem = divmod(time_delta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)

        embed.add_field(name=time_delta_heading,
                        value=f'{days}d {hours}h {minutes}m',
                        inline=True)
        embed.add_field(name='Progress',
                        value=f'{round(progress * 100, 2)}%' if progress is not None else 'N/A',
                        inline=True)
        embed.add_field(name=date_heading,
                        value=str(date_value),
                        inline=True)

        await ctx.send(files=[logo], embed=embed)

    def get_latest_event(self, ctx: commands.Context) -> EventMaster:
        """Returns the oldest event that has not ended or the newest event otherwise."""
        try:
            # NY event overlapped with previous event
            return min((v for v in masters.events.values(ctx) if v.state() == EventState.Open),
                       key=lambda e: e.start_datetime)
        except ValueError:
            try:
                return min((v for v in masters.events.values(ctx) if v.state() < EventState.Ended),
                           key=lambda e: e.start_datetime)
            except ValueError:
                return max(masters.events.values(ctx), key=lambda v: v.start_datetime)

    @commands.command(name='t20',
                      aliases=['top20', 'top_20'],
                      description='Displays the top 20 in the main leaderboard',
                      help='!t20')
    async def t20(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            async with session.get('http://www.projectdivar.com/eventdata/t20') as resp:
                leaderboard = await resp.json(encoding='utf-8')

        latest = self.get_latest_event(ctx)
        logo = discord.File(latest.logo_path, filename='logo.png')
        embed = discord.Embed(title=f'{latest.name} t20').set_thumbnail(url=f'attachment://logo.png')
        max_points_digits = len(str(leaderboard[0]['points']))
        nl = "\n"
        update_date = dateutil.parser.isoparse(leaderboard[0]["date"]).replace(microsecond=0)
        update_date = update_date.astimezone(pytz.timezone('Asia/Tokyo'))
        header = f'Updated {update_date}\n\nRank  {"Points".ljust(max_points_digits)}  Name'
        listing = [
            f'{str(player["rank"]).ljust(4)}  {str(player["points"]).ljust(max_points_digits)}  {player["name"].replace(nl, "")}'
            for player in leaderboard]
        paged = run_paged_message(ctx, embed, listing, header=header, page_size=10, files=[logo], numbered=False)
        asyncio.ensure_future(paged)


def setup(bot):
    bot.add_cog(Event(bot))
