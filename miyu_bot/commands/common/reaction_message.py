import asyncio
from typing import List, Callable, Awaitable

from discord import Message, Embed
from discord.ext.commands import Context


async def make_tabbed_message(ctx: Context, message: Message, emote_ids: List[int], embeds: List[Embed], timeout=300):
    async def callback(index, _ctx, _message):
        await message.edit(embed=embeds[index])

    await make_reaction_message(ctx, message, emote_ids, callback, timeout)


async def make_reaction_message(ctx: Context, message: Message, emote_ids: List[int],
                                callback: Callable[[int, Context, Message], Awaitable[None]], timeout = 300):
    for emote_id in emote_ids:
        await message.add_reaction(ctx.bot.get_emoji(emote_id))

    def check(rxn, usr):
        return usr == ctx.author and rxn.emoji.id in emote_ids and rxn.message.id == message.id

    while True:
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout, check=check)
            emote_index = emote_ids.index(reaction.emoji.id)
            await callback(emote_index, ctx, message)
            await message.remove_reaction(reaction, user)
        except asyncio.TimeoutError:
            for emote_id in emote_ids:
                await message.remove_reaction(ctx.bot.get_emoji(emote_id), ctx.bot.user)
            break
