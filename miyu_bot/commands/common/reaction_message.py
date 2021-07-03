import asyncio
from typing import List, Callable, Awaitable, Union, Tuple, Dict, Optional

import discord
from discord import Message, Embed, Emoji, PartialEmoji, RawReactionActionEvent
from discord.ext.commands import Context

AnyEmoji = Union[str, Emoji, PartialEmoji]


async def run_tabbed_message(ctx: Context, emojis: List[AnyEmoji], embeds: List[Embed], files=None, starting_index=0,
                             timeout=600):
    if len(emojis) != len(embeds):
        raise ValueError('Emojis and embeds must have the same number of elements.')

    last_emoji = emojis[starting_index]

    async def callback(view: discord.ui.View,
                       interaction: discord.Interaction,
                       emoji,
                       buttons: Dict[AnyEmoji, EmojiButton]):
        nonlocal last_emoji
        buttons[last_emoji].disabled = False
        last_emoji = emoji
        buttons[emoji].disabled = True
        await interaction.response.edit_message(embed=embeds[emojis.index(emoji)], view=view)

    disabled = [False] * len(emojis)
    disabled[starting_index] = True

    await ctx.send(embed=embeds[starting_index],
                   files=files or [],
                   view=ReactionButtonView(emojis,
                                           callback,
                                           allowed_users={ctx.bot.owner_id, ctx.author.id, *ctx.bot.owner_ids},
                                           disabled=disabled,
                                           timeout=timeout))


async def run_dynamically_paged_message(ctx: Context, embed_generator: Callable[[int], discord.Embed], timeout=600):
    left_arrow = '<:prev:860683672382603294>'
    right_arrow = '<:next:860683672402526238>'
    arrows = [left_arrow, right_arrow]

    message = await ctx.send(embed=embed_generator(0))

    async def callback(emoji):
        if emoji == left_arrow:
            new_embed = embed_generator(-1)
        elif emoji == right_arrow:
            new_embed = embed_generator(1)
        else:
            return

        if new_embed:
            await message.edit(embed=new_embed)

    await run_reaction_message(ctx, message, arrows, callback, timeout)


async def run_paged_message(ctx: Context, base_embed: discord.Embed, content: List[str], page_size: int = 15,
                            header='', numbered: bool = True, timeout=600, max_tabbed_pages=-1, start_page: int = 0,
                            files=None):
    if header:
        header = f'`{header}`\n'

    if max_tabbed_pages > 9:
        raise ValueError('max_tabbed_pages must be 9 or less.')

    if not content:
        embed = base_embed.copy().set_footer(text='Page 0/0')
        await run_deletable_message(ctx, embed=embed, timeout=timeout)
        return

    page_contents = [content[i:i + page_size] for i in range(0, len(content), page_size)]

    item_number = 0
    max_item_number_length = len(str(len(content)))

    def format_item(item):
        nonlocal item_number
        item_number += 1
        if numbered:
            return f'`{item_number}.{" " * (max_item_number_length - len(str(item_number)))} {item}`'
        else:
            return f'`{item}`'

    embeds = [
        base_embed.from_dict({
            **base_embed.to_dict(),
            'description': header + '\n'.join((format_item(i) for i in page)),
        }).set_footer(text=f'Page {i + 1}/{len(page_contents)}')
        for i, page in enumerate(page_contents)]

    if len(embeds) <= max_tabbed_pages:
        reaction_emoji = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
        await run_tabbed_message(ctx, reaction_emoji[:len(embeds)], embeds, starting_index=start_page, timeout=timeout)
    else:
        double_left_arrow = '<:first:860679908258873344>'
        double_right_arrow = '<:last:860679908426514465>'
        left_arrow = '<:prev:860683672382603294>'
        right_arrow = '<:next:860683672402526238>'

        arrows = [double_left_arrow, left_arrow, right_arrow, double_right_arrow]

        index = start_page

        async def callback(view: discord.ui.View,
                           interaction: discord.Interaction,
                           emoji,
                           buttons: Dict[AnyEmoji, EmojiButton]):
            nonlocal index

            if emoji == double_left_arrow:
                index = 0
            elif emoji == left_arrow:
                index -= 1
            elif emoji == right_arrow:
                index += 1
            elif emoji == double_right_arrow:
                index = len(embeds) - 1
            index = min(len(embeds) - 1, max(0, index))

            disable_left = index == 0
            buttons[left_arrow].disabled = disable_left
            buttons[double_left_arrow].disabled = disable_left
            disable_right = index == len(embeds) - 1
            buttons[right_arrow].disabled = disable_right
            buttons[double_right_arrow].disabled = disable_right

            await interaction.response.edit_message(embed=embeds[index], view=view)

        is_single_page = len(embeds) <= 1

        await ctx.send(embed=embeds[start_page],
                       files=files or [],
                       view=ReactionButtonView(arrows,
                                               callback,
                                               allowed_users={ctx.bot.owner_id, ctx.author.id, *ctx.bot.owner_ids},
                                               disabled=[True, True, is_single_page, is_single_page],
                                               timeout=timeout))


async def run_deletable_message(ctx: Context,
                                content: Optional[str] = None,
                                embed: Optional[discord.Embed] = None,
                                files: Optional[List] = None,
                                timeout=600):
    async def callback(*_):
        pass

    await ctx.send(content=content,
                   embed=embed,
                   files=files or [],
                   view=ReactionButtonView([],
                                           callback,
                                           allowed_users={ctx.bot.owner_id, ctx.author.id, *ctx.bot.owner_ids},
                                           timeout=timeout))


async def _noop(n):
    return None


class CloseButton(discord.ui.Button):
    def __init__(self, row, allowed_users):
        self.allowed_users = allowed_users
        super(CloseButton, self).__init__(style=discord.ButtonStyle.danger, emoji='<:close:860679908157030430>', row=row)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id not in self.allowed_users:
            await interaction.response.send_message('This is not your message.', ephemeral=True)
            return
        await interaction.message.delete()


class EmojiButton(discord.ui.Button):
    def __init__(self, emoji, row, disabled, style, callback, allowed_users):
        self.allowed_users = allowed_users
        self.original_emoji = emoji
        super(EmojiButton, self).__init__(style=style, emoji=emoji, row=row, disabled=disabled,)
        self._callback = callback

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id not in self.allowed_users:
            await interaction.response.send_message('This is not your message.', ephemeral=True)
            return
        await self._callback(self.view, interaction, self.original_emoji, self.view.buttons)


class ReactionButtonView(discord.ui.View):
    def __init__(self,
                 emojis: List[Union[AnyEmoji, Tuple[AnyEmoji, int]]],
                 callback: Callable[[discord.ui.View, discord.Interaction, AnyEmoji, Dict[AnyEmoji, EmojiButton]],
                                    Awaitable[None]],
                 allowed_users: set,
                 rows: Optional[List[int]] = None,
                 disabled: Optional[List[bool]] = None,
                 styles: Optional[List[discord.ButtonStyle]] = None,
                 close_button_row: int = 0,
                 timeout=600):
        super(ReactionButtonView, self).__init__(timeout=timeout)
        buttons = {}
        for i, emoji in enumerate(emojis):
            if rows:
                row = rows[i]
            else:
                row = 0
            if disabled:
                disable = disabled[i]
            else:
                disable = False
            if styles:
                style = styles[i]
            else:
                style = discord.ButtonStyle.secondary
            button = EmojiButton(emoji, row, disable, style, callback, allowed_users)
            self.add_item(button)
            buttons[emoji] = button
        self.buttons = buttons
        self.add_item(CloseButton(row=close_button_row, allowed_users=allowed_users))


async def run_reaction_message(ctx: Context, message: Message, emojis: List[AnyEmoji],
                               callback: Callable[[AnyEmoji], Awaitable[None]], timeout=600):
    emojis.append('❎')
    for emoji in emojis:
        await message.add_reaction(emoji)

    def check(ev: RawReactionActionEvent):
        return ev.message_id == message.id and ev.user_id in {ctx.bot.owner_id, ctx.author.id, *ctx.bot.owner_ids}

    while True:
        try:
            tasks = [
                asyncio.create_task(ctx.bot.wait_for('raw_reaction_add', check=check)),
                asyncio.create_task(ctx.bot.wait_for('raw_reaction_remove', check=check))
            ]
            done, pending = await asyncio.wait(tasks, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()

            if len(done) == 0:
                raise asyncio.TimeoutError()

            emoji = done.pop().result().emoji

            if emoji.id:
                emoji = ctx.bot.get_emoji(emoji.id) or emoji
            elif emoji.name:
                emoji = emoji.name

            if emoji == '❎':
                await message.delete()
                break

            await callback(emoji)
        except asyncio.TimeoutError:
            try:
                await message.clear_reactions()
            except discord.Forbidden:
                for emoji in emojis:
                    await message.remove_reaction(emoji, ctx.bot.user)
            break
