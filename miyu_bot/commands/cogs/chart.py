import logging

import discord
from d4dj_utils.master.chart_master import ChartDifficulty, ChartMaster
from d4dj_utils.master.common_enums import ChartSectionType
from d4dj_utils.master.music_master import MusicMaster
from discord.ext import commands

from main import asset_manager
from miyu_bot.commands.common.fuzzy_matching import romanize, FuzzyMatcher


class Charts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.music = self.get_music()

    def get_music(self):
        music = FuzzyMatcher(lambda m: m.is_released)
        for m in asset_manager.music_master.values():
            music[f'{m.name} {m.special_unit_name}'] = m
        return music

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

    @commands.command()
    async def chart(self, ctx, *, arg):
        self.logger.info(f'Searching for chart "{arg}".')

        arg = arg.strip()

        if not arg:
            await ctx.send('Argument is empty.')
            return

        split_args = arg.split()

        difficulty = ChartDifficulty.Expert
        if len(split_args) >= 2:
            final_word = split_args[-1]
            if final_word in self.difficulty_names:
                difficulty = self.difficulty_names[final_word]
                arg = ''.join(split_args[:-1])

        song: MusicMaster = self.music[arg]
        if not song:
            msg = f'Failed to find chart "{arg}".'
            await ctx.send(msg)
            self.logger.info(msg)
            return
        self.logger.info(f'Found "{song}" ({romanize(song.name)[1]}).')

        chart: ChartMaster = song.charts[difficulty]

        chart_data = chart.load_chart_data()
        note_counts = chart_data.get_note_counts()

        thumb = discord.File(song.jacket_path, filename='jacket.png')
        render = discord.File(chart.image_path, filename='render.png')

        embed = discord.Embed(title=song.name)
        embed.set_thumbnail(url=f'attachment://jacket.png')
        embed.set_image(url=f'attachment://render.png')

        embed.add_field(name='Info',
                        value=f'Difficulty: {chart.display_level} ({chart.difficulty.name})\n'
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
                        inline=True
                        )

        await ctx.send(files=[thumb, render], embed=embed)


def setup(bot):
    bot.add_cog(Charts(bot))
