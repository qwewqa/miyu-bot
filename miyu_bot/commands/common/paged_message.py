from typing import List, Iterable, Set, Optional, Callable

import discord
from discord import SelectOption, Interaction
from discord.ext.commands import Context

from miyu_bot.commands.common.reaction_message import run_deletable_message, CloseButton


async def run_paged_message(ctx: Context,
                            base_embed: discord.Embed,
                            entries: Iterable[str],
                            page_size: int = 20,
                            *,
                            header='',
                            numbered: bool = True,
                            start_page: int = 0,
                            timeout=600,
                            files=None):
    if not entries:
        embed = base_embed.copy().set_footer(text='Page 0/0')
        await run_deletable_message(ctx, embed=embed, timeout=timeout)
        return

    if header:
        header = f'`{header}`\n'

    entries = [*entries]
    max_item_number_length = len(str(len(entries)))

    def format_entry(number, entry):
        if numbered:
            return f'`{number}.{" " * (max_item_number_length - len(str(number)))} {entry}`'
        else:
            return f'`{entry}`'

    entries = [format_entry(i, entry) for i, entry in enumerate(entries, 1)]
    paged_entries = [entries[i:i + page_size] for i in range(0, len(entries), page_size)]

    embeds = [discord.Embed.from_dict({**base_embed.to_dict(), 'description': header + '\n'.join(page), })
                  .set_footer(text=f'Page {i + 1}/{len(paged_entries)}')
              for i, page in enumerate(paged_entries)]

    page_titles = [f'Page {i + 1}. #{i * 25 + 1}-{i * 25 + len(page)}' for i, page in enumerate(paged_entries)]

    await ctx.send(embed=embeds[start_page],
                   files=files,
                   view=PagedMessageView(embeds,
                                         page_titles=page_titles,
                                         start_index=start_page,
                                         allowed_users={ctx.bot.owner_id, ctx.author.id, *ctx.bot.owner_ids},
                                         timeout=timeout))


class PageChangeButton(discord.ui.Button['PagedMessageView']):
    def __init__(self, change_step: int, style=discord.ButtonStyle.secondary, **kwargs):
        self.change_step = change_step
        super(PageChangeButton, self).__init__(style=style, **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        self.view.page_index += self.change_step
        await interaction.response.edit_message(embed=self.view.active_embed, view=self.view)


class PageSelectPageChangeButton(discord.ui.Button['PagedMessageView']):
    def __init__(self, change_step: int, style=discord.ButtonStyle.secondary, **kwargs):
        self.change_step = change_step
        super(PageSelectPageChangeButton, self).__init__(style=style, **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        self.view.select_page_index += self.change_step
        await interaction.response.edit_message(view=self.view)


class PageSelect(discord.ui.Select['PagedMessageView']):
    async def callback(self, interaction: Interaction):
        assert self.view is not None
        self.view.page_index = int(self.values[0])
        await interaction.response.edit_message(embed=self.view.active_embed, view=self.view)


class PagedMessageView(discord.ui.View):
    def __init__(self,
                 embeds: List[discord.Embed],
                 *,
                 page_titles: Optional[List[str]] = None,
                 start_index: int = 0,
                 allowed_users: Set[int],
                 **kwargs):
        super(PagedMessageView, self).__init__(**kwargs)
        self.embeds = embeds
        self.page_titles = page_titles
        self.max_page_index = len(embeds) - 1
        self.max_select_page_index = len(embeds) // 25
        self.allowed_users = allowed_users
        self.active_embed = embeds[start_index]
        self._page_index = start_index
        self._select_page_index = start_index // 25

        self.first_button = PageChangeButton(-self.max_page_index, emoji='<:first:860679908258873344>', row=0)
        self.prev_button = PageChangeButton(-1, emoji='<:prev:860683672382603294>', row=0)
        self.next_button = PageChangeButton(1, emoji='<:next:860683672402526238>', row=0)
        self.last_button = PageChangeButton(self.max_page_index, emoji='<:last:860679908426514465>', row=0)
        self.add_item(self.first_button)
        self.add_item(self.prev_button)
        self.add_item(self.next_button)
        self.add_item(self.last_button)
        self.add_item(CloseButton(row=0))
        self.page_select = PageSelect(placeholder=self.get_select_placeholder(start_index),
                                      options=self.get_select_options(), row=1)
        self.add_item(self.page_select)
        self.prev_page_select = PageSelectPageChangeButton(-1, emoji='<:prev:860683672382603294>', row=2)
        self.next_page_select = PageSelectPageChangeButton(1, emoji='<:next:860683672402526238>', row=2)
        if self.max_select_page_index > 0:
            self.add_item(self.prev_page_select)
            self.add_item(self.next_page_select)

        # Run setters
        self.page_index = start_index
        self.select_page_index = start_index // 25

    @property
    def page_index(self):
        return self._page_index

    @page_index.setter
    def page_index(self, value):
        self._page_index = max(0, min(value, self.max_page_index))
        self.active_embed = self.embeds[self._page_index]
        self.first_button.disabled = self._page_index == 0
        self.prev_button.disabled = self._page_index == 0
        self.next_button.disabled = self._page_index == self.max_page_index
        self.last_button.disabled = self._page_index == self.max_page_index

    @property
    def select_page_index(self):
        return self._select_page_index

    @select_page_index.setter
    def select_page_index(self, value):
        self._select_page_index = max(0, min(value, self.max_select_page_index))
        self.page_select.options = self.get_select_options()
        self.page_select.placeholder = self.get_select_placeholder(self.select_page_index)
        self.prev_page_select.disabled = self.select_page_index == 0
        self.next_page_select.disabled = self.select_page_index == self.max_select_page_index

    def get_select_placeholder(self, select_page_index: int):
        return f'Pages {select_page_index * 25 + 1}-{min(self.max_page_index + 1, select_page_index * 25 + 25)}'

    def get_select_option_label(self, page_index: int):
        return self.page_titles[page_index] if self.page_titles else f'{page_index + 1}.'

    def get_select_options(self):
        return [SelectOption(label=self.get_select_option_label(i),
                             value=str(i))
                for i in range(self.select_page_index * 25,
                               min(self.max_page_index + 1, self.select_page_index * 25 + 25))]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in self.allowed_users:
            await interaction.response.send_message('This is not your message.', ephemeral=True)
            return False
        return True
