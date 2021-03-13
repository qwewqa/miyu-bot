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

from miyu_bot.bot.bot import D4DJBot


class Audio(commands.Cog):
    bot: D4DJBot
    queues: 'Dict[int, AudioQueue]'

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

        self.live_interaction_paths = [interaction_dir for interaction_dir in
                                       (self.bot.asset_path / 'plain' / 'voice' / 'ondemand' / 'live').iterdir() if
                                       interaction_dir.is_dir() and not interaction_dir.name.startswith('live_general')]
        live_interaction_path_characters = defaultdict(lambda: set())
        live_audio_re = re.compile(r'.*([1-6][1-4])\.hca\.wav')
        for interaction_path in self.live_interaction_paths:
            for path in interaction_path.iterdir():
                if match := live_audio_re.fullmatch(path.name):
                    character_id = int(match.groups()[0])
                    live_interaction_path_characters[interaction_path].add(character_id)
        self.live_interaction_path_characters = live_interaction_path_characters
        self.queues = defaultdict(lambda: AudioQueue())

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

    @play.command(name='stamp',
                  aliases=['sticker'],
                  description='Plays stamp audio.',
                  help='!play stamp')
    async def stamp(self, ctx: commands.Context, *, name: str):
        stamp = list(stamp
                     for stamp in self.bot.asset_filters.stamps.get_sorted(name, ctx)
                     if stamp.audio_path.exists())
        if not stamp:
            await ctx.send('Stamp not found or no audio.')
            return
        stamp = stamp[0]
        print(stamp.quote)
        self.queues[ctx.guild.id].enqueue(str(stamp.audio_path))

    @play.command(name='interactions',
                  aliases=['live', 'interact'],
                  description='Plays live interaction audio.'
                              'Giving one character as an argument restricts to interactions including that character.'
                              'Giving multiple characters as arguments restricts to interactions only including the given characters.',
                  help='!play interactions')
    async def play_interactions(self, ctx: commands.Context, *allowed_characters):
        if allowed_characters:
            allowed_cids = set()
            for character_name in allowed_characters:
                if chr := self.bot.aliases.characters_by_name.get(character_name.lower()):
                    allowed_cids.add(chr.id)
                else:
                    await ctx.send('Unknown character.')
                    return
        else:
            allowed_cids = None

        if source := self.get_live_interaction_audio_source(allowed_cids):
            self.queues[ctx.guild.id].set_queue_source(source)
            await ctx.send('Playing live interactions.')
        else:
            await ctx.send('No results for given filters.')

    def get_live_interaction_audio_source(self, allowed_character_ids):
        if not allowed_character_ids:
            paths = self.live_interaction_paths
        elif len(allowed_character_ids) == 1:
            allowed_character_id = next(iter(allowed_character_ids))
            paths = [p for p in self.live_interaction_paths
                     if allowed_character_id in self.live_interaction_path_characters[p]]
        else:
            paths = [p for p in self.live_interaction_paths
                     if all(cid in allowed_character_ids for cid in self.live_interaction_path_characters[p])]

        if not paths:
            return

        queue = []

        async def source():
            if not queue:
                while not queue:
                    interaction = random.choice(paths)
                    queue.extend([a for a in interaction.iterdir() if a.suffix == '.wav'][::-1])
                await asyncio.sleep(random.randint(8, 12))
            else:
                await asyncio.sleep(0.5)
            return queue.pop()

        return source

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
