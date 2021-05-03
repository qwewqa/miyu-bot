import re

import discord
from PIL import ImageColor
from d4dj_utils.master.chart_master import ChartDifficulty
from d4dj_utils.master.common_enums import ChartSectionType
from d4dj_utils.master.music_master import MusicMaster

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
                    reverse_sort=True)
    def date(self, ctx, value: MusicMaster):
        return value.start_datetime

    @date.formatter
    def format_date(self, ctx, value: MusicMaster):
        return f'{value.start_datetime.month:>2}/{value.start_datetime.day:02}/{value.start_datetime.year % 100:02}'

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

    @data_attribute('level',
                    aliases=['difficulty', 'diff'],
                    is_sortable=True,
                    is_comparable=True,
                    reverse_sort=True)
    def level(self, value: MusicMaster):
        if value.chart_levels:
            return max(value.chart_levels)
        else:
            return -1

    @level.formatter
    def format_level(self, value: MusicMaster):
        if value.chart_levels:
            level = max(value.chart_levels)
            if level % 1 != 0:
                return f'{int(level - 0.5):>2}+'
            else:
                return f'{int(level):>2} '
        else:
            return f'N/A'

    @level.compare_converter
    def level_compare_converter(self, s):
        if s[-1] == '+':
            return int(s[:-1]) + 0.5
        else:
            return int(s)

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
                         aliases=['musics'],
                         description='Lists songs.',
                         help='!songs'),
                    default_sort=date,
                    default_display=level,
                    list_name='Song Search')
    def get_song_embed(self, ctx, song: MusicMaster):
        color_code = song.unit.main_color_code
        color = discord.Colour.from_rgb(*ImageColor.getcolor(color_code, 'RGB')) if color_code else discord.Embed.Empty

        embed = discord.Embed(title=song.name, color=color)
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
            'Fair Use': song.can_fair_use,
        }

        embed.add_field(name='Artist',
                        value=format_info(artist_info),
                        inline=False)
        embed.add_field(name='Info',
                        value=format_info(music_info),
                        inline=False)

        embed.set_footer(text=f'Song Id: {song.id:>07}')

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

        embed.add_field(name='Info',
                        value=f'Level: {chart.display_level}\n'
                              f'Duration: {self.format_duration(song.duration)}\n'
                              f'Unit: {song.special_unit_name or song.unit.name}\n'
                              f'Category: {song.category.name}\n'
                              f'BPM: {song.bpm}\n'
                              f'Designer: {chart.designer.name}\n'
                              f'Skills: {", ".join("{:.2f}s".format(t) if t not in chart_data.info.base_skill_times else "[{:.2f}s]".format(t) for t in chart_data.info.skill_times)}\n'
                              f'Fever: {chart_data.info.fever_start:.2f}s - {chart_data.info.fever_end:.2f}s\n',
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
        embed.set_footer(text=f'Chart Id: {chart.id:>08}; 1 column = 10 seconds, 9 second skills')

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
        difficulty = ChartDifficulty(difficulty + 1)

        if difficulty not in song.charts:
            embed = discord.Embed(title=f'Mix: {song.name} [{difficulty.name}]', description='No Data')
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
        embed.set_footer(text=f'Chart Id: {chart.id:>08}; 1 column = 10 seconds')

        return embed

    def format_duration(self, seconds):
        if seconds is None:
            return 'None'
        minutes = int(seconds // 60)
        seconds = round(seconds % 60, 2)
        return f'{minutes}:{str(int(seconds)).zfill(2)}.{str(int(seconds % 1 * 100)).zfill(2)}'
