import asyncio
import datetime
import enum
import logging
import re
from dataclasses import dataclass
from inspect import cleandoc
from io import BytesIO
from typing import Tuple

import discord
from d4dj_utils.chart.chart import Chart
from d4dj_utils.chart.mix import get_best_mix, get_mix_data, calculate_mix_rating
from d4dj_utils.chart.score_calculator import calculate_score
from d4dj_utils.master.chart_master import ChartDifficulty, ChartMaster
from d4dj_utils.master.common_enums import ChartSectionType
from d4dj_utils.master.music_master import MusicMaster
from d4dj_utils.master.skill_master import SkillMaster
from discord import AllowedMentions
from discord.ext import commands

from miyu_bot.bot.bot import D4DJBot
from miyu_bot.commands.common.argument_parsing import parse_arguments, list_operator_for
from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.common.emoji import difficulty_emoji_ids
from miyu_bot.commands.common.formatting import format_info
from miyu_bot.commands.common.fuzzy_matching import romanize
from miyu_bot.commands.common.reaction_message import run_tabbed_message, run_paged_message, run_deletable_message


class Music(commands.Cog):
    bot: D4DJBot
    CUSTOM_MIX_MIN_LIFETIME = 3600  # Minimum amount of time in seconds before a custom mix is removed

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.custom_mixes = {}

    @property
    def reaction_emojis(self):
        return [self.bot.get_emoji(eid) for eid in difficulty_emoji_ids.values()]

    difficulty_names = {
        'expert': ChartDifficulty.Expert,
        'hard': ChartDifficulty.Hard,
        'normal': ChartDifficulty.Normal,
        'easy': ChartDifficulty.Easy,
        'norm': ChartDifficulty.Normal,
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
        embed.set_thumbnail(url=self.bot.asset_url + get_asset_filename(song.jacket_path))

        artist_info = {
            'Lyricist': song.lyricist,
            'Composer': song.composer,
            'Arranger': song.arranger,
            'Unit': song.unit.name,
            'Special Unit Name': song.special_unit_name,
        }

        music_info = {
            'Category': song.category.name,
            'Duration': self.format_duration(song.duration),
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

    @commands.command(name='score',
                      aliases=[],
                      description='Calculates chart score.',
                      help='!score Cyber Cyber diff=ex power=150000 acc=100 skill=50 $assist')
    async def score(self, ctx: commands.Context, *, arg: commands.clean_content):
        def format_skill(skill):
            if skill.score_up_rate and skill.perfect_score_up_rate:
                return f'{skill.score_up_rate}%+{skill.perfect_score_up_rate}%p'
            elif skill.score_up_rate:
                return f'{skill.score_up_rate}%'
            elif skill.perfect_score_up_rate:
                return f'{skill.perfect_score_up_rate}%p'
            else:
                return f'0%'

        arguments = parse_arguments(arg)

        difficulty = arguments.single(['diff', 'difficulty'], default=ChartDifficulty.Expert,
                                      converter=self.difficulty_names)
        power = arguments.single('power', default=150000, converter=lambda p: int(p))
        accuracy = arguments.single(['acc', 'accuracy'], default=100, converter=lambda a: float(a))
        skill = arguments.single(['skill', 'skills'], default=['40'], is_list=True)
        assist = arguments.tag('assist')
        song_name = arguments.text()
        arguments.require_all_arguments_used()

        if song_name.lower() == 'mix':
            data = self.custom_mixes.get(ctx.author.id)
            if not data:
                await ctx.send('No recent user mix found. Use the mix command to create one.')
                return
            chart = data.chart
            title = 'Mix Score:\n' + data.name
        else:
            song = self.bot.asset_filters.music.get(song_name, ctx)

            if not song:
                await ctx.send(f'Failed to find chart {song_name}.')
                return
            if not song.charts:
                await ctx.send('Song does not have charts.')
                return

            chart = song.charts[difficulty]
            title = f'Song Score: {song.name} [{chart.difficulty.name}]'

        if not (0 <= accuracy <= 100):
            await ctx.send('Accuracy must be between 0 and 100.')
            return
        accuracy /= 100

        skill_re = re.compile(r'\d{1,3}%?|\d{1,3}%?\+\d{1,3}%?p|\d{1,3}%?p')

        def create_dummy_skill(score, perfect):
            return SkillMaster(
                self.bot.assets,
                id=0,
                min_recovery_value=0,
                max_recovery_value=0,
                combo_support_count=0,
                score_up_rate=int(score),
                min_seconds=5,
                max_seconds=9,
                perfect_score_up_rate=int(perfect),
            )

        skills = []
        for s in skill:
            if skill_re.fullmatch(s):
                effects = [(e[:-1] if e[-1] == '%' else e) for e in s.split('+')]
                skills.append(create_dummy_skill(next((e for e in effects if not e.endswith('p')), 0),
                                                 next((e[:-1] for e in effects if e.endswith('p')), 0)))
            else:
                await ctx.send('Invalid skill format.')
                return

        if len(skills) == 1:
            skills = skills * 5
        if len(skills) != 5:
            await ctx.send('Invalid skill count.')
            return

        embed = discord.Embed(title=title,
                              description=f'Power: {power:,}\n'
                                          f'Accuracy: {accuracy * 100:.1f}%\n'
                                          f'Skills: {", ".join(format_skill(skill) for skill in skills)}\n'
                                          f'Assist: {"On" if assist else "Off"}\n'
                                          f'\u200b')

        baseline = None
        for autoplay, enable_fever in [[False, True], [False, False], [True, True], [True, False]]:
            score = int(calculate_score(chart, power, skills, enable_fever, accuracy, assist, autoplay))
            if not baseline:
                baseline = score

            embed.add_field(name=f'{"Multi" if enable_fever else "Solo"} Live{" (Autoplay)" if autoplay else ""}',
                            value=f'Score: {score:,}\n'
                                  f'Value: {score / baseline * 100:.2f}%',
                            inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='mixorder',
                      aliases=['ordermix', 'mix_order', 'order_mix'],
                      description='Finds order of songs when mixed.',
                      help='!mixorder grgr grgr grgr "cyber cyber"')
    async def mix_order(self, ctx: commands.Context, a: str, b: str, c: str, d: str):
        songs = []
        for name in [a, b, c, d]:
            song = self.bot.asset_filters.music.get(name, ctx)
            if not song:
                await ctx.send(f'Unknown song "{name}".', allowed_mentions=AllowedMentions.none())
                return
            if not song.mix_info:
                await ctx.send(f'Song "{song.name}" does not have mix enabled.')
                return
            songs.append(song)

        mix = get_best_mix(songs)
        mix_data = get_mix_data(mix)
        nl = '\n'
        embed = discord.Embed(title='Mix Order',
                              description=f'```{nl.join(f"{i}. {self.format_song_title(song)}" for i, song in enumerate(mix, 1))}\n\n'
                                          f'Total Duration: {sum(md.duration for md in mix_data):.2f}s```')
        await ctx.send(embed=embed)

    @commands.command(name='mix',
                      aliases=[],
                      description='Creates a custom mix.',
                      help='!mix grgr hard cyber hard puransu expert "cats eye" easy')
    async def mix(self, ctx: commands.Context, a: str, a_diff: str, b: str, b_diff: str, c: str, c_diff: str,
                  d: str, d_diff: str):
        songs = []
        for name in [a, b, c, d]:
            song = self.bot.asset_filters.music.get(name, ctx)
            if not song:
                await ctx.send(f'Unknown song "{name}".', allowed_mentions=AllowedMentions.none())
                return
            if not song.mix_info:
                await ctx.send(f'Song "{song.name}" does not have mix enabled.')
                return
            songs.append(song)
        diffs = []
        for diff_name in [a_diff, b_diff, c_diff, d_diff]:
            diff = self.difficulty_names.get(diff_name.lower())
            if not diff:
                await ctx.send(f'Unknown difficulty "{diff_name}".', allowed_mentions=AllowedMentions.none())
                return
            diffs.append(diff)

        mix = Chart.create_mix(songs, diffs)
        mix_image = await self.bot.loop.run_in_executor(self.bot.thread_pool, mix.render)
        mix_name = '\n'.join(f'{song.name} [{diff.name}]' for song, diff in zip(songs, diffs))

        now = datetime.datetime.now()
        self.custom_mixes = {k: v
                             for k, v in self.custom_mixes.items()
                             if (now - v.create_time).total_seconds() < self.CUSTOM_MIX_MIN_LIFETIME}
        self.custom_mixes[ctx.author.id] = CustomMixData(mix_name, mix, now)

        buffer = BytesIO()
        mix_image.save(buffer, 'png')
        buffer.seek(0)

        embed = discord.Embed(title='Custom Mix')
        embed.add_field(name='Songs',
                        value=mix_name,
                        inline=False)
        embed.add_field(name='Info',
                        value=f'Duration: {self.format_duration(mix.info.end_time - mix.info.start_time)}\n'
                              f'Level: {mix.info.level}',
                        inline=False)
        embed.set_image(url='attachment://mix.png')

        await ctx.send(embed=embed, file=discord.File(fp=buffer, filename='mix.png'))

    @commands.command(name='mixrating',
                      aliases=['mix_rating'],
                      description='Returns the rating of a mix.',
                      help='!mixrating grgr grgr grgr "cyber cyber"')
    async def mixrating(self, ctx: commands.Context, a: str, b: str, c: str, d: str):
        songs = []
        for name in [a, b, c, d]:
            song = self.bot.asset_filters.music.get(name, ctx)
            if not song:
                await ctx.send(f'Unknown song "{name}".')
                return
            songs.append(song)

        rating = calculate_mix_rating(songs)

        nl = '\n'
        embed = discord.Embed(title='Mix Rating',
                              description=f'```{nl.join(f"{i}. {self.format_song_title(song)}" for i, song in enumerate(songs, 1))}\n\n'
                                          f'Rating: {rating}```')
        await ctx.send(embed=embed)

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

        sort, sort_op = arguments.single_op('sort', MusicAttribute.DefaultOrder,
                                            allowed_operators=['<', '>', '='], converter=music_attribute_aliases)
        reverse_sort = sort_op == '<' or arguments.tag('reverse')
        display, _op = arguments.single_op(['display', 'disp'], sort, allowed_operators=['='],
                                           converter=music_attribute_aliases)
        units = {self.bot.aliases.units_by_name[unit].id
                 for unit in arguments.tags(names=self.bot.aliases.units_by_name.keys(),
                                            aliases=self.bot.aliases.unit_aliases)}

        def difficulty_converter(d):
            return int(d[:-1]) + 0.5 if d[-1] == '+' else int(d)

        difficulty = arguments.repeatable_op(['difficulty', 'diff', 'level'], is_list=True,
                                             converter=difficulty_converter)

        songs = self.bot.asset_filters.music.get_by_relevance(arguments.text(), ctx)

        arguments.require_all_arguments_used()

        for value, op in difficulty:
            operator = list_operator_for(op)
            songs = [song for song in songs if operator(song.charts[4].level, value)]

        if units:
            songs = [song for song in songs if song.unit.id in units]

        if not (arguments.text_argument and sort == MusicAttribute.DefaultOrder):
            songs = sorted(songs, key=lambda s: sort.get_sort_key_from_music(s))
            if sort == MusicAttribute.DefaultOrder and songs and songs[0].id == 1:
                songs = [*songs[1:], songs[0]]
            if sort in [MusicAttribute.Level, MusicAttribute.Date, MusicAttribute.Combo]:
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
                listing.append(
                    f'{song.name}{" (" + song.special_unit_name + ")" if song.special_unit_name else ""}{" (Hidden)" if song.is_hidden else ""}')

        embed = discord.Embed(title=f'Song Search "{arg}"' if arg else 'Songs')
        asyncio.ensure_future(run_paged_message(ctx, embed, listing))

    def get_chart_embeds(self, song):
        embeds = []

        for difficulty in [ChartDifficulty.Easy, ChartDifficulty.Normal, ChartDifficulty.Hard, ChartDifficulty.Expert]:
            chart = song.charts[difficulty]
            embed = discord.Embed(title=f'{song.name} [{chart.difficulty.name}]')
            embed.set_thumbnail(url=self.bot.asset_url + get_asset_filename(song.jacket_path))
            embed.set_image(url=self.bot.asset_url + get_asset_filename(chart.image_path))
            chart_data = chart.load_chart_data()
            note_counts = chart_data.get_note_counts()

            embed.add_field(name='Info',
                            value=f'Level: {chart.display_level}\n'
                                  f'Duration: {self.format_duration(song.duration)}\n'
                                  f'Unit: {song.special_unit_name or song.unit.name}\n'
                                  f'Category: {song.category.name}\n'
                                  f'BPM: {song.bpm}\n'
                                  f'Designer: {chart.designer.name}\n',
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
            embed.set_footer(text='1 column = 10 seconds, 9 second skills')

            embeds.append(embed)

        return embeds

    def get_mix_embeds(self, song):
        embeds = []

        for difficulty in [ChartDifficulty.Easy, ChartDifficulty.Normal, ChartDifficulty.Hard, ChartDifficulty.Expert]:
            chart: ChartMaster = song.charts[difficulty]
            embed = discord.Embed(title=f'Mix: {song.name} [{chart.difficulty.name}]')
            embed.set_thumbnail(url=self.bot.asset_url + get_asset_filename(song.jacket_path))
            embed.set_image(url=self.bot.asset_url + get_asset_filename(chart.mix_path))

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
            if final_word.lower() in self.difficulty_names:
                difficulty = self.difficulty_names[final_word.lower()]
                arg = ''.join(split_args[:-1])
        return arg, difficulty

    _music_durations = {}

    @staticmethod
    def format_song_title(song):
        return f'{song.name}{" (" + song.special_unit_name + ")" if song.special_unit_name else ""}{" (Hidden)" if song.is_hidden else ""}'

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
    BPM = enum.auto()
    Combo = enum.auto()

    def get_sort_key_from_music(self, music: MusicMaster):
        return {
            self.DefaultOrder: -music.default_order,
            self.Name: music.name,
            self.Id: music.id,
            self.Unit: music.unit.name if not music.special_unit_name else f'{music.unit.name} ({music.special_unit_name})',
            self.Level: music.charts[4].display_level if len(music.charts) == 4 else '0',
            self.Duration: music.duration,
            self.Date: music.start_datetime,
            self.BPM: music.bpm,
            self.Combo: music.charts[4].note_counts[0].count if 4 in music.charts else 0,
        }[self]

    def get_formatted_from_music(self, music: MusicMaster):
        return {
            self.DefaultOrder: None,
            self.Name: None,
            self.Id: str(music.id).zfill(7),
            self.Unit: music.unit.name if not music.special_unit_name else f'{music.unit.name} ({music.special_unit_name})',
            self.Level: (music.charts[4].display_level if len(music.charts) == 4 else '?').ljust(3),
            self.Duration: Music.format_duration(music.duration),
            self.Date: str(music.start_datetime.date()),
            self.BPM: f'{music.bpm:>5.2f}',
            self.Combo: str(music.charts[4].note_counts[0].count) if 4 in music.charts else '?',
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
    'bpm': MusicAttribute.BPM,
    'combo': MusicAttribute.Combo,
}


@dataclass
class CustomMixData:
    name: str
    chart: Chart
    create_time: datetime.datetime


def setup(bot):
    bot.add_cog(Music(bot))
