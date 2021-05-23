import re
from datetime import datetime

import discord
from PIL import ImageColor
from d4dj_utils.master.chart_master import ChartDifficulty
from d4dj_utils.master.common_enums import ChartSectionType
from d4dj_utils.master.music_master import MusicMaster
from fluent.runtime.types import fluent_date

from miyu_bot.bot.bot import PrefContext
from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.common.emoji import unit_emoji_ids_by_unit_id, grey_emoji_id, difficulty_emoji_ids
from miyu_bot.commands.common.formatting import format_info
from miyu_bot.commands.master_filter.master_filter import MasterFilter, data_attribute, DataAttributeInfo, \
    command_source


class MusicFilter(MasterFilter[MusicMaster]):
    def get_name(self, value: MusicMaster) -> str:
        return f'{value.name} {value.special_unit_name}{" (Hidden)" if value.is_hidden else ""}'.strip()

    @data_attribute('name',
                    aliases=['title'],
                    is_sortable=True)
    def name(self, value: MusicMaster):
        return value.name

    @data_attribute('date',
                    aliases=['release', 'recent'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def date(self, ctx, value: MusicMaster):
        return ctx.convert_tz(value.start_datetime).date()

    @date.formatter
    def format_date(self, ctx, value: MusicMaster):
        dt = ctx.convert_tz(value.start_datetime)
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
    def unit(self, value: MusicMaster):
        return value.unit_id

    @unit.init
    def init_unit(self, info: DataAttributeInfo):
        info.value_mapping = {k: v.id for k, v in self.bot.aliases.units_by_name.items()}

    @data_attribute('id',
                    is_sortable=True,
                    is_comparable=True)
    def id(self, value: MusicMaster):
        return value.id

    @id.formatter
    def format_id(self, value: MusicMaster):
        return str(value.id).zfill(7)

    @data_attribute('chart_designer',
                    aliases=['chartdesigner', 'designer'],
                    is_sortable=True,
                    is_eq=True,
                    is_plural=True)  # Some music have charts with multiple designers
    def chart_designer(self, value: MusicMaster):
        return {c.designer.id for c in value.charts.values()}

    @chart_designer.formatter
    def format_chart_designer(self, value: MusicMaster):
        return '/'.join({str(c.designer.id): None for c in value.charts.values()}.keys()) or 'None'

    @chart_designer.init
    def init_chart_designer(self, info):
        self.chart_designers_by_name = {v.name.lower(): k for k, v in self.bot.assets.chart_designer_master.items()}

    @chart_designer.compare_converter
    def chart_designer_compare_converter(self, s):
        if s.isnumeric():
            return int(s)
        else:
            return self.chart_designers_by_name[s.lower()]

    @data_attribute('level',
                    aliases=['difficulty', 'diff'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def level(self, value: MusicMaster):
        if override_levels := [self.level_compare_converter(c.override_level)
                               for c in value.charts.values() if re.fullmatch(r'\d+\+?', c.override_level)]:
            level = max(override_levels)
            if level > 99:
                return 0  # Mainly just so April fools doesn't show at the top
            else:
                return level
        if value.chart_levels:
            return max(value.chart_levels)
        else:
            return -1

    @level.formatter
    def format_level(self, value: MusicMaster):
        if value.chart_levels:
            if override_levels := [self.level_compare_converter(c.override_level)
                                   for c in value.charts.values() if re.fullmatch(r'\d+\+?', c.override_level)]:
                level = max(override_levels)
            else:
                level = max(value.chart_levels)
            if level % 1 != 0:
                return f'{int(level - 0.5):>2}+'
            else:
                return f'{int(level):>2} '
        else:
            return f'N/A'

    @data_attribute('expert',
                    aliases=['exp', 'ex'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def expert(self, value: MusicMaster):
        if chart := value.charts.get(4):
            level = chart.level
            if chart.override_level and re.fullmatch(r'\d+\+?', chart.override_level):
                level = self.level_compare_converter(chart.override_level)
            if level > 99:
                return 0
            else:
                return level
        return -1

    @expert.formatter
    def format_expert(self, value: MusicMaster):
        level = self.expert(value)
        if level == -1:
            return 'N/A'
        else:
            if level % 1 != 0:
                return f'{int(level - 0.5):>2}+'
            else:
                return f'{int(level):>2} '

    @data_attribute('hard',
                    aliases=['hrd', 'hd'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def hard(self, value: MusicMaster):
        if chart := value.charts.get(3):
            level = chart.level
            if chart.override_level and re.fullmatch(r'\d+\+?', chart.override_level):
                level = self.level_compare_converter(chart.override_level)
            if level > 99:
                return 0
            else:
                return level
        return -1

    @hard.formatter
    def format_hard(self, value: MusicMaster):
        level = self.hard(value)
        if level == -1:
            return 'N/A'
        else:
            if level % 1 != 0:
                return f'{int(level - 0.5):>2}+'
            else:
                return f'{int(level):>2} '

    @data_attribute('normal',
                    aliases=['norm', 'nrm', 'nm'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def normal(self, value: MusicMaster):
        if chart := value.charts.get(2):
            level = chart.level
            if chart.override_level and re.fullmatch(r'\d+\+?', chart.override_level):
                level = self.level_compare_converter(chart.override_level)
            if level > 99:
                return 0
            else:
                return level
        return -1

    @normal.formatter
    def format_normal(self, value: MusicMaster):
        level = self.normal(value)
        if level == -1:
            return 'N/A'
        else:
            if level % 1 != 0:
                return f'{int(level - 0.5):>2}+'
            else:
                return f'{int(level):>2} '

    @data_attribute('easy',
                    aliases=['esy', 'es'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def easy(self, value: MusicMaster):
        if chart := value.charts.get(1):
            level = chart.level
            if chart.override_level and re.fullmatch(r'\d+\+?', chart.override_level):
                level = self.level_compare_converter(chart.override_level)
            if level > 99:
                return 0
            else:
                return level
        return -1

    @easy.formatter
    def format_easy(self, value: MusicMaster):
        level = self.easy(value)
        if level == -1:
            return 'N/A'
        else:
            if level % 1 != 0:
                return f'{int(level - 0.5):>2}+'
            else:
                return f'{int(level):>2} '

    @level.compare_converter
    @expert.compare_converter
    @hard.compare_converter
    @normal.compare_converter
    @easy.compare_converter
    def level_compare_converter(self, s):
        if s[-1] == '+':
            return float(s[:-1]) + 0.5
        else:
            return float(s)

    @data_attribute('duration',
                    aliases=['length'],
                    is_sortable=True,
                    is_comparable=True)
    def duration(self, value: MusicMaster):
        return value.duration or 0.0

    @duration.formatter
    def format_song_duration(self, value: MusicMaster):
        return self.format_duration(value.duration)

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
    def bpm(self, value: MusicMaster):
        return value.bpm

    @bpm.formatter
    def format_bpm(self, value: MusicMaster):
        return f'{value.bpm:>5.2f}'

    @data_attribute('combo',
                    aliases=['max_combo', 'maxcombo'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def combo(self, value: MusicMaster):
        def get_chart_note_count(c):
            if ncm := c.note_counts.get(0):
                return ncm.count
            else:
                return -1

        if value.charts:
            return max(get_chart_note_count(c) for c in value.charts.values())
        else:
            return -1

    @combo.formatter
    def format_combo(self, value: MusicMaster):
        combo = self.combo(value)
        if combo >= 0:
            return f'{combo:>4}'
        else:
            return ' N/A'

    @command_source(command_args=
                    dict(name='song',
                         aliases=['music'],
                         description='Displays song info.',
                         help='!song grgr'),
                    list_command_args=
                    dict(name='songs',
                         aliases=['musics', 'charts'],
                         description='Lists songs.',
                         help='!songs'),
                    default_sort=date,
                    default_display=level,
                    list_name='song-search')
    def get_song_embed(self, ctx, song: MusicMaster):
        l10n = self.l10n[ctx]

        color_code = song.unit.main_color_code
        color = discord.Colour.from_rgb(*ImageColor.getcolor(color_code, 'RGB')) if color_code else discord.Embed.Empty

        embed = discord.Embed(title=song.name, color=color)
        embed.set_thumbnail(url=self.bot.asset_url + get_asset_filename(song.jacket_path))

        embed.add_field(name=l10n.format_value('artist'),
                        value=l10n.format_value('artist-desc', {
                            'lyricist': song.lyricist,
                            'composer': song.composer,
                            'arranger': song.arranger,
                            'unit-name': song.unit.name,
                            'special-unit-name': song.special_unit_name or 'None',
                        }),
                        inline=False)
        embed.add_field(name=l10n.format_value('info'),
                        value=l10n.format_value('song-info-desc', {
                            'song-category': song.category.name,
                            'duration': self.format_duration(song.duration),
                            'bpm': song.bpm,
                            'section-trend': song.section_trend.name,
                            'sort-order': song.default_order,
                            'levels': ', '.join(c.display_level for c in song.charts.values()),
                            'chart-designers': ', '.join(
                                {f'{c.designer.name} ({c.designer.id})': None for c in song.charts.values()}.keys()),
                            'release-date': fluent_date(ctx.convert_tz(song.start_datetime), dateStyle='medium', timeStyle='medium'),
                            'hidden': song.is_hidden,
                            'fair-use': song.can_fair_use,
                        }),
                        inline=False)

        embed.set_footer(text=l10n.format_value('song-id', {'song-id': f'{song.id:>07}'}))

        return embed

    @get_song_embed.list_formatter
    def format_song_title(self, song):
        return f'`{self.bot.get_emoji(unit_emoji_ids_by_unit_id.get(song.unit_id, grey_emoji_id))}` {song.name}{" (" + song.special_unit_name + ")" if song.special_unit_name else ""}{" (Hidden)" if song.is_hidden else ""}'.strip()

    difficulty_names = {
        'expert': 3,
        'hard': 2,
        'normal': 1,
        'easy': 0,
        'expt': 3,
        'norm': 1,
        'exp': 3,
        'hrd': 2,
        'nrm': 1,
        'esy': 0,
        'ex': 3,
        'hd': 2,
        'nm': 1,
        'es': 0,
    }

    @command_source(command_args=
                    dict(name='chart',
                         description='Displays chart info.',
                         help='!chart grgr'),
                    default_sort=date,
                    tabs=list(difficulty_emoji_ids.values()),
                    default_tab=3,
                    suffix_tab_aliases=difficulty_names)
    def get_chart_embed(self, ctx, song: MusicMaster, difficulty):
        l10n = self.l10n[ctx]

        difficulty = ChartDifficulty(difficulty + 1)

        if difficulty not in song.charts:
            embed = discord.Embed(title=f'{song.name} [{difficulty.name}]', description='No Data')
            embed.set_thumbnail(url=self.bot.asset_url + get_asset_filename(song.jacket_path))
            return embed

        color_code = song.unit.main_color_code
        color = discord.Colour.from_rgb(*ImageColor.getcolor(color_code, 'RGB')) if color_code else discord.Embed.Empty

        chart = song.charts[difficulty]
        embed = discord.Embed(title=f'{song.name} [{chart.difficulty.name}]', color=color)
        embed.set_thumbnail(url=self.bot.asset_url + get_asset_filename(song.jacket_path))
        embed.set_image(url=self.bot.asset_url + get_asset_filename(chart.image_path))
        chart_data = chart.load_chart_data()
        note_counts = chart_data.get_note_counts()

        embed.add_field(name=l10n.format_value('info'),
                        value=l10n.format_value('chart-info-desc', {
                            'level': chart.display_level,
                            'duration': self.format_duration(song.duration),
                            'unit-name': song.special_unit_name or song.unit.name,
                            'song-category': song.category.name,
                            'bpm': song.bpm,
                            'designer': f'{chart.designer.name} ({chart.designer.id})',
                            'skills': ', '.join('{:.2f}s'.format(t) if t not in chart_data.info.base_skill_times else '[{:.2f}s]'.format(t) for t in chart_data.info.skill_times),
                            'fever': f'{chart_data.info.fever_start:.2f}s - {chart_data.info.fever_end:.2f}s'
                        }),
                        inline=False)
        embed.add_field(name=l10n.format_value('combo'),
                        value=l10n.format_value('combo-desc', {
                            'max-combo': chart.note_counts[ChartSectionType.Full].count,
                            **note_counts,
                        }),
                        inline=True)
        embed.add_field(name=l10n.format_value('ratings'),
                        value=f'NTS: {round(chart.trends[0] * 100, 2)}%\n'
                              f'DNG: {round(chart.trends[1] * 100, 2)}%\n'
                              f'SCR: {round(chart.trends[2] * 100, 2)}%\n'
                              f'EFT: {round(chart.trends[3] * 100, 2)}%\n'
                              f'TEC: {round(chart.trends[4] * 100, 2)}%\n',
                        inline=True)
        embed.set_footer(text=l10n.format_value('chart-id', {'chart-id': f'{chart.id:>08}'}))

        return embed

    @command_source(command_args=
                    dict(name='sections',
                         aliases=['mixinfo', 'mix_info'],
                         description='Displays chart mix section info.',
                         help='!sections grgr'),
                    default_sort=date,
                    tabs=list(difficulty_emoji_ids.values()),
                    default_tab=3,
                    suffix_tab_aliases=difficulty_names)
    def get_sections_embed(self, ctx, song: MusicMaster, difficulty):
        l10n = self.l10n[ctx]

        difficulty = ChartDifficulty(difficulty + 1)

        if difficulty not in song.charts:
            embed = discord.Embed(title=f'Mix: {song.name} [{difficulty.name}]', description=l10n.format_value('no-data'))
            embed.set_thumbnail(url=self.bot.asset_url + get_asset_filename(song.jacket_path))
            return embed

        color_code = song.unit.main_color_code
        color = discord.Colour.from_rgb(*ImageColor.getcolor(color_code, 'RGB')) if color_code else discord.Embed.Empty

        chart = song.charts[difficulty]
        embed = discord.Embed(title=f'Mix: {song.name} [{chart.difficulty.name}]', color=color)
        embed.set_thumbnail(url=self.bot.asset_url + get_asset_filename(song.jacket_path))
        embed.set_image(url=self.bot.asset_url + get_asset_filename(chart.mix_path))

        note_counts = chart.note_counts
        mix_info = chart.mix_info

        embed.add_field(name=l10n.format_value('info'),
                        value=l10n.format_value('sections-info-desc', {
                            'level': chart.display_level,
                            'unit-name': song.unit.name,
                            'bpm': song.bpm,
                            'section-trend': song.section_trend.name,
                        }),
                        inline=False)
        embed.add_field(name=l10n.format_value('section-begin'),
                        value=l10n.format_value('section-desc', {
                            'time': f'{round(mix_info[ChartSectionType.Begin].duration, 2)}s',
                            'combo': note_counts[ChartSectionType.Begin].count,
                        }),
                        inline=True)
        embed.add_field(name=l10n.format_value('section-middle'),
                        value=l10n.format_value('section-desc', {
                            'time': f'{round(mix_info[ChartSectionType.Middle].duration, 2)}s',
                            'combo': note_counts[ChartSectionType.Middle].count,
                        }),
                        inline=True)
        embed.add_field(name=l10n.format_value('section-end'),
                        value=l10n.format_value('section-desc', {
                            'time': f'{round(mix_info[ChartSectionType.End].duration, 2)}s',
                            'combo': note_counts[ChartSectionType.End].count,
                        }),
                        inline=True)
        embed.set_footer(text=l10n.format_value('chart-id', {'chart-id': f'{chart.id:>08}'}))

        return embed

    def format_duration(self, seconds):
        if seconds is None:
            return 'None'
        minutes = int(seconds // 60)
        seconds = round(seconds % 60, 2)
        return f'{minutes}:{str(int(seconds)).zfill(2)}.{str(int(seconds % 1 * 100)).zfill(2)}'
