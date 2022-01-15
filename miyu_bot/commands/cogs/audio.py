import asyncio
import logging
import random
import re
from asyncio import Task, Queue
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Optional, Awaitable, Callable, Iterable, Union

import discord
from discord.ext import commands

from miyu_bot.bot.bot import MiyuBot
from miyu_bot.bot.servers import Server
from miyu_bot.commands.master_filter.localization_manager import LocalizationManager


class Audio(commands.Cog):
    bot: MiyuBot
    queues: 'Dict[int, AudioQueue]'

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.queues = defaultdict(lambda: AudioQueue())
        self.l10n = LocalizationManager(self.bot.fluent_loader, 'audio.ftl')

    def cog_unload(self):
        for queue in self.queues.values():
            queue.stop()

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
            self.queues[ctx.guild.id].stop()
            await ctx.voice_client.disconnect()

    @commands.command(name='stop',
                      aliases=[],
                      description='Stops playing audio.',
                      help='!stop')
    async def stop(self, ctx: commands.Context):
        self.queues[ctx.guild.id].stop()
        if ctx.voice_client:
            await ctx.send('Stopped playback.')

    @commands.group(name='play')
    async def play(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid play subcommand.')

    @play.command(name='volume',
                  description='Adjusts or displays volume.',
                  help='!volume 100')
    async def volume(self, ctx: commands.Context, *, value: Optional[int]):
        if value is None:
            await ctx.send(f'{self.queues[ctx.guild.id].volume * 100:.0f}%')
        else:
            if 0 <= value <= 200:
                self.queues[ctx.guild.id].volume = value / 100
                await ctx.send('Volume changed.')
            else:
                await ctx.send('Volume should be between 0 and 200, inclusive.')

    @play.command(name='file',
                  hidden=True)
    @commands.is_owner()
    async def play_file(self, ctx: commands.Context, *, name: str):
        file = self.bot.assets[Server.JP].path / 'plain' / name
        if not file.exists():
            await ctx.send('Does not exist.')
            return
        self.queues[ctx.guild.id].enqueue(str(file))

    @play.command(name='stamp',
                  aliases=['sticker'],
                  description='Plays stamp audio.',
                  help='!play stamp')
    async def stamp(self, ctx: commands.Context, *, name: str):
        stamp = list(stamp
                     for stamp in self.bot.master_filters.stamps.get_by_relevance(name, ctx)
                     if stamp.audio_path.exists())
        if not stamp:
            await ctx.send('Stamp not found or no audio.')
            return
        stamp = stamp[0]
        self.queues[ctx.guild.id].enqueue(str(stamp.audio_path))

    @play.before_invoke
    async def ensure_voice(self, ctx: commands.Context):
        if ctx.voice_client is None:
            if ctx.author.voice:
                self.queues[ctx.guild.id].start(await ctx.author.voice.channel.connect())
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        else:
            self.queues[ctx.guild.id].start(ctx.voice_client)


@dataclass
class AudioQueue:
    queue: Queue = Queue()
    client: Optional[discord.VoiceClient] = None
    playback_task: Optional[Task] = None
    on_empty_task: Optional[Task] = None
    volume: float = 0.7

    def start(self, client):
        if self.client:
            return
        self.client = client
        self.playback_task = asyncio.create_task(self._playback())

    def stop(self):
        if self.playback_task:
            self.playback_task.cancel()
            self.playback_task = None
        if self.on_empty_task:
            self.on_empty_task.cancel()
            self.on_empty_task = None
        if self.client:
            self.client.stop()
            self.client = None
        self.queue = Queue()

    def set_queue_source(self, source: Callable[[], Awaitable[Union[Iterable[str], str]]]):
        if not self.playback_task:
            raise RuntimeError('Playback not active.')

        if self.on_empty_task:
            self.on_empty_task.cancel()

        async def on_empty():
            while True:
                await self.queue.join()
                next_audio = await source()
                if isinstance(next_audio, Iterable):
                    for audio in next_audio:
                        self.queue.put_nowait(audio)
                else:
                    self.queue.put_nowait(next_audio)

        self.on_empty_task = asyncio.create_task(on_empty())

    def enqueue(self, audio):
        if not self.playback_task:
            raise RuntimeError('Playback not active.')
        self.queue.put_nowait(audio)

    async def _playback(self):
        playback_finished = asyncio.Event()

        def after(_err):
            playback_finished.set()

        while True:
            next_audio = await self.queue.get()
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(next_audio))
            source.volume = self.volume
            self.client.play(source, after=after)
            await playback_finished.wait()
            playback_finished.clear()
            self.queue.task_done()


def setup(bot):
    bot.add_cog(Audio(bot))
