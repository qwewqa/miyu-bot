import datetime
import logging

import discord
from d4dj_utils.master.event_master import EventMaster, EventState
from discord.ext import commands

from main import asset_manager
from miyu_bot.commands.common.emoji import attribute_emoji_by_id, unit_emoji_by_id, parameter_bonus_emoji_by_id, \
    event_point_emoji
from miyu_bot.commands.common.formatting import format_info
from miyu_bot.commands.common.fuzzy_matching import FuzzyMap, romanize


class Event(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.events = FuzzyMap(
            lambda e: e.start_datetime < datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)
        )
        for e in asset_manager.event_master.values():
            self.events[e.name] = e

    @commands.command(name='event',
                      aliases=['ev'],
                      description='Finds the event with the given name.',
                      help='!event pkcooking')
    async def event(self, ctx: commands.Context, *, arg: str = ""):
        self.logger.info(f'Searching for event "{arg}".')

        event: EventMaster
        if arg:
            try:
                event = asset_manager.event_master[int(arg)]
                if event not in self.events.values():
                    event = self.events[arg]
            except (ValueError, KeyError):
                event = self.events[arg]
        else:
            event = self.get_latest_event()

        if not event:
            msg = f'Failed to find event "{arg}".'
            await ctx.send(msg)
            self.logger.info(msg)
            return
        self.logger.info(f'Found event "{event}" ({romanize(event.name)}).')

        logo = discord.File(event.logo_path, filename='logo.png')

        embed = discord.Embed(title=event.name)
        embed.set_thumbnail(url=f'attachment://logo.png')

        embed.add_field(name='Dates',
                        value=format_info({
                            'Duration': event.duration,
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
                            f'{self.bot.get_emoji(unit_emoji_by_id[char.unit_id])} {char.full_name_english}'
                            for char in event.bonus.characters
                        ),
                        inline=True)
        embed.add_field(name='Bonus Attribute',
                        value=f'{self.bot.get_emoji(attribute_emoji_by_id[event.bonus.attribute_id])} '
                              f'{event.bonus.attribute.en_name.capitalize()}' if event.bonus.attribute else 'None',
                        inline=True)
        embed.add_field(name='Point Bonus',
                        value=format_info({
                            'Attribute': f'{self.bot.get_emoji(event_point_emoji)} +{event.bonus.attribute_match_point_bonus_value}%' if event.bonus.attribute_match_point_bonus_value else 'None',
                            'Character': f'{self.bot.get_emoji(event_point_emoji)} +{event.bonus.character_match_point_bonus_value}%' if event.bonus.character_match_point_bonus_value else 'None',
                            'Both': f'{self.bot.get_emoji(event_point_emoji)} +{event.bonus.all_match_point_bonus_value}%' if event.bonus.all_match_point_bonus_value else 'None',
                        }),
                        inline=True)
        embed.add_field(name='Parameter Bonus',
                        value=format_info({
                            'Attribute': f'{self.bot.get_emoji(parameter_bonus_emoji_by_id[event.bonus.attribute_match_parameter_bonus_id])} +{event.bonus.attribute_match_parameter_bonus_value}%' if event.bonus.attribute_match_parameter_bonus_value else 'None',
                            'Character': f'{self.bot.get_emoji(parameter_bonus_emoji_by_id[event.bonus.character_match_parameter_bonus_id])} +{event.bonus.attribute_match_parameter_bonus_value}%' if event.bonus.attribute_match_parameter_bonus_value else 'None',
                            'Both': f'{self.bot.get_emoji(parameter_bonus_emoji_by_id[event.bonus.all_match_parameter_bonus_id])} +{event.bonus.all_match_parameter_bonus_value}%' if event.bonus.all_match_parameter_bonus_value else 'None',
                        }),
                        inline=True)
        embed.set_footer(text=f'Event Id: {event.id}')

        await ctx.send(files=[logo], embed=embed)

    @commands.command(name='timeleft',
                      aliases=['tl', 'time_left'],
                      description='Displays the time left in the current event',
                      help='!timeleft')
    async def time_left(self, ctx: commands.Context):
        latest = self.get_latest_event()

        state = latest.state()

        logo = discord.File(latest.logo_path, filename='logo.png')

        embed = discord.Embed(title=latest.name)
        embed.set_thumbnail(url=f'attachment://logo.png')

        progress = None

        if state == EventState.Upcoming:
            time_delta_heading = 'Time Until Start'
            time_delta = latest.start_datetime - datetime.datetime.now(datetime.timezone.utc)
            date_heading = 'Start Date'
            date_value = latest.start_datetime
        elif state == EventState.Open:
            time_delta_heading = 'Time Until Close'
            time_delta = latest.reception_close_datetime - datetime.datetime.now(datetime.timezone.utc)
            progress = 1 - (time_delta / (latest.reception_close_datetime - latest.start_datetime))
            date_heading = 'Close Date'
            date_value = latest.reception_close_datetime
        elif state in (EventState.Closing, EventState.Ranks_Fixed):
            time_delta_heading = 'Time Until Results'
            time_delta = latest.result_announcement_datetime - datetime.datetime.now(datetime.timezone.utc)
            date_heading = 'Results Date'
            date_value = latest.result_announcement_datetime
        elif state == EventState.Results:
            time_delta_heading = 'Time Until End'
            time_delta = latest.end_datetime - datetime.datetime.now(datetime.timezone.utc)
            date_heading = 'End Date'
            date_value = latest.end_datetime
        else:
            time_delta_heading = 'Time Since End'
            time_delta = datetime.datetime.now(datetime.timezone.utc) - latest.end_datetime
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

    def get_latest_event(self) -> EventMaster:
        """Returns the oldest event that has not ended or the newest event otherwise."""
        try:
            return min((v for v in self.events.values() if v.state() < EventState.Ended),
                       key=lambda e: e.start_datetime)
        except ValueError:
            return max(self.events.values(), key=lambda v: v.start_datetime)


def setup(bot):
    bot.add_cog(Event(bot))
