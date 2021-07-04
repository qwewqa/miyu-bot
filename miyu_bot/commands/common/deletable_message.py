from typing import Optional, List

import discord
from discord.ext.commands import Context

from miyu_bot.commands.common.user_restricted_view import UserRestrictedView


async def run_deletable_message(ctx: Context,
                                content: Optional[str] = None,
                                embed: Optional[discord.Embed] = None,
                                files: Optional[List] = None,
                                timeout=600):
    await ctx.send(content=content,
                   embed=embed,
                   files=files or [],
                   view=DeletableMessageView(timeout=timeout,
                                             allowed_users={ctx.bot.owner_id, ctx.author.id, *ctx.bot.owner_ids}))


class DeleteButton(discord.ui.Button):
    def __init__(self,
                 style: discord.ButtonStyle = discord.ButtonStyle.danger,
                 emoji='<:close:860679908157030430>',
                 **kwargs):
        super(DeleteButton, self).__init__(style=style, emoji=emoji, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        await interaction.message.delete()


class DeletableMessageView(UserRestrictedView):
    def __init__(self, **kwargs):
        super(DeletableMessageView, self).__init__(**kwargs)
        self.add_item(DeleteButton())
