import asyncio
import logging
import random
import re
from asyncio import Task
from collections import defaultdict
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

        self.live_interaction_paths = [dir for dir in
                                       (self.bot.asset_path / 'plain' / 'voice' / 'ondemand' / 'live').iterdir() if
                                       dir.is_dir() and not dir.name.startswith('live_general')]
        live_interaction_path_characters = defaultdict(lambda: set())
        live_audio_re = re.compile(r'.*([1-6][1-4])\.hca\.wav')
        for interaction_path in self.live_interaction_paths:
            for path in interaction_path.iterdir():
                if match := live_audio_re.fullmatch(path.name):
                    character_id = int(match.groups()[0])
                    live_interaction_path_characters[interaction_path].add(character_id)
        self.live_interaction_path_characters = live_interaction_path_characters
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
                      description='Plays live interaction audio.'
                                  'Giving one character as an argument restricts to interactions including that character.'
                                  'Giving multiple characters as arguments restricts to interactions only including the given characters.',
                      help='!play')
    async def play(self, ctx: commands.Context, *allowed_characters):
        if allowed_characters:
            allowed_cids = set()
            for character_name in allowed_characters:
                if cid := self.bot.aliases.characters_by_name.get(character_name.lower()).id:
                    allowed_cids.add(cid)
                else:
                    await ctx.send('Unknown character.')
                    return
        else:
            allowed_cids = None
        self.tasks[ctx.guild.id] = asyncio.create_task(self.play_live_audio(ctx, allowed_cids))

    async def play_live_audio(self, ctx, allowed_character_ids):
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
            await ctx.send('No results for given filters.')
            return

        queue = []
        event = asyncio.Event()

        def after(_err):
            event.set()

        while True:
            if not queue:
                interaction = random.choice(paths)
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
