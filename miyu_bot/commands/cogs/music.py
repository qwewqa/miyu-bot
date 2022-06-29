import datetime
import enum
import logging
import re
from dataclasses import dataclass
from io import BytesIO
from typing import Tuple, Any

import discord
from d4dj_utils.chart.chart import Chart
from d4dj_utils.chart.mix import get_best_mix, get_mix_data, calculate_mix_rating
from d4dj_utils.chart.score_calculator import calculate_score
from d4dj_utils.master.chart_master import ChartDifficulty
from d4dj_utils.master.music_master import MusicMaster
from d4dj_utils.master.skill_master import SkillMaster
from discord import AllowedMentions
from discord.ext import commands

from miyu_bot.bot.bot import MiyuBot, PrefContext
from miyu_bot.commands.common.argument_parsing import parse_arguments, ParsedArguments
from miyu_bot.commands.master_filter.localization_manager import LocalizationManager


class Music(commands.Cog):
    bot: MiyuBot
    CUSTOM_MIX_MIN_LIFETIME = 3600  # Minimum amount of time in seconds before a custom mix is removed

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.custom_mixes = {}
        self.l10n = LocalizationManager(self.bot.fluent_loader, 'music.ftl')

    difficulty_names = {
        'expert': ChartDifficulty.Expert,
        'hard': ChartDifficulty.Hard,
        'normal': ChartDifficulty.Normal,
        'easy': ChartDifficulty.Easy,
        'expt': ChartDifficulty.Expert,
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

    @commands.command(name='score',
                      aliases=[],
                      description='Calculates chart score.',
                      help='!score Cyber Cyber diff=ex power=150000 acc=100 skill=50 $assist')
    async def score(self, ctx: PrefContext, *, arguments: ParsedArguments):
        def format_skill(skill):
            if skill.score_up_rate and skill.perfect_score_up_rate:
                return f'{skill.score_up_rate}%+{skill.perfect_score_up_rate}%p'
            elif skill.score_up_rate:
                return f'{skill.score_up_rate}%'
            elif skill.perfect_score_up_rate:
                return f'{skill.perfect_score_up_rate}%p'
            else:
                return f'0%'

        difficulty = arguments.single(['diff', 'difficulty'], default=None,
                                      converter=self.difficulty_names)
        power = arguments.single('power', default=150000, converter=lambda p: int(p))
        accuracy = arguments.single(['acc', 'accuracy'], default=100, converter=lambda a: float(a))
        skill = arguments.single(['skill', 'skills'], default=['40'], is_list=True)
        skill_duration = arguments.single(['skill_duration', 'sd', 'skilldur'], default=9.0, converter=lambda a: float(a))
        fever_bonus = arguments.single(['fever_bonus', 'fb'], default=0, converter=lambda a: float(a))
        fever_multiplier = 1 + fever_bonus / 100
        assist = arguments.tag('assist')
        random_skill_order = arguments.tags(['rng', 'randomorder', 'random_order'])
        if difficulty:
            song_name = arguments.text()
        else:
            song_name, difficulty = self.parse_chart_args(arguments.text())
        arguments.require_all_arguments_used()

        if song_name.lower() == 'mix':
            data = self.custom_mixes.get(ctx.author.id)
            if not data:
                await ctx.send('No recent user mix found. Use the mix command to create one.')
                return
            chart = data.chart
            title = 'Mix Score:\n' + data.name
        else:
            song = self.bot.master_filters.music.get(song_name, ctx)

            if not song:
                await ctx.send(f'Failed to find chart.')
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

        skill_re = re.compile(r'\d{1,3}(\.\d+)?%?|\d{1,3}(\.\d+)?%?\+\d{1,3}(\.\d+)?%?p|\d{1,3}(\.\d+)?%?p')

        def create_dummy_skill(score, perfect):
            return SkillMaster(
                ctx.assets,
                id=0,
                min_recovery_value=0,
                max_recovery_value=0,
                combo_support_count=0,
                score_up_rate=float(score),
                min_seconds=5,
                max_seconds=skill_duration,
                perfect_score_up_rate=float(perfect),
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
        if len(skills) == 4:
            skills = skills + [skills[0]]
        if len(skills) != 5:
            await ctx.send('Invalid skill count.')
            return

        if random_skill_order:
            # Score calc doesn't care that these aren't actually ints
            mean_score_up: Any = sum(s.score_up_rate for s in skills[:4]) / 4
            mean_perfect_score_up: Any = sum(s.perfect_score_up_rate for s in skills[:4]) / 4
            avg_skill = SkillMaster(
                ctx.assets,
                id=0,
                min_recovery_value=0,
                max_recovery_value=0,
                combo_support_count=0,
                score_up_rate=mean_score_up,
                min_seconds=5,
                max_seconds=skill_duration,
                perfect_score_up_rate=mean_perfect_score_up,
            )
            skills = [avg_skill] * 4 + [skills[-1]]

        embed = discord.Embed(title=title,
                              description=f'Power: {power:,}\n'
                                          f'Accuracy: {accuracy * 100:.1f}%\n'
                                          f'Skills: {", ".join(format_skill(skill) for skill in skills)}\n'
                                          f'Assist: {"On" if assist else "Off"}\n'
                                          f'\u200b')

        baseline = None
        for heading, enable_fever, autoplay, enable_combo_bonus in [
            ('Multi Live', True, False, True),
            ('Multi Live (No Combo)', True, False, False),
            ('Multi Live (Autoplay)', True, True, True),
            ('Solo Live / No Groovy', False, False, True),
            ('Solo Live (No Combo)', False, False, False),
            ('Solo Live (Autoplay)', False, True, True)
        ]:
            score = int(self.bot.chart_scorer(chart, power, skills, fever_multiplier, enable_fever, accuracy, assist,
                                              autoplay=autoplay, enable_combo_bonus=enable_combo_bonus))
            if not baseline:
                baseline = score
            embed.add_field(name=heading,
                            value=f'Score: {score:,}\n'
                                  f'Value: {score / baseline * 100:.1f}%'
                                  f'{f" ({(score - baseline) / baseline * 100:+.1f}%)" if score != baseline else ""}',
                            inline=True)
        await ctx.send(embed=embed)

    def parse_chart_args(self, arg: str) -> Tuple[str, ChartDifficulty]:
        split_args = arg.split()

        difficulty = ChartDifficulty.Expert
        if len(split_args) >= 2:
            final_word = split_args[-1].lower()
            if final_word.lower() in self.difficulty_names:
                difficulty = self.difficulty_names[final_word.lower()]
                arg = ' '.join(split_args[:-1])
        return arg, difficulty

    _music_durations = {}

    @commands.command(name='mixorder',
                      aliases=['ordermix', 'mix_order', 'order_mix'],
                      description='Finds order of songs when mixed.',
                      help='!mixorder grgr grgr grgr "cyber cyber"')
    async def mix_order(self, ctx: commands.Context, a: str, b: str, c: str, d: str):
        songs = []
        for name in [a, b, c, d]:
            song = self.bot.master_filters.music.get(name, ctx)
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
    async def mix(self, ctx: commands.Context, *args: str):
        if len(args) == 8:
            a, a_diff, b, b_diff, c, c_diff, d, d_diff = args
            names = [a, b, c, d]
            diff_names = [a_diff, b_diff, c_diff, d_diff]
        elif len(args) == 5:
            if re.match(r'[1-4]{4}', args[-1]):
                diff_mapping = {1: 'easy', 2: 'normal', 3: 'hard', 4: 'expert'}
                names = args[:-1]
                diff_names = [diff_mapping[int(c)] for c in args[-1]]
            else:
                await ctx.send('Invalid difficulty format')
                return
        elif len(args) == 4:
            names = args
            diff_names = ['ex'] * 4
        else:
            await ctx.send('Invalid argument count.')
            return

        songs = []
        for name in names:
            song = self.bot.master_filters.music.get(name, ctx)
            if not song:
                await ctx.send(f'Unknown song "{name}".', allowed_mentions=AllowedMentions.none())
                return
            if not song.mix_info:
                await ctx.send(f'Song "{song.name}" does not have mix enabled.')
                return
            songs.append(song)
        diffs = []
        for diff_name in diff_names:
            diff = self.difficulty_names.get(diff_name.lower())
            if not diff:
                await ctx.send(f'Unknown difficulty "{diff_name}".', allowed_mentions=AllowedMentions.none())
                return
            diffs.append(diff)

        mix = Chart.create_mix(songs, diffs)
        mix_image = await self.bot.loop.run_in_executor(self.bot.thread_pool, mix.render)
        mix_name = '\n'.join(f'{song.name} [{diff.name}]' for song, diff in zip(songs, diffs))
        note_counts = mix.get_note_counts()

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
                              f'Level: {mix.info.level}\n'
                              f'Ordered: {all(a == b for a, b in zip(get_best_mix(songs), songs))}\n'
                              f'Skills: {", ".join("{:.2f}s".format(t - mix.info.start_time) if t not in mix.info.base_skill_times else "[{:.2f}s]".format(t - mix.info.start_time) for t in mix.info.skill_times)}\n'
                              f'Fever: {mix.info.fever_start - mix.info.start_time:.2f}s - {mix.info.fever_end - mix.info.start_time:.2f}s\n'
                              f'Transitions: {", ".join("{:.2f}s".format(t - mix.info.start_time) for t in mix.info.medley_transition_times)}',
                        inline=False)
        embed.add_field(name='Combo',
                        value=f'Max Combo: {len(mix.notes)}\n'
                              f'Taps: {note_counts["tap"]} (dark: {note_counts["tap1"]}, light: {note_counts["tap2"]})\n'
                              f'Scratches: {note_counts["scratch"]} (left: {note_counts["scratch_left"]}, right: {note_counts["scratch_right"]})\n'
                              f'Stops: {note_counts["stop"]} (head: {note_counts["stop_start"]}, tail: {note_counts["stop_end"]})\n'
                              f'Long: {note_counts["long"]} (head: {note_counts["long_start"]}, tail: {note_counts["long_end"]})\n'
                              f'Slide: {note_counts["slide"]} (tick: {note_counts["slide_tick"]}, flick {note_counts["slide_flick"]})',
                        inline=True)
        embed.set_image(url='attachment://mix.png')

        await ctx.send(embed=embed, file=discord.File(fp=buffer, filename='mix.png'))

    @commands.command(name='mixrating',
                      aliases=['mix_rating'],
                      description='Returns the rating of a mix. Used internally.',
                      help='!mixrating grgr grgr grgr "cyber cyber"',
                      hidden=True)
    async def mixrating(self, ctx: commands.Context, a: str, b: str, c: str, d: str):
        songs = []
        for name in [a, b, c, d]:
            song = self.bot.master_filters.music.get(name, ctx)
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
