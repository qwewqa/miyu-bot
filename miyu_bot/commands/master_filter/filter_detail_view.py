from typing import List, Optional, TYPE_CHECKING, Union, Callable, Coroutine

import discord
from discord import Interaction
from discord.ui import Button

from miyu_bot.bot.models import log_usage
from miyu_bot.bot.servers import Server
from miyu_bot.commands.common.deletable_message import DeleteButton
from miyu_bot.commands.common.paged_message import PageChangeButton
from miyu_bot.commands.common.user_restricted_view import UserRestrictedView

if TYPE_CHECKING:
    from miyu_bot.commands.master_filter.master_filter import EmbedSourceCallable


class DetailTabButton(discord.ui.Button['FilterDetailView']):
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


class DetailServerChangeButton(discord.ui.Button['FilterDetailView']):
    def __init__(self,
                 style=discord.ButtonStyle.secondary,
                 emoji='<:globe:860687306889494569>',
                 **kwargs):
        super(DetailServerChangeButton, self).__init__(style=style, emoji=emoji, **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        self.view.target_server_index += 1
        await interaction.message.edit(embed=self.view.active_embed, view=self.view)
        await interaction.response.send_message(f'Target server set to {self.view.target_server.name}.',
                                                ephemeral=True)
        await log_usage('filter_detail_server_change_button')


class DetailToListButton(discord.ui.Button['FilterDetailView']):
    def __init__(self,
                 style=discord.ButtonStyle.secondary,
                 emoji='<:list:861762364764061727> ',
                 **kwargs):
        super(DetailToListButton, self).__init__(style=style, emoji=emoji, **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view, embed = self.view.manager.get_list_view(self.view.page_index)
        await interaction.response.edit_message(embed=embed, view=view)
        self.view.stop()
        await log_usage('filter_detail_to_list_button')


class ShortcutButton(discord.ui.Button['FilterDetailView']):
    def __init__(self,
                 emoji: Union[str, discord.Emoji],
                 function: Callable,
                 check: Callable,
                 style=discord.ButtonStyle.success,
                 **kwargs):
        self.function = function
        self.check = check
        super(ShortcutButton, self).__init__(style=style, emoji=emoji, **kwargs)

    async def callback(self, interaction: Interaction):
        view = self.view
        await self.function(view.master_filter, view.ctx, view.values[view.page_index], view.target_server, interaction)
        await log_usage('filter_detail_shortcut_button')


class FilterDetailView(UserRestrictedView):
    def __init__(self,
                 manager,
                 master_filter,
                 ctx,
                 values: List,
                 source: 'EmbedSourceCallable',
                 shortcut_buttons: List,
                 *,
                 start_index: int = 0,
                 tabs: Optional[List] = None,
                 start_tab: Optional[int] = None,
                 start_target_server: Optional[Server] = None,
                 **kwargs):
        super(FilterDetailView, self).__init__(**kwargs)
        self.manager = manager
        self.master_filter = master_filter
        self.ctx = ctx
        self.values = values
        self.servers = list(Server)
        if start_target_server is not None:
            self._target_server_index = self.servers.index(start_target_server)
        else:
            self._target_server_index = self.servers.index(ctx.preferences.server)
        self.fallback_server = ctx.preferences.server
        self.source = source if tabs is not None else self.wrap_tabless_source(source)
        self._page_index = start_index
        self.max_page_index = len(values) - 1
        self._tab = start_tab
        self.active_embed = self.source(master_filter, ctx, values[self.page_index], start_tab, ctx.preferences.server)

        self.tab_buttons = []
        if tabs is not None:
            for i, tab_emoji in enumerate(tabs):
                tab_button = DetailTabButton(i, emoji=tab_emoji, row=0)
                self.tab_buttons.append(tab_button)
                self.add_item(tab_button)

        row_offset = 1 if tabs is not None else 0
        self.prev_button = PageChangeButton(-1, log_name='filter_detail_page_change',
                                            emoji='<:prev:860683672382603294>', row=row_offset)
        self.next_button = PageChangeButton(1, log_name='filter_detail_page_change',
                                            emoji='<:next:860683672402526238>', row=row_offset)
        self.add_item(self.prev_button)
        self.add_item(self.next_button)
        self.add_item(DetailServerChangeButton(row=row_offset))
        self.detail_to_list_button = DetailToListButton(row=row_offset)
        self.add_item(self.detail_to_list_button)
        self.add_item(DeleteButton(row=row_offset))
        self.large_decr_button = PageChangeButton(-20, log_name='filter_detail_page_change_extra',
                                                  label='-20', row=row_offset + 1)
        self.small_decr_button = PageChangeButton(-5, log_name='filter_detail_page_change_extra',
                                                  label='-5', row=row_offset + 1)
        self.small_incr_button = PageChangeButton(5, log_name='filter_detail_page_change_extra',
                                                  label='+5', row=row_offset + 1)
        self.large_incr_button = PageChangeButton(20, log_name='filter_detail_page_change_extra',
                                                  label='+20', row=row_offset + 1)
        self.page_display_button = Button(disabled=True, style=discord.ButtonStyle.secondary, row=row_offset + 1)
        self.add_item(self.large_decr_button)
        self.add_item(self.small_decr_button)
        self.add_item(self.small_incr_button)
        self.add_item(self.large_incr_button)
        self.add_item(self.page_display_button)

        self.shortcut_buttons = []
        for shortcut in shortcut_buttons:
            button = ShortcutButton(function=shortcut.function, check=shortcut.check,
                                    label=master_filter.l10n[ctx.preferences.language].format_value(shortcut.name),
                                    emoji=shortcut.emoji, row=3)
            self.shortcut_buttons.append(button)
            self.add_item(button)

        # Run setters
        self.page_index = start_index
        self.tab = start_tab

    @property
    def page_index(self):
        return self._page_index

    @page_index.setter
    def page_index(self, value):
        self._page_index = max(0, min(value, self.max_page_index))
        self.update_embed()
        self.prev_button.disabled = self._page_index == 0
        self.large_decr_button.disabled = self._page_index == 0
        self.small_decr_button.disabled = self._page_index == 0
        self.next_button.disabled = self._page_index == self.max_page_index
        self.large_incr_button.disabled = self._page_index == self.max_page_index
        self.small_incr_button.disabled = self._page_index == self.max_page_index
        self.page_display_button.label = f'{self._page_index + 1}/{self.max_page_index + 1}'

    @property
    def target_server(self):
        return self.servers[self.target_server_index]

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

    def update_embed(self):
        value = self.values[self.page_index]
        target_server = self.target_server
        if target_server_value := self.master_filter.get_by_id(value.id, self.ctx, target_server):
            value = target_server_value
            server = target_server
        else:
            server = self.fallback_server
        self.active_embed = self.source(self.master_filter, self.ctx, value, self.tab, server)
        for shortcut in self.shortcut_buttons:
            shortcut.disabled = not shortcut.check(self.master_filter, value)

    @staticmethod
    def wrap_tabless_source(source: 'EmbedSourceCallable') -> 'EmbedSourceCallable':
        def wrapped(self, ctx, value, tab, server):
            return source(self, ctx, value, server)

        return wrapped
