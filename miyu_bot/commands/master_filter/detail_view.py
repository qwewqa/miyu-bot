from typing import List, Tuple, Iterable, Optional, TYPE_CHECKING

import discord
from discord import SelectOption, Interaction

from miyu_bot.bot.servers import Server
from miyu_bot.commands.common.deletable_message import DeleteButton
from miyu_bot.commands.common.paged_message import PageChangeButton, PageSelect, PageSelectPageChangeButton
from miyu_bot.commands.common.user_restricted_view import UserRestrictedView

if TYPE_CHECKING:
    from miyu_bot.commands.master_filter.master_filter import EmbedSourceCallable, AnyEmoji


class DetailTabButton(discord.ui.Button['DetailView']):
    def __init__(self,
                 tab: int,
                 style=discord.ButtonStyle.primary,
                 **kwargs):
        super(DetailTabButton, self).__init__(style=style, **kwargs)
        self.tab = tab

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        self.view.tab = self.tab
        await interaction.response.edit_message(embed=self.view.active_embed, view=self.view)


class DetailServerChangeButton(discord.ui.Button['DetailView']):
    def __init__(self,
                 style=discord.ButtonStyle.secondary,
                 emoji='<:globe:860687306889494569>',
                 **kwargs):
        super(DetailServerChangeButton, self).__init__(style=style, emoji=emoji, **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        self.view.target_server_index += 1
        await interaction.response.edit_message(embed=self.view.active_embed, view=self.view)


class DetailView(UserRestrictedView):
    def __init__(self,
                 master_filter,
                 ctx,
                 values: List,
                 source: 'EmbedSourceCallable',
                 *,
                 select_names: 'Iterable[Tuple[str, str, Optional[AnyEmoji]]]',
                 start_index: int = 0,
                 tabs: Optional[List] = None,
                 start_tab: Optional[int] = None,
                 **kwargs):
        super(DetailView, self).__init__(**kwargs)
        self.master_filter = master_filter
        self.ctx = ctx
        self.values = values
        self.servers = list(Server)
        self._target_server_index = self.servers.index(ctx.preferences.server)
        self.fallback_server = ctx.preferences.server
        self.select_names = [(f'{i}. {name[0][:19]}', name[1][:50], name[2]) for i, name in enumerate(select_names, 1)]
        self.source = source if tabs is not None else self.wrap_tabless_source(source)
        self._page_index = start_index
        self.max_page_index = len(values) - 1
        self._select_page_index = start_index // 25
        self.max_select_page_index = self.max_page_index // 25
        self._tab = start_tab
        self.active_embed = self.source(master_filter, ctx, values[self.page_index], start_tab, ctx.preferences.server)

        self.tab_buttons = []
        if tabs is not None:
            for i, tab_emoji in enumerate(tabs):
                tab_button = DetailTabButton(i, emoji=tab_emoji, row=0)
                self.tab_buttons.append(tab_button)
                self.add_item(tab_button)

        row_offset = 1 if tabs is not None else 0
        self.prev_button = PageChangeButton(-1, emoji='<:prev:860683672382603294>', row=row_offset)
        self.next_button = PageChangeButton(1, emoji='<:next:860683672402526238>', row=row_offset)
        self.add_item(self.prev_button)
        self.add_item(self.next_button)
        self.add_item(DetailServerChangeButton(row=row_offset))
        self.add_item(DeleteButton(row=row_offset))
        self.page_select = PageSelect(placeholder=self.get_select_placeholder(start_index),
                                      options=self.get_select_options(), row=row_offset + 1)
        if len(values) > 1:
            self.add_item(self.page_select)
        self.prev_page_select = PageSelectPageChangeButton(-1, emoji='<:prev:860683672382603294>', row=row_offset + 2)
        self.next_page_select = PageSelectPageChangeButton(1, emoji='<:next:860683672402526238>', row=row_offset + 2)
        if self.max_select_page_index > 0:
            self.add_item(self.prev_page_select)
            self.add_item(self.next_page_select)

        # Run setters
        self.page_index = start_index
        self.select_page_index = start_index // 25
        self.tab = start_tab

    @property
    def page_index(self):
        return self._page_index

    @page_index.setter
    def page_index(self, value):
        self._page_index = max(0, min(value, self.max_page_index))
        self.update_embed()
        self.prev_button.disabled = self._page_index == 0
        self.next_button.disabled = self._page_index == self.max_page_index

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

    @property
    def target_server_index(self):
        return self._target_server_index

    @target_server_index.setter
    def target_server_index(self, value):
        self._target_server_index = value % len(self.servers)
        self.update_embed()

    @property
    def tab(self):
        return self._tab

    @tab.setter
    def tab(self, value):
        if self.tab_buttons:
            self.tab_buttons[self._tab].disabled = False
            self.tab_buttons[value].disabled = True
        self._tab = value
        self.update_embed()

    def get_select_placeholder(self, select_page_index: int):
        return f'Entries {select_page_index * 25 + 1}-{min(self.max_page_index + 1, select_page_index * 25 + 25)}'

    def get_select_options(self):
        return [SelectOption(label=self.select_names[i][0],
                             description=self.select_names[i][1],
                             emoji=self.select_names[i][2],
                             value=str(i))
                for i in range(self.select_page_index * 25,
                               min(self.max_page_index + 1, self.select_page_index * 25 + 25))]

    def update_embed(self):
        value = self.values[self.page_index]
        target_server = self.servers[self.target_server_index]
        if target_server_value := self.master_filter.get_by_id(value.id, self.ctx, target_server):
            value = target_server_value
            server = target_server
        else:
            server = self.fallback_server
        self.active_embed = self.source(self.master_filter, self.ctx, value, self.tab, server)

    @staticmethod
    def wrap_tabless_source(source: 'EmbedSourceCallable') -> 'EmbedSourceCallable':
        def wrapped(self, ctx, value, tab, server):
            return source(self, ctx, value, server)

        return wrapped
