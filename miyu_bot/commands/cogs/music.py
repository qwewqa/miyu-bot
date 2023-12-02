import asyncio
import datetime
import enum
import itertools
import logging
import re
from dataclasses import dataclass
from io import BytesIO
from typing import Tuple, List, Optional

import discord
from d4dj_utils.chart.chart import Chart
from d4dj_utils.chart.mix import get_best_mix, get_mix_data, calculate_mix_rating
from d4dj_utils.master.chart_master import ChartDifficulty, ChartMaster
from d4dj_utils.master.music_master import MusicMaster
from d4dj_utils.master.skill_master import SkillMaster
from discord import AllowedMentions, app_commands
from discord.ext import commands

from miyu_bot.bot.bot import MiyuBot, PrefContext
from miyu_bot.bot.servers import Server, SERVER_NAMES
from miyu_bot.commands.common.argument_parsing import ArgumentError
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
        groovy_score_up: app_commands.Range[float, 0, 100] = 0,
        skill_duration_up: app_commands.Range[float, 0, 100] = 0,
        passive_score_up: app_commands.Range[float, 0, 100] = 0,
        general_score_up: app_commands.Range[float, 0, 100] = 0,
        power: app_commands.Range[int, 0, 999999] = 0,
        solo: bool = False,
        auto: bool = False,
        max_level: Optional[str] = None,
        server: Optional[str] = None,
    ):
        """Lists songs by score.

        Parameters
        ----------
        skills: str
            A list of skills. E.g. 80,60,50,40 or 60 or 80x6.75,60x9,50x9,40x9
        groovy_score_up: float
            Groovy score up percentage
        skill_duration_up: float
            Skill duration up percentage
        passive_score_up: float
            Passive score up percentage
        general_score_up: float
            Auto/manual score up percentage
        power: int
            Team power
        solo: bool
            Whether to calculate solo score
        auto: bool
            Whether to calculate auto score
        max_level: str
            The maximum level of songs to include
        server: str
            The server to use. Defaults to the current server. Can be one of: 'jp' or 'en'
        """
        await ctx.defer()

        def make_skill(score, duration):
            return SkillMaster(
                self.bot.assets[Server.JP], score_up_rate=score, max_seconds=duration
            )

        if max_level is None:
            max_level_value = 99999
        else:
            max_level_re = re.compile(r"(\d+)(\+)?")
            match = max_level_re.fullmatch(max_level)
            if not match:
                raise ArgumentError("Invalid max level")
            max_level_value = int(match.group(1)) + (0.5 if match.group(2) else 0)

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
                raise ArgumentError("Invalid skill format")
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
                raise ArgumentError("Invalid skill format")
            if not (0 <= duration <= 20):
                raise ArgumentError("Invalid skill format")
            skill_values.append((score_up, duration))

        # Apply skill duration up
        skill_values = [
            (score_up, duration * (1 + skill_duration_up / 100))
            for score_up, duration in skill_values
        ]

        if not skill_values or len(skill_values) > 4:
            raise ArgumentError("Invalid skill format")

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
                raise ArgumentError("Invalid server name")
            ctx.preferences.server = SERVER_NAMES[server]

        charts: List[ChartMaster] = list(self.bot.master_filters.charts.values(ctx))
        charts = [
            chart
            for chart in charts
            if chart.music.is_available
            and not chart.music.is_hidden
            and chart.music.id > 3
            and chart.level <= max_level_value
        ]

        if not charts:
            raise ArgumentError("No satisfying charts")

        if power:
            relative_display = False
        else:
            relative_display = True
            power = 150_000

        async def score_chart(chart):
            await asyncio.sleep(0)
            total_score = 0
            total_weight = 0
            for skill_perm, weight in weighted_skill_permutations:
                score = self.bot.chart_scorer.score(
                    chart=chart,
                    power=power,
                    skills=skill_perm,
                    fever_score_up=groovy_score_up / 100,
                    enable_fever=not solo,
                    passive_score_up=passive_score_up / 100,
                    auto_score_up=general_score_up / 100,
                    manual_score_up=general_score_up / 100,
                    autoplay=auto,
                )
                total_score += score * weight
                total_weight += weight
            return total_score / total_weight

        chart_scores = {chart: await score_chart(chart) for chart in charts}
        charts = sorted(charts, key=lambda chart: chart_scores[chart], reverse=True)

        if relative_display:
            ref_score = self.reference_chart_score()
            ref_length = 0
        else:
            ref_score = chart_scores[charts[0]]
            ref_length = len(f"{ref_score:,}")

        def format_score(_master_filter, _ctx, chart):
            if relative_display:
                return f"{chart_scores[chart] / ref_score * 100:5.1f}%  {chart.music.duration:>5.1f}s "
            else:
                return f"{int(chart_scores[chart]):>{ref_length},}  {chart.music.duration:>5.1f}s "

        def title():
            sorted_skill_values = sorted(skill_values, reverse=True)
            leader_skill_index = sorted_skill_values.index(leader_skill)
            formatted_skills = " ".join(
                f"{score_up}x{duration:.2f}"
                if i != leader_skill_index
                else f"[{score_up}x{duration:.2f}]"
                for i, (score_up, duration) in enumerate(sorted_skill_values)
            )
            power_text = f"Power: {power:,}\n" if not relative_display else ""
            max_level_text = f"Max Level: {max_level}\n" if max_level else ""
            return f"Song Meta\n{power_text}{max_level_text}Skills: {formatted_skills}\nGroovy Score Up: {groovy_score_up}\nPassive Score Up: {passive_score_up}\nGeneral Score Up: {general_score_up}\nSolo: {solo}\nAuto: {auto}"

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
    )
    @app_commands.choices(
        difficulty=[
            app_commands.Choice(name="Expert", value=int(ChartDifficulty.Expert)),
            app_commands.Choice(name="Hard", value=int(ChartDifficulty.Hard)),
            app_commands.Choice(name="Normal", value=int(ChartDifficulty.Normal)),
            app_commands.Choice(name="Easy", value=int(ChartDifficulty.Easy)),
        ]
    )
    async def score(
        self,
        ctx: PrefContext,
        song: str,
        difficulty: app_commands.Choice[int] = None,
        skills: str = "60",
        groovy_score_up: app_commands.Range[float, 0, 100] = 0,
        skill_duration_up: app_commands.Range[float, 0, 100] = 0,
        passive_score_up: app_commands.Range[float, 0, 100] = 0,
        general_score_up: app_commands.Range[float, 0, 100] = 0,
        power: app_commands.Range[int, 0, 999999] = 0,
        solo: bool = False,
        auto: bool = False,
        server: Optional[str] = None,
    ):
        """Lists songs by score.

        Parameters
        ----------
        song: str
            The song to use. Use 'mix' for mixes.
        difficulty: app_commands.Choice[int]
            The difficulty to use. Defaults to Expert.
            Ignored for mixes.
        skills: str
            A list of skills. E.g. 80,60,50,40 or 60 or 80x6.75,60x9,50x9,40x9
        groovy_score_up: float
            Groovy score up percentage
        skill_duration_up: float
            Skill duration up percentage
        passive_score_up: float
            Passive score up percentage
        general_score_up: float
            Auto/manual score up percentage
        power: int
            Team power
        solo: bool
            Whether to calculate solo score
        auto: bool
            Whether to calculate auto score
        server: str
            The server to use. Defaults to the current server. Can be one of: 'jp' or 'en'
        """
        await ctx.defer()

        if difficulty is None:
            difficulty = app_commands.Choice(
                name="Expert", value=int(ChartDifficulty.Expert)
            )

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
                raise ArgumentError("Invalid skill format")
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
                raise ArgumentError("Invalid skill format")
            if not (0 <= duration <= 20):
                raise ArgumentError("Invalid skill format")
            skill_values.append((score_up, duration))

        # Apply skill duration up
        skill_values = [
            (score_up, duration * (1 + skill_duration_up / 100))
            for score_up, duration in skill_values
        ]

        if not skill_values or len(skill_values) > 4:
            raise ArgumentError("Invalid skill format")

        if len(skill_values) < 4:
            # Pad using last skill/m
            skill_values += [skill_values[-1]] * (4 - len(skill_values))

        leader_skill = skill_values[0]

        skill_permutations = set()
        for perm in itertools.permutations(skill_values):
            skill_permutations.add(perm + (leader_skill,))

        if server is not None:
            server = server.lower()
            if server not in SERVER_NAMES:
                raise ArgumentError("Invalid server name")
            ctx.preferences.server = SERVER_NAMES[server]

        if song.lower() == "mix":
            data = self.custom_mixes.get(ctx.author.id)
            if not data:
                await ctx.send(
                    "No recent user mix found. Use the mix command to create one."
                )
                return
            chart = data.chart
            mode_title = "Mix Score:\n" + data.name
        else:
            music: MusicMaster = self.bot.master_filters.music.get(song, ctx)
            if music is None:
                raise ArgumentError("Invalid song")
            chart = music.charts.get(difficulty.value)
            if chart is None:
                raise ArgumentError("Invalid difficulty")
            mode_title = f"Song Score: {music.name} [{chart.difficulty.name}]"

        if power:
            relative_display = False
        else:
            relative_display = True
            power = 150_000

        scores: List[Tuple[int, List[Tuple[int, float]]]] = []

        for skill_perm in skill_permutations:
            score = self.bot.chart_scorer.score(
                chart=chart,
                power=power,
                skills=[make_skill(*skill) for skill in skill_perm],
                fever_score_up=groovy_score_up / 100,
                enable_fever=not solo,
                passive_score_up=passive_score_up / 100,
                auto_score_up=general_score_up / 100,
                manual_score_up=general_score_up / 100,
                autoplay=auto,
            )
            scores.append((score, skill_perm))

        def format_skill_sequence(skill_sequence: List[Tuple[int, float]]):
            return " ".join(
                f"{score_up:>2}x{duration:.2f}"
                for score_up, duration in skill_sequence[:4]
            )

        def title():
            return f"{mode_title}"

        def body():
            sorted_skill_values = sorted(skill_values, reverse=True)
            leader_skill_index = sorted_skill_values.index(leader_skill)
            formatted_skills = " ".join(
                f"{score_up}x{duration:.2f}"
                if i != leader_skill_index
                else f"[{score_up}x{duration:.2f}]"
                for i, (score_up, duration) in enumerate(sorted_skill_values)
            )
            power_text = f"power: {power:,}\n" if not relative_display else ""
            arg_detail = f"{power_text}skills: {formatted_skills}\ngroovy_score_up: {groovy_score_up}\npassive_score_up: {passive_score_up}\ngeneral_score_up: {general_score_up}\nsolo: {solo}\nauto: {auto}\n"

            if relative_display:
                ref_score = self.reference_chart_score()
                return (
                    "```"
                    + arg_detail
                    + "``` ```"
                    + "\n".join(
                        f"{score / ref_score:.2%} : {format_skill_sequence(skill_perm)}"
                        for score, skill_perm in sorted(scores, reverse=True)
                    )
                    + "```"
                )
            else:
                longest_score = max(score for score, _ in scores)
                score_digits = len(f"{longest_score:,}")
                return (
                    "```"
                    + arg_detail
                    + "``` ```"
                    + "\n".join(
                        f"{score:>{score_digits},} : {format_skill_sequence(skill_perm)}"
                        for score, skill_perm in sorted(scores, reverse=True)
                    )
                    + "```"
                )

        embed = discord.Embed(title=title(), description=body())

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
    async def mix_order(
        self,
        ctx: commands.Context,
        a: str,
        b: str,
        c: str,
        d: str,
        server: Optional[str] = None,
    ):
        if server is not None:
            server = server.lower()
            if server not in SERVER_NAMES:
                raise ArgumentError("Invalid server name")
            ctx.preferences.server = SERVER_NAMES[server]

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
        b: str,
        c: str,
        d: str,
        server: Optional[str] = None,
    ):
        """Creates a custom mix.

        Parameters
        ----------
        a : str
            The first song. E.g. "synchro", "synchro hard", "synchro hd", etc.
        b : str
            The second song.
        c : str
            The third song.
        d : str
            The fourth song.
        """
        await ctx.defer()

        if server is not None:
            server = server.lower()
            if server not in SERVER_NAMES:
                raise ArgumentError("Invalid server name")
            ctx.preferences.server = SERVER_NAMES[server]
            ctx.assets = ctx.bot.assets[ctx.preferences.server]

        def extract_difficulty(name: str) -> Tuple[str, ChartDifficulty]:
            split_args = name.split()

            difficulty = ChartDifficulty.Expert
            if len(split_args) >= 2:
                final_word = split_args[-1].lower()
                if final_word.lower() in self.difficulty_names:
                    difficulty = self.difficulty_names[final_word.lower()]
                    name = name[: -len(final_word) - 1].strip()
            return name, difficulty

        names = []
        diffs = []

        for arg in [a, b, c, d]:
            name, diff = extract_difficulty(arg)
            names.append(name)
            diffs.append(diff)

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

        song_ids = tuple(song.id for song in songs)
        if hidden_mix := next(
            (
                mix.details
                for mix in ctx.assets.hidden_music_mix_master.values()
                if mix.trigger_music_ids == song_ids
            ),
            None,
        ):
            original_mix_masters = [
                song.mix_info[section] for song, section in zip(songs, [1, 2, 2, 3])
            ]
            mix_masters = [
                hidden_mix_details.apply_to(mix_master)
                for hidden_mix_details, mix_master in zip(
                    hidden_mix, original_mix_masters
                )
            ]
            is_hidden_mix = True
        else:
            mix_masters = None
            is_hidden_mix = False

        mix = Chart.create_mix(songs, diffs, mix_masters)
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
            f'Transitions: {", ".join("{:.2f}s".format(t - mix.info.start_time) for t in mix.info.medley_transition_times)}\n'
            f"Special: {is_hidden_mix}",
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
