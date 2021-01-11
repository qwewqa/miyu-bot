import asyncio
from typing import List, Callable, Awaitable, Union, Optional

import discord
from discord import Message, Embed, Emoji, PartialEmoji
from discord.ext.commands import Context

AnyEmoji = Union[str, Emoji]


async def run_tabbed_message(ctx: Context, message: Message, emojis: List[Emoji], embeds: List[Embed], timeout=300):
    async def callback(emoji, _ctx, _message):
        await message.edit(embed=embeds[emojis.index(emoji)])

    await run_reaction_message(ctx, message, emojis, callback, timeout)


async def run_paged_message(ctx: Context, title: str, content: List[str], page_size: int = 15, numbered: bool = True,
                            timeout=300, double_arrow_threshold=4):
    if not content:
        embed = discord.Embed(title=title).set_footer(text='Page 0/0')
        await ctx.send(embed=embed)
        return

    page_contents = [content[i:i + page_size] for i in range(0, len(content), page_size)]

    item_number = 0
    max_item_number_length = len(str(len(content)))

    def format_item(item):
        nonlocal item_number
        item_number += 1
        if numbered:
            return f'{item_number}.{" " * (max_item_number_length - len(str(item_number)))} {item}'
        else:
            return str(item)

    embeds = [
        discord.Embed(title=title, description='```' + '\n'.join((format_item(i) for i in page)) + '```').set_footer(
            text=f'Page {i + 1}/{len(page_contents)}')
        for i, page in enumerate(page_contents)]

    message = await ctx.send(embed=embeds[0])

    if len(embeds) == 1:
        return

    double_left_arrow = '⏪'
    double_right_arrow = '⏩'
    left_arrow = '◀'
    right_arrow = '▶'

    if 0 < double_arrow_threshold <= len(embeds):
        arrows = [double_left_arrow, left_arrow, right_arrow, double_right_arrow]
    else:
        arrows = [left_arrow, right_arrow]

    index = 0

    async def callback(emoji, _ctx, _message):
        nonlocal index
        start_index = index
        if emoji == double_left_arrow:
            index = 0
        elif emoji == left_arrow:
            index -= 1
        elif emoji == right_arrow:
            index += 1
        elif emoji == double_right_arrow:
            index = len(embeds) - 1
        index = min(len(embeds) - 1, max(0, index))

        if index != start_index:
            await message.edit(embed=embeds[index])

    await run_reaction_message(ctx, message, arrows, callback, timeout)


async def run_reaction_message(ctx: Context, message: Message, emojis: List[AnyEmoji],
                               callback: Callable[[AnyEmoji, Context, Message], Awaitable[None]], timeout=300):
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
                await message.remove_reaction(emoji, ctx.bot.user)
            break
