import asyncio
import datetime
import enum
import functools
import itertools
import logging
import re
from dataclasses import dataclass
from io import BytesIO
from typing import Tuple, Any, List, Dict, Optional

import discord
from d4dj_utils.chart.chart import Chart
from d4dj_utils.chart.mix import get_best_mix, get_mix_data, calculate_mix_rating
from d4dj_utils.chart.score_calculator import calculate_score
from d4dj_utils.master.chart_master import ChartDifficulty, ChartMaster
from d4dj_utils.master.music_master import MusicMaster
from d4dj_utils.master.skill_master import SkillMaster
from discord import AllowedMentions, app_commands
from discord.ext import commands

from miyu_bot.bot.bot import MiyuBot, PrefContext
from miyu_bot.bot.servers import Server, SERVER_NAMES
from miyu_bot.commands.common.argument_parsing import parse_arguments, ParsedArguments
from miyu_bot.commands.master_filter.filter_list_view import FilterListView
from miyu_bot.commands.master_filter.filter_result import FilterResults
from miyu_bot.commands.master_filter.localization_manager import LocalizationManager


class Music(commands.Cog):
    bot: MiyuBot
    CUSTOM_MIX_MIN_LIFETIME = (
        3600  # Minimum amount of time in seconds before a custom mix is removed
    )

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.custom_mixes = {}
        self.l10n = LocalizationManager(self.bot.fluent_loader, "music.ftl")

    difficulty_names = {
        "expert": ChartDifficulty.Expert,
        "hard": ChartDifficulty.Hard,
        "normal": ChartDifficulty.Normal,
        "easy": ChartDifficulty.Easy,
        "expt": ChartDifficulty.Expert,
        "norm": ChartDifficulty.Normal,
        "exp": ChartDifficulty.Expert,
        "hrd": ChartDifficulty.Hard,
        "nrm": ChartDifficulty.Normal,
        "esy": ChartDifficulty.Easy,
        "ex": ChartDifficulty.Expert,
        "hd": ChartDifficulty.Hard,
        "nm": ChartDifficulty.Normal,
        "es": ChartDifficulty.Easy,
    }

    @functools.cache
    def reference_chart_score(self):
        reference_chart = self.bot.assets[Server.JP].chart_master[3200094]
        return self.bot.chart_scorer.score(
            chart=reference_chart,
            power=150_000,
            skills=[
                SkillMaster(self.bot.assets[Server.JP], score_up_rate=40, max_seconds=9)
            ]
            * 5,
        )

    @commands.hybrid_command(
        name="meta",
    )
    async def meta(
        self,
        ctx: PrefContext,
        skills: str = "60",
        groovy_score: app_commands.Range[float, 0, 100] = 0,
        skill_duration_up: app_commands.Range[float, 0, 100] = 0,
        solo: bool = False,
        auto: bool = False,
        server: Optional[str] = None,
    ):
        """Lists songs by score.

        Parameters
        ----------
        skills: str
            A list of skills. E.g. 80,60,50,40 or 60 or 80x6.75,60x9,50x9,40x9
        groovy_score: float
            Groovy score up percentage
        skill_duration_up: float
            Skill duration up percentage
        solo: bool
            Whether to calculate solo score
        auto: bool
            Whether to calculate auto score
        server: str
            The server to use. Defaults to the current server. Can be one of: 'jp' or 'en'
        """
        await ctx.defer()

        def make_skill(score, duration):
            return SkillMaster(
                self.bot.assets[Server.JP], score_up_rate=score, max_seconds=duration
            )

        # Skill formats:
        # score_up := [0-9]+
        # skill_time := 'x' float  // if not specified, default to 6.75 for 80% score up, and 9 otherwise
        # skill := score_up skill_time?
        # skills := skill (',' skill)*
        #
        # Example: 80,60
        # Example: 80x6.75,60x9,50x9,40x9

        skill_values: List[Tuple[int, float]] = []
        for skill in re.split(r"\s+|\s*,\s*", skills):
            skill = skill.strip()
            if not skill:
                raise commands.BadArgument("Invalid skill format")
            if skill[-1] == "x":
                score_up = int(skill[:-1])
                duration = 6.75 if score_up == 80 else 9
            elif "x" in skill:
                score_up, duration = skill.split("x")
                score_up = int(score_up)
                duration = float(duration)
            else:
                score_up = int(skill)
                duration = 6.75 if score_up == 80 else 9
            if not (0 <= score_up <= 200):
                raise commands.BadArgument("Invalid skill format")
            if not (0 <= duration <= 20):
                raise commands.BadArgument("Invalid skill format")
            skill_values.append((score_up, duration))

        # Apply skill duration up
        skill_values = [
            (score_up, duration * (1 + skill_duration_up / 100))
            for score_up, duration in skill_values
        ]

        if not skill_values or len(skill_values) > 4:
            raise commands.BadArgument("Invalid skill format")

        if len(skill_values) < 4:
            # Pad using last skill/m
            skill_values += [skill_values[-1]] * (4 - len(skill_values))

        leader_skill = skill_values[0]

        # find all permutations of skills, with weights
        skill_permutations = {}
        for perm in itertools.permutations(skill_values):
            skill_permutations[perm + (leader_skill,)] = (
                skill_permutations.get(perm, 0) + 1
            )

        weighted_skill_permutations = [
            ([make_skill(score_up, duration) for score_up, duration in perm], weight)
            for perm, weight in skill_permutations.items()
        ]

        if server is not None:
            server = server.lower()
            if server not in SERVER_NAMES:
                raise commands.BadArgument("Invalid server name")
            ctx.preferences.server = SERVER_NAMES[server]

        charts: List[ChartMaster] = list(self.bot.master_filters.charts.values(ctx))
        charts = [
            chart
            for chart in charts
            if chart.music.is_available
            and not chart.music.is_hidden
            and chart.music.id > 3
        ]

        async def score_chart(chart):
            await asyncio.sleep(0)
            total_score = 0
            total_weight = 0
            for skill_perm, weight in weighted_skill_permutations:
                score = self.bot.chart_scorer.score(
                    chart=chart,
                    power=150_000,
                    skills=skill_perm,
                    fever_multiplier=1.0 + groovy_score / 100,
                    enable_fever=not solo,
                    autoplay=auto,
                )
                total_score += score * weight
                total_weight += weight
            return total_score / total_weight

        chart_scores = {chart: await score_chart(chart) for chart in charts}
        charts = sorted(charts, key=lambda chart: chart_scores[chart], reverse=True)

        def format_score(_master_filter, _ctx, chart):
            return f"{chart_scores[chart] / self.reference_chart_score() * 100:5.1f}%  {chart.music.duration:>5.1f}s "

        def title():
            sorted_skill_values = sorted(skill_values, reverse=True)
            leader_skill_index = sorted_skill_values.index(leader_skill)
            # put [] around leader skill
            formatted_skills = " ".join(
                f"{score_up}x{duration}"
                if i != leader_skill_index
                else f"[{score_up}x{duration:.2f}]"
                for i, (score_up, duration) in enumerate(sorted_skill_values)
            )
            return f"Song Meta\nskills: {formatted_skills}\ngroovy_score: {groovy_score}\nsolo: {solo}\nauto: {auto}"

        results = FilterResults(
            master_filter=self.bot.master_filters.charts,
            command_source_info=None,
            server=ctx.preferences.server,
            values=charts,
            display_formatter=format_score,
            list_title=title(),
        )

        view = FilterListView(self.bot.master_filters.charts, ctx, results)
        embed = view.active_embed

        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(
        name="score",
        aliases=[],
        description="Calculates chart score.",
        help="!score Cyber Cyber diff=ex power=150000 acc=100 skill=50 $assist",
    )
    async def score(self, ctx: PrefContext, *, arguments: ParsedArguments):
        def format_skill(skill):
            if skill.score_up_rate and skill.perfect_score_up_rate:
                return f"{skill.score_up_rate}%+{skill.perfect_score_up_rate}%p"
            elif skill.score_up_rate:
                return f"{skill.score_up_rate}%"
            elif skill.perfect_score_up_rate:
                return f"{skill.perfect_score_up_rate}%p"
            else:
                return f"0%"

        difficulty = arguments.single(
            ["diff", "difficulty"], default=None, converter=self.difficulty_names
        )
        power = arguments.single("power", default=150000, converter=lambda p: int(p))
        accuracy = arguments.single(
            ["acc", "accuracy"], default=100, converter=lambda a: float(a)
        )
        skill = arguments.single(["skill", "skills"], default=["40"], is_list=True)
        skill_duration = arguments.single(
            ["skill_duration", "sd", "skilldur"],
            default=9.0,
            converter=lambda a: float(a),
        )
        fever_bonus = arguments.single(
            ["fever_bonus", "fb"], default=0, converter=lambda a: float(a)
        )
        fever_multiplier = 1 + fever_bonus / 100
        assist = arguments.tag("assist")
        random_skill_order = arguments.tags(["rng", "randomorder", "random_order"])
        if difficulty:
            song_name = arguments.text()
        else:
            song_name, difficulty = self.parse_chart_args(arguments.text())
        arguments.require_all_arguments_used()

        if song_name.lower() == "mix":
            data = self.custom_mixes.get(ctx.author.id)
            if not data:
                await ctx.send(
                    "No recent user mix found. Use the mix command to create one."
                )
                return
            chart = data.chart
            title = "Mix Score:\n" + data.name
        else:
            song = self.bot.master_filters.music.get(song_name, ctx)

            if not song:
                await ctx.send(f"Failed to find chart.")
                return
            if not song.charts:
                await ctx.send("Song does not have charts.")
                return

            chart = song.charts[difficulty]
            title = f"Song Score: {song.name} [{chart.difficulty.name}]"

        if not (0 <= accuracy <= 100):
            await ctx.send("Accuracy must be between 0 and 100.")
            return
        accuracy /= 100

        skill_re = re.compile(
            r"\d{1,3}(\.\d+)?%?|\d{1,3}(\.\d+)?%?\+\d{1,3}(\.\d+)?%?p|\d{1,3}(\.\d+)?%?p"
        )

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
                effects = [(e[:-1] if e[-1] == "%" else e) for e in s.split("+")]
                skills.append(
                    create_dummy_skill(
                        next((e for e in effects if not e.endswith("p")), 0),
                        next((e[:-1] for e in effects if e.endswith("p")), 0),
                    )
                )
            else:
                await ctx.send("Invalid skill format.")
                return

        if len(skills) == 1:
            skills = skills * 5
        if len(skills) == 4:
            skills = skills + [skills[0]]
        if len(skills) != 5:
            await ctx.send("Invalid skill count.")
            return

        if random_skill_order:
            # Score calc doesn't care that these aren't actually ints
            mean_score_up: Any = sum(s.score_up_rate for s in skills[:4]) / 4
            mean_perfect_score_up: Any = (
                sum(s.perfect_score_up_rate for s in skills[:4]) / 4
            )
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

        embed = discord.Embed(
            title=title,
            description=f"Power: {power:,}\n"
            f"Accuracy: {accuracy * 100:.1f}%\n"
            f'Skills: {", ".join(format_skill(skill) for skill in skills)}\n'
            f'Assist: {"On" if assist else "Off"}\n'
            f"\u200b",
        )

        baseline = None
        for heading, enable_fever, autoplay, enable_combo_bonus in [
            ("Multi Live", True, False, True),
            ("Multi Live (No Combo)", True, False, False),
            ("Multi Live (Autoplay)", True, True, True),
            ("Solo Live / No Groovy", False, False, True),
            ("Solo Live (No Combo)", False, False, False),
            ("Solo Live (Autoplay)", False, True, True),
        ]:
            score = int(
                self.bot.chart_scorer(
                    chart,
                    power,
                    skills,
                    fever_multiplier,
                    enable_fever,
                    accuracy,
                    assist,
                    autoplay=autoplay,
                    enable_combo_bonus=enable_combo_bonus,
                )
            )
            if not baseline:
                baseline = score
            embed.add_field(
                name=heading,
                value=f"Score: {score:,}\n"
                f"Value: {score / baseline * 100:.1f}%"
                f'{f" ({(score - baseline) / baseline * 100:+.1f}%)" if score != baseline else ""}',
                inline=True,
            )
        await ctx.send(embed=embed)

    def parse_chart_args(self, arg: str) -> Tuple[str, ChartDifficulty]:
        split_args = arg.split()

        difficulty = ChartDifficulty.Expert
        if len(split_args) >= 2:
            final_word = split_args[-1].lower()
            if final_word.lower() in self.difficulty_names:
                difficulty = self.difficulty_names[final_word.lower()]
                arg = " ".join(split_args[:-1])
        return arg, difficulty

    _music_durations = {}

    @commands.hybrid_command(
        name="mixorder",
        aliases=["ordermix", "mix_order", "order_mix"],
        description="Finds order of songs when mixed.",
        help='!mixorder grgr grgr grgr "cyber cyber"',
    )
    async def mix_order(self, ctx: commands.Context, a: str, b: str, c: str, d: str):
        songs = []
        for name in [a, b, c, d]:
            song = self.bot.master_filters.music.get(name, ctx)
            if not song:
                await ctx.send(
                    f'Unknown song "{name}".', allowed_mentions=AllowedMentions.none()
                )
                return
            if not song.mix_info:
                await ctx.send(f'Song "{song.name}" does not have mix enabled.')
                return
            songs.append(song)

        mix = get_best_mix(songs)
        mix_data = get_mix_data(mix)
        nl = "\n"
        embed = discord.Embed(
            title="Mix Order",
            description=f'```{nl.join(f"{i}. {self.format_song_title(song)}" for i, song in enumerate(mix, 1))}\n\n'
            f"Total Duration: {sum(md.duration for md in mix_data):.2f}s```",
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="mix",
        aliases=[],
        description="Creates a custom mix.",
        help='!mix grgr hard cyber hard puransu expert "cats eye" easy',
    )
    async def mix(
        self,
        ctx: commands.Context,
        a: str,
        a_diff: str,
        b: str,
        b_diff: str,
        c: str,
        c_diff: str,
        d: str,
        d_diff: str,
    ):
        names = [a, b, c, d]
        diff_names = [a_diff, b_diff, c_diff, d_diff]

        songs = []
        for name in names:
            song = self.bot.master_filters.music.get(name, ctx)
            if not song:
                await ctx.send(
                    f'Unknown song "{name}".', allowed_mentions=AllowedMentions.none()
                )
                return
            if not song.mix_info:
                await ctx.send(f'Song "{song.name}" does not have mix enabled.')
                return
            songs.append(song)
        diffs = []
        for diff_name in diff_names:
            diff = self.difficulty_names.get(diff_name.lower())
            if not diff:
                await ctx.send(
                    f'Unknown difficulty "{diff_name}".',
                    allowed_mentions=AllowedMentions.none(),
                )
                return
            diffs.append(diff)

        mix = Chart.create_mix(songs, diffs)
        mix_image = await self.bot.loop.run_in_executor(
            self.bot.thread_pool, mix.render
        )
        mix_name = "\n".join(
            f"{song.name} [{diff.name}]" for song, diff in zip(songs, diffs)
        )
        note_counts = mix.get_note_counts()

        now = datetime.datetime.now()
        self.custom_mixes = {
            k: v
            for k, v in self.custom_mixes.items()
            if (now - v.create_time).total_seconds() < self.CUSTOM_MIX_MIN_LIFETIME
        }
        self.custom_mixes[ctx.author.id] = CustomMixData(mix_name, mix, now)

        buffer = BytesIO()
        mix_image.save(buffer, "png")
        buffer.seek(0)

        embed = discord.Embed(title="Custom Mix")
        embed.add_field(name="Songs", value=mix_name, inline=False)
        embed.add_field(
            name="Info",
            value=f"Duration: {self.format_duration(mix.info.end_time - mix.info.start_time)}\n"
            f"Level: {mix.info.level}\n"
            f"Ordered: {all(a == b for a, b in zip(get_best_mix(songs), songs))}\n"
            f'Skills: {", ".join("{:.2f}s".format(t - mix.info.start_time) if t not in mix.info.base_skill_times else "[{:.2f}s]".format(t - mix.info.start_time) for t in mix.info.skill_times)}\n'
            f"Fever: {mix.info.fever_start - mix.info.start_time:.2f}s - {mix.info.fever_end - mix.info.start_time:.2f}s\n"
            f'Transitions: {", ".join("{:.2f}s".format(t - mix.info.start_time) for t in mix.info.medley_transition_times)}',
            inline=False,
        )
        embed.add_field(
            name="Combo",
            value=f"Max Combo: {len(mix.notes)}\n"
            f'Taps: {note_counts["tap"]} (dark: {note_counts["tap1"]}, light: {note_counts["tap2"]})\n'
            f'Scratches: {note_counts["scratch"]} (left: {note_counts["scratch_left"]}, right: {note_counts["scratch_right"]})\n'
            f'Stops: {note_counts["stop"]} (head: {note_counts["stop_start"]}, tail: {note_counts["stop_end"]})\n'
            f'Long: {note_counts["long"]} (head: {note_counts["long_start"]}, tail: {note_counts["long_end"]})\n'
            f'Slide: {note_counts["slide"]} (tick: {note_counts["slide_tick"]}, flick {note_counts["slide_flick"]})',
            inline=True,
        )
        embed.set_image(url="attachment://mix.png")

        await ctx.send(embed=embed, file=discord.File(fp=buffer, filename="mix.png"))

    @commands.command(
        name="mixrating",
        aliases=["mix_rating"],
        description="Returns the rating of a mix. Used internally.",
        help='!mixrating grgr grgr grgr "cyber cyber"',
        hidden=True,
    )
    async def mixrating(self, ctx: commands.Context, a: str, b: str, c: str, d: str):
        songs = []
        for name in [a, b, c, d]:
            song = self.bot.master_filters.music.get(name, ctx)
            if not song:
                await ctx.send(f'Unknown song "{name}".')
                return
            songs.append(song)

        rating = calculate_mix_rating(songs)

        nl = "\n"
        embed = discord.Embed(
            title="Mix Rating",
            description=f'```{nl.join(f"{i}. {self.format_song_title(song)}" for i, song in enumerate(songs, 1))}\n\n'
            f"Rating: {rating}```",
        )
        await ctx.send(embed=embed)

    @staticmethod
    def format_song_title(song):
        return f'{song.name}{" (" + song.special_unit_name + ")" if song.special_unit_name else ""}{" (Hidden)" if song.is_hidden else ""}'

    @staticmethod
    def format_duration(seconds):
        minutes = int(seconds // 60)
        seconds = round(seconds % 60, 2)
        return f"{minutes}:{str(int(seconds)).zfill(2)}.{str(int(seconds % 1 * 100)).zfill(2)}"


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
            self.Unit: music.unit.name
            if not music.special_unit_name
            else f"{music.unit.name} ({music.special_unit_name})",
            self.Level: music.charts[4].display_level
            if len(music.charts) == 4
            else "0",
            self.Duration: music.duration,
            self.Date: music.start_datetime,
            self.BPM: music.bpm,
            self.Combo: music.charts[4].note_counts[0].count
            if 4 in music.charts
            else 0,
        }[self]

    def get_formatted_from_music(self, music: MusicMaster):
        return {
            self.DefaultOrder: None,
            self.Name: None,
            self.Id: str(music.id).zfill(7),
            self.Unit: music.unit.name
            if not music.special_unit_name
            else f"{music.unit.name} ({music.special_unit_name})",
            self.Level: (
                music.charts[4].display_level if len(music.charts) == 4 else "?"
            ).ljust(3),
            self.Duration: Music.format_duration(music.duration),
            self.Date: str(music.start_datetime.date()),
            self.BPM: f"{music.bpm:>5.2f}",
            self.Combo: str(music.charts[4].note_counts[0].count)
            if 4 in music.charts
            else "?",
        }[self]


music_attribute_aliases = {
    "default": MusicAttribute.DefaultOrder,
    "name": MusicAttribute.Name,
    "id": MusicAttribute.Id,
    "relevance": MusicAttribute.Name,
    "unit": MusicAttribute.Unit,
    "level": MusicAttribute.Level,
    "difficulty": MusicAttribute.Level,
    "diff": MusicAttribute.Level,
    "duration": MusicAttribute.Duration,
    "length": MusicAttribute.Duration,
    "date": MusicAttribute.Date,
    "bpm": MusicAttribute.BPM,
    "combo": MusicAttribute.Combo,
}


@dataclass
class CustomMixData:
    name: str
    chart: Chart
    create_time: datetime.datetime


async def setup(bot):
    await bot.add_cog(Music(bot))
