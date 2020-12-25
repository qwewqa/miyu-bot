import asyncio
from typing import List, Callable, Awaitable

from discord import Message, Embed, Emoji
from discord.ext.commands import Context


async def make_tabbed_message(ctx: Context, message: Message, emoji_ids: List[int], embeds: List[Embed], timeout=300):
    emoji_ids = list(emoji_ids)

    async def callback(emoji_id, _ctx, _message):
        await message.edit(embed=embeds[emoji_ids.index(emoji_id)])

    await make_reaction_message(ctx, message, emoji_ids, callback, timeout)


async def make_reaction_message(ctx: Context, message: Message, emoji_ids: List[int],
                                callback: Callable[[int, Context, Message], Awaitable[None]], timeout=300):
    for emoji_id in emoji_ids:
        await message.add_reaction(ctx.bot.get_emoji(emoji_id))

    def check(rxn, usr):
        return usr == ctx.author and rxn.emoji.id in emoji_ids and rxn.message.id == message.id

    while True:
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout, check=check)
            await callback(reaction.emoji.id, ctx, message)
            await message.remove_reaction(reaction, user)
        except asyncio.TimeoutError:
            for emoji_id in emoji_ids:
                await message.remove_reaction(ctx.bot.get_emoji(emoji_id), ctx.bot.user)
            break
