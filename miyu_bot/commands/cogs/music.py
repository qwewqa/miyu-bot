import asyncio
import contextlib
import enum
import logging
import wave
from functools import lru_cache
from typing import Tuple

import discord
from d4dj_utils.master.chart_master import ChartDifficulty, ChartMaster
from d4dj_utils.master.common_enums import ChartSectionType
from d4dj_utils.master.music_master import MusicMaster
from discord.ext import commands

from main import asset_manager, masters
from miyu_bot.commands.common.argument_parsing import parse_arguments, ArgumentError
from miyu_bot.commands.common.emoji import difficulty_emoji_ids
from miyu_bot.commands.common.formatting import format_info
from miyu_bot.commands.common.fuzzy_matching import romanize
from miyu_bot.commands.common.reaction_message import run_tabbed_message, run_paged_message


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
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
    async def song(self, ctx: commands.Context, *, arg: str):
        self.logger.info(f'Searching for song "{arg}".')

        song = masters.music.get(arg, ctx)

        if not song:
            msg = f'Failed to find song "{arg}".'
            await ctx.send(msg)
            self.logger.info(msg)
            return
        self.logger.info(f'Found song "{song}" ({romanize(song.name)}).')

        try:
            thumb = discord.File(song.jacket_path, filename='jacket.png')
        except FileNotFoundError:
            # Just a fallback
            thumb = discord.File(asset_manager.path / 'ondemand/stamp/stamp_10006.png', filename='jacket.png')

        embed = discord.Embed(title=song.name)
        embed.set_thumbnail(url=f'attachment://jacket.png')

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
        }

        embed.add_field(name='Artist',
                        value=format_info(artist_info),
                        inline=False)
        embed.add_field(name='Info',
                        value=format_info(music_info),
                        inline=False)

        await ctx.send(files=[thumb], embed=embed)

    @commands.command(name='chart',
                      aliases=[],
                      description='Finds the chart with the given name.',
                      help='!chart grgr\n!chart grgr normal')
    async def chart(self, ctx: commands.Context, *, arg: str):
        self.logger.info(f'Searching for chart "{arg}".')

        name, difficulty = self.parse_chart_args(arg)
        song = masters.music.get(name, ctx)

        if not song:
            msg = f'Failed to find chart "{name}".'
            await ctx.send(msg)
            self.logger.info(msg)
            return
        self.logger.info(f'Found song "{song}" ({romanize(song.name)}).')

        embeds, files = self.get_chart_embed_info(song)

        message = await ctx.send(files=files, embed=embeds[difficulty - 1])

        asyncio.ensure_future(run_tabbed_message(ctx, message, self.reaction_emojis, embeds))

    @commands.command(name='sections',
                      aliases=['mixes'],
                      description='Finds the sections of the chart with the given name.',
                      help='!sections grgr')
    async def sections(self, ctx: commands.Context, *, arg: str):
        self.logger.info(f'Searching for chart sections "{arg}".')

        name, difficulty = self.parse_chart_args(arg)
        song = masters.music.get(name, ctx)

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

        embeds, files = self.get_mix_embed_info(song)

        message = await ctx.send(files=files, embed=embeds[difficulty - 1])

        asyncio.ensure_future(run_tabbed_message(ctx, message, self.reaction_emojis, embeds))

    @commands.command(name='songs',
                      aliases=['songsearch', 'song_search'],
                      description='Finds songs matching the given name.',
                      help='!songs grgr')
    async def songs(self, ctx: commands.Context, *, arg: str = ''):
        self.logger.info(f'Searching for songs "{arg}".' if arg else 'Listing songs.')
        arguments = parse_arguments(arg)
        songs = masters.music.get_sorted(arguments.text_argument, ctx)

        try:
            sort, sort_op = arguments.single('sort', MusicAttribute.DefaultOrder,
                                       allowed_operators=['<', '>', '='], converter=music_attribute_names)
            reverse_sort = sort_op == '<'
            display, _ = arguments.single('display', sort, allowed_operators=['='], converter=music_attribute_names)
            arguments.require_all_arguments_used()
        except ArgumentError as e:
            await ctx.send(str(e))
            return

        if not (arguments.text_argument and sort == MusicAttribute.DefaultOrder):
            songs = sorted(songs, key=lambda s: sort.get_from_music(s))
            if sort == MusicAttribute.DefaultOrder:
                songs = [*songs[1:], songs[0]]
            if reverse_sort:
                songs = reversed(songs)

        listing = []
        for song in songs:
            display_prefix = display.get_formatted_from_music(song)
            if display_prefix:
                listing.append(f'{display_prefix} : {song.name}{" (" + song.special_unit_name + ")" if song.special_unit_name else ""}')
            else:
                listing.append(f'{song.name}{" (" + song.special_unit_name + ")" if song.special_unit_name else ""}')

        embed = discord.Embed(title=f'Song Search "{arg}"' if arg else 'Songs')
        asyncio.ensure_future(run_paged_message(ctx, embed, listing))

    def get_chart_embed_info(self, song):
        embeds = []

        try:
            thumb = discord.File(song.jacket_path, filename='jacket.png')
        except FileNotFoundError:
            # dig delight is just a fallback
            thumb = discord.File(masters.music.get('110001', None).jacket_path, filename='jacket.png')

        files = [thumb]

        for difficulty in [ChartDifficulty.Easy, ChartDifficulty.Normal, ChartDifficulty.Hard, ChartDifficulty.Expert]:
            chart = song.charts[difficulty]
            embed = discord.Embed(title=f'{song.name} [{chart.difficulty.name}]')
            embed.set_thumbnail(url=f'attachment://jacket.png')
            embed.set_image(
                url=f'https://qwewqa.github.io/d4dj-dumps/{chart.image_path.relative_to(asset_manager.path).as_posix()}'
            )

            chart_data = chart.load_chart_data()
            note_counts = chart_data.get_note_counts()

            embed.add_field(name='Info',
                            value=f'Level: {chart.display_level}\n'
                                  f'Duration: {self.format_duration(self.get_music_duration(song))}\n'
                                  f'Unit: {song.special_unit_name or song.unit.name}\n'
                                  f'Category: {song.category.name}\n'
                                  f'BPM: {song.bpm}',
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

        return embeds, files

    def get_mix_embed_info(self, song):
        embeds = []
        files = [discord.File(song.jacket_path, filename=f'jacket.png')]

        for difficulty in [ChartDifficulty.Easy, ChartDifficulty.Normal, ChartDifficulty.Hard, ChartDifficulty.Expert]:
            chart: ChartMaster = song.charts[difficulty]
            embed = discord.Embed(title=f'Mix: {song.name} [{chart.difficulty.name}]')
            embed.set_thumbnail(url=f'attachment://jacket.png')
            embed.set_image(
                url=f'https://qwewqa.github.io/d4dj-dumps/{chart.mix_path.relative_to(asset_manager.path).as_posix()}'
            )

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

        return embeds, files

    def parse_chart_args(self, arg: str) -> Tuple[str, ChartDifficulty]:
        split_args = arg.split()

        difficulty = ChartDifficulty.Expert
        if len(split_args) >= 2:
            final_word = split_args[-1]
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
    Unit = enum.auto()
    Level = enum.auto()
    Duration = enum.auto()
    Date = enum.auto()

    def get_from_music(self, music: MusicMaster):
        return {
            self.DefaultOrder: -music.default_order,
            self.Name: music.name,
            self.Unit: music.unit.name if not music.special_unit_name else f'{music.unit.name} ({music.special_unit_name})',
            self.Level: music.charts[4].display_level,
            self.Duration: Music.get_music_duration(music),
            self.Date: music.start_datetime
        }[self]

    def get_formatted_from_music(self, music: MusicMaster):
        return {
            self.DefaultOrder: None,
            self.Name: None,
            self.Unit: music.unit.name if not music.special_unit_name else f'{music.unit.name} ({music.special_unit_name})',
            self.Level: music.charts[4].display_level,
            self.Duration: Music.format_duration(Music.get_music_duration(music)),
            self.Date: str(music.start_datetime.date()),
        }[self]


music_attribute_names = {
    'default': MusicAttribute.DefaultOrder,
    'name': MusicAttribute.Name,
    'relevance': MusicAttribute.Name,
    'unit': MusicAttribute.Unit,
    'level': MusicAttribute.Level,
    'difficulty': MusicAttribute.Level,
    'duration': MusicAttribute.Duration,
    'length': MusicAttribute.Duration,
    'date': MusicAttribute.Date,
}


def setup(bot):
    bot.add_cog(Music(bot))
