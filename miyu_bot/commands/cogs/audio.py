import asyncio
import logging
import random
from asyncio import Task
from typing import Dict

import discord
from discord.ext import commands

from miyu_bot.bot.bot import D4DJBot


class Audio(commands.Cog):
    bot: D4DJBot
    tasks: Dict[int, Task]

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

        self.live_audio_paths = [dir for dir in
                                 (self.bot.asset_path / 'plain' / 'voice' / 'ondemand' / 'live').iterdir() if
                                 dir.is_dir()]
        self.tasks = {}

    def cog_unload(self):
        for task in self.tasks.values():
            if not task.cancelled():
                task.cancel()

    @commands.command(name='join',
                      aliases=[],
                      description='Joins VC.',
                      help='!join voice-channel')
    async def join(self, ctx: commands.Context, *, channel: discord.VoiceChannel):
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()

    @commands.command(name='leave',
                      aliases=[],
                      description='Leaves VC.',
                      help='!leave')
    async def leave(self, ctx: commands.Context):
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
            self.stop_task(ctx)

    @commands.command(name='stop',
                      aliases=[],
                      description='Stops playing audio.',
                      help='!leave')
    async def stop(self, ctx: commands.Context):
        self.stop_task(ctx)
        if ctx.voice_client is not None:
            ctx.voice_client.stop()

    @commands.command(name='play',
                      aliases=[],
                      description='Plays audio.',
                      help='!play')
    async def play(self, ctx: commands.Context):
        self.tasks[ctx.guild.id] = asyncio.create_task(self.play_live_audio(ctx))

    async def play_live_audio(self, ctx):
        queue = []
        event = asyncio.Event()

        def after(_err):
            event.set()

        while True:
            if not queue:
                interaction = random.choice(self.live_audio_paths)
                queue.extend([a for a in interaction.iterdir() if a.suffix == '.wav'][::-1])
                await asyncio.sleep(random.randint(8, 12))
            else:
                await asyncio.sleep(0.5)
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(queue.pop()))
            source.volume = 0.8
            ctx.voice_client.play(source, after=after)
            await event.wait()
            event.clear()

    def stop_task(self, ctx):
        if ctx.guild.id in self.tasks:
            if not (task := self.tasks[ctx.guild.id]).cancelled():
                task.cancel()

    @play.before_invoke
    async def ensure_voice(self, ctx: commands.Context):
        self.stop_task(ctx)
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


def setup(bot):
    bot.add_cog(Audio(bot))
