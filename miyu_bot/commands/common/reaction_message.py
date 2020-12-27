import asyncio
from typing import List, Callable, Awaitable

import discord
from discord import Message, Embed, Emoji
from discord.ext.commands import Context


async def run_tabbed_message(ctx: Context, message: Message, emojis: List[Emoji], embeds: List[Embed], timeout=300):
    async def callback(emoji, _ctx, _message):
        await message.edit(embed=embeds[emojis.index(emoji)])

    await run_reaction_message(ctx, message, emojis, callback, timeout)


async def run_reaction_message(ctx: Context, message: Message, emojis: List[Emoji],
                               callback: Callable[[Emoji, Context, Message], Awaitable[None]], timeout=300):
    for emoji in emojis:
        await message.add_reaction(emoji)

    def check(rxn, usr):
        return usr == ctx.author and rxn.emoji in emojis and rxn.message.id == message.id

    while True:
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout, check=check)
            await callback(reaction.emoji, ctx, message)
            await message.remove_reaction(reaction, user)
        except asyncio.TimeoutError:
            for emoji in emojis:
                await message.remove_reaction(ctx.bot.get_emoji(emoji), ctx.bot.user)
            break
