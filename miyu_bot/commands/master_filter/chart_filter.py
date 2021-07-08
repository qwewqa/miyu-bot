import asyncio
import re
from datetime import datetime

from d4dj_utils.master.chart_master import ChartMaster, ChartDifficulty
from d4dj_utils.master.skill_master import SkillMaster

from miyu_bot.bot.bot import PrefContext, MiyuBot
from miyu_bot.bot.servers import Server
from miyu_bot.commands.common.emoji import difficulty_emoji_ids
from miyu_bot.commands.master_filter.master_filter import MasterFilter, data_attribute, DataAttributeInfo, \
    command_source


class ChartFilter(MasterFilter[ChartMaster]):
    def __init__(self, bot: MiyuBot, master_name: str, name: str):
        super().__init__(bot, master_name, name)
        self.score_cache = {k: {} for k in self._score_cache_keys}
        self.reference_chart = self.bot.assets[Server.JP].chart_master[3200094]
        self.bot.loop.create_task(self.preload_song_scores())

    def get_name(self, value: ChartMaster) -> str:
        return f'{value.music.name} {value.music.special_unit_name}{" (Hidden)" if value.music.is_hidden else ""} {value.difficulty.name.lower()}'.strip()

    def get_select_name(self, value: ChartMaster):
        return f'{value.difficulty.name}', f'{value.music.name}', None

    def is_released(self, value: ChartMaster) -> bool:
        return value.music.is_released

    difficulty_short_names = {
        ChartDifficulty.Easy: 'ES',
        ChartDifficulty.Normal: 'NM',
        ChartDifficulty.Hard: 'HD',
        ChartDifficulty.Expert: 'EX',
    }

    @data_attribute('name',
                    aliases=['title'],
                    is_sortable=True)
    def name(self, value: ChartMaster):
        return value.music.name

    @data_attribute('date',
                    aliases=['release', 'recent'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def date(self, ctx, value: ChartMaster):
        return ctx.convert_tz(value.music.start_datetime).date()

    @date.formatter
    def format_date(self, ctx, value: ChartMaster):
        dt = ctx.convert_tz(value.music.start_datetime)
        return f'{dt.year % 100:02}/{dt.month:02}/{dt.day:02}'

    @date.compare_converter
    def date_compare_converter(self, ctx: PrefContext, s):
        match = re.fullmatch(r'(\d+)/(\d+)/(\d+)', s)
        if not match:
            raise
        y, m, d = (int(n) for n in match.groups())
        if y < 100:
            y += ctx.localize(datetime.now()).year // 100 * 100
        return ctx.localize(datetime(year=y, month=m, day=d)).date()

    @data_attribute('unit',
                    is_sortable=True,
                    is_tag=True,
                    is_eq=True)
    def unit(self, value: ChartMaster):
        return value.music.unit_id

    @unit.init
    def init_unit(self, info: DataAttributeInfo):
        info.value_mapping = {k: v.id for k, v in self.bot.aliases.units_by_name.items()}

    @data_attribute('id',
                    is_sortable=True,
                    is_comparable=True)
    def id(self, value: ChartMaster):
        return value.music.id

    @id.formatter
    def format_id(self, value: ChartMaster):
        return str(value.music.id).zfill(8)

    @data_attribute('chart_designer',
                    aliases=['chartdesigner', 'designer'],
                    is_sortable=True,
                    is_eq=True)  # Some music have charts with multiple designers
    def chart_designer(self, value: ChartMaster):
        return value.designer.id

    @chart_designer.formatter
    def format_chart_designer(self, value: ChartMaster):
        return value.designer.name

    @chart_designer.init
    def init_chart_designer(self, info):
        self.chart_designers_by_name = {}
        for assets in self.bot.assets.values():
            self.chart_designers_by_name.update({v.name.lower(): k for k, v in assets.chart_designer_master.items()})

    @chart_designer.compare_converter
    def chart_designer_compare_converter(self, s):
        if s.isnumeric():
            return int(s)
        else:
            return self.chart_designers_by_name[s.lower()]

    @data_attribute('difficulty',
                    aliases=['diff'],
                    is_sortable=True,
                    is_comparable=True,
                    is_tag=True,
                    is_keyword=True,
                    value_mapping={
                        'expert': 4,
                        'hard': 3,
                        'normal': 2,
                        'easy': 1,
                        'expt': 4,
                        'norm': 2,
                    },
                    reverse_sort=True)
    def difficulty(self, value: ChartMaster):
        return value.difficulty

    @data_attribute('level',
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def level(self, value: ChartMaster):
        if override_level := re.fullmatch(r'\d+\+?', value.override_level) and value.override_level:
            level = self.level_compare_converter(override_level)
            if level > 99:
                return 0  # Mainly just so April fools doesn't show at the top
            else:
                return level
        return value.level

    # Intentionally not decorated
    # Instead, always included in listing
    def format_level(self, value: ChartMaster):
        if override_level := re.fullmatch(r'\d+\+?', value.override_level) and value.override_level:
            level = self.level_compare_converter(override_level)
        else:
            level = value.level
        if level % 1 != 0:
            return f'{int(level - 0.5):>2}+'
        else:
            return f'{int(level):>2} '

    @level.compare_converter
    def level_compare_converter(self, s):
        if s[-1] == '+':
            return float(s[:-1]) + 0.5
        else:
            return float(s)

    @data_attribute('duration',
                    aliases=['length'],
                    is_sortable=True,
                    is_comparable=True)
    def duration(self, value: ChartMaster):
        return value.music.duration or 0.0

    @duration.formatter
    def format_song_duration(self, value: ChartMaster):
        return f'{value.music.duration:>5.1f}s'

    @duration.compare_converter
    def duration_compare_converter(self, s):
        if match := re.fullmatch(r'(\d+):(\d{1,2}(\.\d+)?)', s):
            groups = match.groups()
            return 60 * int(groups[0]) + float(groups[1])
        else:
            return float(s)

    @data_attribute('bpm',
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def bpm(self, value: ChartMaster):
        return value.music.bpm

    @bpm.formatter
    def format_bpm(self, value: ChartMaster):
        return f'{value.music.bpm:>5.2f}'

    @data_attribute('combo',
                    aliases=['max_combo', 'maxcombo'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def combo(self, value: ChartMaster):
        if ncm := value.note_counts.get(0):
            return ncm.count
        else:
            return -1

    @combo.formatter
    def format_combo(self, value: ChartMaster):
        combo = self.combo(value)
        if combo >= 0:
            return f'{combo:>4}'
        else:
            return ' N/A'

    @data_attribute(name='playable',
                    is_flag=True)
    def playable(self, value: ChartMaster):
        return value.music.is_released and not value.music.is_hidden and value.music.id > 3

    _score_cache_keys = set()

    for _temp_score in [0, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
        for _temp_fever in [True, False]:
            _score_cache_keys.add((_temp_score, _temp_fever))
            _temp_attr_name = f'score{_temp_score}{"solo" if not _temp_fever else ""}'

            @data_attribute(_temp_attr_name,
                            is_sortable=True,
                            reverse_sort=True)
            def _temp_score_attr(self, _ctx, value: ChartMaster, score=_temp_score, fever=_temp_fever):
                return self.get_chart_score(value, score, fever)

            @_temp_score_attr.formatter
            def _temp_format_score_attr(self, _ctx, value: ChartMaster, score=_temp_score, fever=_temp_fever):
                return f'{self.get_chart_score_formatted(value, score, fever)}  {self.format_song_duration(value)} '

            locals()[_temp_attr_name] = _temp_score_attr
            locals()[f'format_{_temp_attr_name}'] = _temp_format_score_attr

            for _temp_menuing_time in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
                _temp_attr_name = f'{_temp_menuing_time}efficiency{_temp_score}{"solo" if not _temp_fever else ""}'

                @data_attribute(_temp_attr_name,
                                aliases=[f'{_temp_menuing_time}eff{_temp_score}{"solo" if not _temp_fever else ""}'],
                                is_sortable=True,
                                reverse_sort=True)
                def _temp_score_attr(self, _ctx, value: ChartMaster, score=_temp_score, fever=_temp_fever,
                                     menuing_time=_temp_menuing_time):
                    return self.get_chart_efficiency(value, score, fever, menuing_time)

                @_temp_score_attr.formatter
                def _temp_format_score_attr(self, _ctx, value: ChartMaster, score=_temp_score, fever=_temp_fever,
                                            menuing_time=_temp_menuing_time):
                    return f'{self.get_chart_efficiency_formatted(value, score, fever, menuing_time)}  {self.format_song_duration(value)} '

                locals()[_temp_attr_name] = _temp_score_attr
                locals()[f'format_{_temp_attr_name}'] = _temp_format_score_attr

    del _temp_attr_name
    del _temp_score_attr
    del _temp_format_score_attr
    del _temp_score
    del _temp_fever
    del _temp_menuing_time

    async def preload_song_scores(self):
        for score, fever in self.score_cache:
            for chart in self.bot.assets[Server.JP].chart_master.values():
                self.get_chart_score(chart, score, fever)
                await asyncio.sleep(0)

    def get_chart_score(self, chart: ChartMaster, score, fever) -> float:
        cache = self.score_cache[(score, fever)]
        if chart.id in cache:
            return cache[chart.id]
        skills = [self.get_dummy_skill(score)] * 5
        score = self.bot.chart_scorer(chart, 150000, skills, fever)
        cache[chart.id] = score
        return score

    def get_chart_score_formatted(self, chart, score, fever):
        ratio = self.get_chart_score(chart, score, fever) / self.get_chart_score(self.reference_chart, score, fever)
        return f'{100 * ratio:>5.1f}%'

    def get_chart_efficiency(self, chart: ChartMaster, score, fever, menuing_time):
        if not chart.music.duration:
            return -1
        return self.get_chart_score(chart, score, fever) / (chart.music.duration + menuing_time)

    def get_chart_efficiency_formatted(self, chart: ChartMaster, score, fever, menuing_time):
        ratio = (self.get_chart_efficiency(chart, score, fever, menuing_time) /
                 self.get_chart_efficiency(self.reference_chart, score, fever, menuing_time))
        return f'{100 * ratio:>5.1f}%'

    def get_dummy_skill(self, score):
        return SkillMaster(
            self.bot.assets[Server.JP],
            id=0,
            min_recovery_value=0,
            max_recovery_value=0,
            combo_support_count=0,
            score_up_rate=score,
            min_seconds=5,
            max_seconds=9,
            perfect_score_up_rate=0,
        )

    @command_source(command_args=None,
                    list_command_args=
                    dict(name='charts',
                         description='Lists charts.',
                         help='!charts'),
                    default_sort=level,
                    list_name='chart-search')
    def get_chart_embed(self, ctx, chart: ChartMaster, server):
        return self.bot.master_filters.music.get_chart_embed(ctx, chart.music, chart.difficulty - 1, server)

    @get_chart_embed.list_formatter
    def format_chart_name(self, chart: ChartMaster):
        song = chart.music
        song_name = f'{song.name}{" (" + song.special_unit_name + ")" if song.special_unit_name else ""}{" (Hidden)" if song.is_hidden else ""}'.strip()
        return f'{self.format_level(chart)}  {self.difficulty_short_names[chart.difficulty]}`{self.bot.get_emoji(difficulty_emoji_ids[chart.difficulty])}`  {song_name}'
