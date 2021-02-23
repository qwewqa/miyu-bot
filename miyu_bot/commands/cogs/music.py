import asyncio
import contextlib
import enum
import logging
import wave
from inspect import cleandoc
from typing import Tuple

import discord
from d4dj_utils.master.chart_master import ChartDifficulty, ChartMaster
from d4dj_utils.master.common_enums import ChartSectionType
from d4dj_utils.master.music_master import MusicMaster
from discord.ext import commands

from miyu_bot.bot.bot import D4DJBot
from miyu_bot.commands.common.argument_parsing import parse_arguments, ArgumentError, list_operator_for
from miyu_bot.commands.common.asset_paths import get_chart_image_path, get_music_jacket_path, get_chart_mix_path
from miyu_bot.commands.common.emoji import difficulty_emoji_ids
from miyu_bot.commands.common.formatting import format_info
from miyu_bot.commands.common.fuzzy_matching import romanize
from miyu_bot.commands.common.reaction_message import run_tabbed_message, run_paged_message, run_deletable_message


class Music(commands.Cog):
    bot: D4DJBot

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @property
    def reaction_emojis(self):
        return [self.bot.get_emoji(eid) for eid in difficulty_emoji_ids.values()]

    difficulty_names = {
        'expert': ChartDifficulty.Expert,
        'hard': ChartDifficulty.Hard,
        'normal': ChartDifficulty.Normal,
        'easy': ChartDifficulty.Easy,
        'exp': ChartDifficulty.Expert,
        'hrd': ChartDifficulty.Hard,
        'nrm': ChartDifficulty.Normal,
        'esy': ChartDifficulty.Easy,
        'ex': ChartDifficulty.Expert,
        'hd': ChartDifficulty.Hard,
        'nm': ChartDifficulty.Normal,
        'es': ChartDifficulty.Easy,
    }

    @commands.command(name='song',
                      aliases=['music'],
                      description='Finds the song with the given name.',
                      help='!song grgr')
    async def song(self, ctx: commands.Context, *, arg: commands.clean_content):
        self.logger.info(f'Searching for song "{arg}".')

        song = self.bot.asset_filters.music.get(arg, ctx)

        if not song:
            msg = f'No results for song "{arg}".'
            await ctx.send(msg)
            self.logger.info(msg)
            return
        self.logger.info(f'Found song "{song}" ({romanize(song.name)}).')

        embed = discord.Embed(title=song.name)
        embed.set_thumbnail(url=self.bot.asset_url + get_music_jacket_path(song))

        artist_info = {
            'Lyricist': song.lyricist,
            'Composer': song.composer,
            'Arranger': song.arranger,
            'Unit': song.unit.name,
            'Special Unit Name': song.special_unit_name,
        }

        music_info = {
            'Category': song.category.name,
            'Duration': self.format_duration(self.get_music_duration(song)),
            'BPM': song.bpm,
            'Section Trend': song.section_trend.name,
            'Sort Order': song.default_order,
            'Levels': ', '.join(c.display_level for c in song.charts.values()),
            'Release Date': song.start_datetime,
            'Hidden': song.is_hidden,
        }

        embed.add_field(name='Artist',
                        value=format_info(artist_info),
                        inline=False)
        embed.add_field(name='Info',
                        value=format_info(music_info),
                        inline=False)

        message = await ctx.send(embed=embed)
        await run_deletable_message(ctx, message)

    @commands.command(name='chart',
                      aliases=[],
                      description='Finds the chart with the given name.',
                      help='!chart grgr\n!chart grgr normal')
    async def chart(self, ctx: commands.Context, *, arg: commands.clean_content):
        self.logger.info(f'Searching for chart "{arg}".')

        name, difficulty = self.parse_chart_args(arg)
        song = self.bot.asset_filters.music.get(name, ctx)

        if not song:
            msg = f'Failed to find chart "{name}".'
            await ctx.send(msg)
            self.logger.info(msg)
            return
        self.logger.info(f'Found song "{song}" ({romanize(song.name)}).')

        embeds = self.get_chart_embeds(song)

        # Difficulty enum easy-expert are 1-4, one more than the embed index
        asyncio.ensure_future(run_tabbed_message(ctx, self.reaction_emojis, embeds, None, difficulty - 1))

    @commands.command(name='sections',
                      aliases=['mixes'],
                      description='Finds the sections of the chart with the given name.',
                      help='!sections grgr')
    async def sections(self, ctx: commands.Context, *, arg: commands.clean_content):
        self.logger.info(f'Searching for chart sections "{arg}".')

        name, difficulty = self.parse_chart_args(arg)
        song = self.bot.asset_filters.music.get(name, ctx)

        if not song:
            msg = f'Failed to find chart "{name}".'
            await ctx.send(msg)
            self.logger.info(msg)
            return
        if not song.mix_info:
            msg = f'Song "{song.name}" does not have mix enabled.'
            await ctx.send(msg)
            self.logger.info(msg)
            return
        self.logger.info(f'Found song "{song}" ({romanize(song.name)}).')

        embeds = self.get_mix_embeds(song)

        asyncio.ensure_future(run_tabbed_message(ctx, self.reaction_emojis, embeds, None, difficulty - 1))

    @commands.command(name='songs',
                      aliases=['songsearch', 'song_search'],
                      description='Finds songs matching the given name.',
                      brief='!songs lhg',
                      help=cleandoc('''
                      Named arguments:
                        sort (<, =) [default|name|id|unit|level|difficulty|duration|date]
                        [display|disp] = [default|name|id|unit|level|difficulty|duration|date]
                        [difficulty|diff|level] ? <difficulty (11, 11.5, 11+, ...)>...
                        
                      Tags:
                        unit: [happy_around|peaky_p-key|photon_maiden|merm4id|rondo|lyrical_lily|other]
                       
                      Extended examples:
                        Songs in descending difficulty order
                          !songs sort<difficulty
                        Songs with difficulty from 11+ to 13+
                          !songs diff>=11+ diff<=13+
                        Songs with difficulty exactly 10 or 14, sorted alphabetically, displaying duration
                          !songs diff=10,14 sort=name disp=duration
                        Songs by happy around
                          !songs $happy_around'''))
    async def songs(self, ctx: commands.Context, *, arg: commands.clean_content = ''):
        self.logger.info(f'Searching for songs "{arg}".' if arg else 'Listing songs.')
        arguments = parse_arguments(arg)

        try:
            sort, sort_op = arguments.single('sort', MusicAttribute.DefaultOrder,
                                             allowed_operators=['<', '>', '='], converter=music_attribute_aliases)
            reverse_sort = sort_op == '<' or arguments.tag('reverse')
            display, _ = arguments.single(['display', 'disp'], sort, allowed_operators=['='],
                                          converter=music_attribute_aliases)
            units = {self.bot.aliases.units_by_name[unit].id
                     for unit in arguments.tags(names=self.bot.aliases.units_by_name.keys(),
                                                aliases=self.bot.aliases.unit_aliases)}

            def difficulty_converter(d):
                return int(d[:-1]) + 0.5 if d[-1] == '+' else int(d)

            difficulty = arguments.repeatable(['difficulty', 'diff', 'level'], is_list=True,
                                              converter=difficulty_converter)

            songs = self.bot.asset_filters.music.get_sorted(arguments.text(), ctx)

            arguments.require_all_arguments_used()
        except ArgumentError as e:
            await ctx.send(str(e))
            return

        for value, op in difficulty:
            operator = list_operator_for(op)
            songs = [song for song in songs if operator(song.charts[4].level, value)]

        if units:
            songs = [song for song in songs if song.unit.id in units]

        if not (arguments.text_argument and sort == MusicAttribute.DefaultOrder):
            songs = sorted(songs, key=lambda s: sort.get_sort_key_from_music(s))
            if sort == MusicAttribute.DefaultOrder and songs and songs[0].id == 1:
                songs = [*songs[1:], songs[0]]
            if sort in [MusicAttribute.Level, MusicAttribute.Date]:
                songs = songs[::-1]
            if reverse_sort:
                songs = songs[::-1]

        listing = []
        for song in songs:
            display_prefix = display.get_formatted_from_music(song)
            if display_prefix:
                listing.append(
                    f'{display_prefix} : {song.name}{" (" + song.special_unit_name + ")" if song.special_unit_name else ""}{" (Hidden)" if song.is_hidden else ""}')
            else:
                listing.append(f'{song.name}{" (" + song.special_unit_name + ")" if song.special_unit_name else ""}{" (Hidden)" if song.is_hidden else ""}')

        embed = discord.Embed(title=f'Song Search "{arg}"' if arg else 'Songs')
        asyncio.ensure_future(run_paged_message(ctx, embed, listing))

    def get_chart_embeds(self, song):
        embeds = []

        for difficulty in [ChartDifficulty.Easy, ChartDifficulty.Normal, ChartDifficulty.Hard, ChartDifficulty.Expert]:
            chart = song.charts[difficulty]
            embed = discord.Embed(title=f'{song.name} [{chart.difficulty.name}]')
            embed.set_thumbnail(url=self.bot.asset_url + get_music_jacket_path(song))
            embed.set_image(url=self.bot.asset_url + get_chart_image_path(chart))
            chart_data = chart.load_chart_data()
            note_counts = chart_data.get_note_counts()

            embed.add_field(name='Info',
                            value=f'Level: {chart.display_level}\n'
                                  f'Duration: {self.format_duration(self.get_music_duration(song))}\n'
                                  f'Unit: {song.special_unit_name or song.unit.name}\n'
                                  f'Category: {song.category.name}\n'
                                  f'BPM: {song.bpm}\n'
                                  f'Designer: {chart.designer.name}',
                            inline=False)
            embed.add_field(name='Combo',
                            value=f'Max Combo: {chart.note_counts[ChartSectionType.Full].count}\n'
                                  f'Taps: {note_counts["tap"]} (dark: {note_counts["tap1"]}, light: {note_counts["tap2"]})\n'
                                  f'Scratches: {note_counts["scratch"]} (left: {note_counts["scratch_left"]}, right: {note_counts["scratch_right"]})\n'
                                  f'Stops: {note_counts["stop"]} (head: {note_counts["stop_start"]}, tail: {note_counts["stop_end"]})\n'
                                  f'Long: {note_counts["long"]} (head: {note_counts["long_start"]}, tail: {note_counts["long_end"]})\n'
                                  f'Slide: {note_counts["slide"]} (tick: {note_counts["slide_tick"]}, flick {note_counts["slide_flick"]})',
                            inline=True)
            embed.add_field(name='Ratings',
                            value=f'NTS: {round(chart.trends[0] * 100, 2)}%\n'
                                  f'DNG: {round(chart.trends[1] * 100, 2)}%\n'
                                  f'SCR: {round(chart.trends[2] * 100, 2)}%\n'
                                  f'EFT: {round(chart.trends[3] * 100, 2)}%\n'
                                  f'TEC: {round(chart.trends[4] * 100, 2)}%\n',
                            inline=True)
            embed.set_footer(text='1 column = 10 seconds')

            embeds.append(embed)

        return embeds

    def get_mix_embeds(self, song):
        embeds = []

        for difficulty in [ChartDifficulty.Easy, ChartDifficulty.Normal, ChartDifficulty.Hard, ChartDifficulty.Expert]:
            chart: ChartMaster = song.charts[difficulty]
            embed = discord.Embed(title=f'Mix: {song.name} [{chart.difficulty.name}]')
            embed.set_thumbnail(url=self.bot.asset_url + get_music_jacket_path(song))
            embed.set_image(url=self.bot.asset_url + get_chart_mix_path(chart))

            note_counts = chart.note_counts
            mix_info = chart.mix_info

            info = {
                'Level': chart.display_level,
                'Unit': song.unit.name,
                'BPM': song.bpm,
                'Section Trend': song.section_trend.name,
            }

            begin = {
                'Time': f'{round(mix_info[ChartSectionType.Begin].duration, 2)}s',
                'Combo': note_counts[ChartSectionType.Begin].count,
            }
            middle = {
                'Time': f'{round(mix_info[ChartSectionType.Middle].duration, 2)}s',
                'Combo': note_counts[ChartSectionType.Middle].count,
            }
            end = {
                'Time': f'{round(mix_info[ChartSectionType.End].duration, 2)}s',
                'Combo': note_counts[ChartSectionType.End].count,
            }

            embed.add_field(name='Info',
                            value=format_info(info),
                            inline=False)
            embed.add_field(name='Begin',
                            value=format_info(begin),
                            inline=True)
            embed.add_field(name='Middle',
                            value=format_info(middle),
                            inline=True)
            embed.add_field(name='End',
                            value=format_info(end),
                            inline=True)
            embed.set_footer(text='1 column = 10 seconds')

            embeds.append(embed)

        return embeds

    def parse_chart_args(self, arg: str) -> Tuple[str, ChartDifficulty]:
        split_args = arg.split()

        difficulty = ChartDifficulty.Expert
        if len(split_args) >= 2:
            final_word = split_args[-1].lower()
            if final_word in self.difficulty_names:
                difficulty = self.difficulty_names[final_word]
                arg = ''.join(split_args[:-1])
        return arg, difficulty

    _music_durations = {}

    @staticmethod
    def get_music_duration(music: MusicMaster):
        if music.id in Music._music_durations:
            return Music._music_durations[music.id]
        with contextlib.closing(wave.open(str(music.audio_path.with_name(music.audio_path.name + '.wav')), 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            Music._music_durations[music.id] = duration
            return duration

    @staticmethod
    def format_duration(seconds):
        minutes = int(seconds // 60)
        seconds = round(seconds % 60, 2)
        return f'{minutes}:{str(int(seconds)).zfill(2)}.{str(int(seconds % 1 * 100)).zfill(2)}'


class MusicAttribute(enum.Enum):
    DefaultOrder = enum.auto()
    Name = enum.auto()
    Id = enum.auto()
    Unit = enum.auto()
    Level = enum.auto()
    Duration = enum.auto()
    Date = enum.auto()

    def get_sort_key_from_music(self, music: MusicMaster):
        return {
            self.DefaultOrder: -music.default_order,
            self.Name: music.name,
            self.Id: music.id,
            self.Unit: music.unit.name if not music.special_unit_name else f'{music.unit.name} ({music.special_unit_name})',
            self.Level: music.charts[4].display_level if len(music.charts) == 4 else 0,
            self.Duration: Music.get_music_duration(music),
            self.Date: music.start_datetime
        }[self]

    def get_formatted_from_music(self, music: MusicMaster):
        return {
            self.DefaultOrder: None,
            self.Name: None,
            self.Id: str(music.id).zfill(7),
            self.Unit: music.unit.name if not music.special_unit_name else f'{music.unit.name} ({music.special_unit_name})',
            self.Level: (music.charts[4].display_level if len(music.charts) == 4 else '?').ljust(3),
            self.Duration: Music.format_duration(Music.get_music_duration(music)),
            self.Date: str(music.start_datetime.date()),
        }[self]


music_attribute_aliases = {
    'default': MusicAttribute.DefaultOrder,
    'name': MusicAttribute.Name,
    'id': MusicAttribute.Id,
    'relevance': MusicAttribute.Name,
    'unit': MusicAttribute.Unit,
    'level': MusicAttribute.Level,
    'difficulty': MusicAttribute.Level,
    'diff': MusicAttribute.Level,
    'duration': MusicAttribute.Duration,
    'length': MusicAttribute.Duration,
    'date': MusicAttribute.Date,
}


def setup(bot):
    bot.add_cog(Music(bot))
