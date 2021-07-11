from typing import List, Optional, TYPE_CHECKING, Union, Callable, Coroutine, Set

import discord
from discord import Interaction
from discord.ui import Button

from miyu_bot.bot.models import log_usage
from miyu_bot.bot.servers import Server
from miyu_bot.commands.common.deletable_message import DeleteButton
from miyu_bot.commands.common.paged_message import PageChangeButton
from miyu_bot.commands.common.user_restricted_view import UserRestrictedView
from miyu_bot.commands.master_filter import filter_list_view
from miyu_bot.commands.master_filter.filter_result import FilterResults

if TYPE_CHECKING:
    from miyu_bot.commands.master_filter.master_filter import CommandSourceInfo, EmbedSourceCallable, MasterFilter


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


SERVER_EMOJI = {
    Server.JP: '🇯🇵',
    Server.EN: '🇺🇸',  # AmE
}


class DetailServerShortcutButton(discord.ui.Button['FilterDetailView']):
    def __init__(self,
                 server: Server,
                 style=discord.ButtonStyle.secondary,
                 **kwargs):
        self.server = server
        emoji = SERVER_EMOJI[server]
        super(DetailServerShortcutButton, self).__init__(style=style, emoji=emoji, **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        value = self.view.master_filter.get_by_id(self.view.active_value.id, self.view.ctx, self.server)
        if value is None:
            await interaction.response.semd_message('Value not available for server.', ephemeral=True)
            await log_usage('filter_detail_server_shortcut_button')
        view, embed = self.view.master_filter.get_simple_detail_view(self.view.ctx,
                                                                     [value],
                                                                     self.server,
                                                                     self.view.source_info)
        await interaction.response.send_message(embed=embed, view=view)
        await log_usage('filter_detail_server_shortcut_button')


class DetailCommandChangeButton(discord.ui.Button['FilterDetailView']):
    def __init__(self,
                 style=discord.ButtonStyle.secondary,
                 emoji='<:switch:863651880861171733>',
                 **kwargs):
        super(DetailCommandChangeButton, self).__init__(style=style, emoji=emoji, **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        command_sources = self.view.master_filter.command_sources
        new_source = command_sources[(command_sources.index(self.view.source_info) + 1) % len(command_sources)]
        view = FilterDetailView(self.view.master_filter, self.view.ctx, self.view.base_results, source_info=new_source)
        view.page_index = self.view.page_index
        embed = view.active_embed
        await interaction.response.edit_message(embed=embed, view=view)
        self.view.stop()
        await log_usage('filter_detail_command_change_button')


class DetailToListButton(discord.ui.Button['FilterDetailView']):
    def __init__(self,
                 style=discord.ButtonStyle.secondary,
                 emoji='<:list:861762364764061727> ',
                 **kwargs):
        super(DetailToListButton, self).__init__(style=style, emoji=emoji, **kwargs)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view = filter_list_view.FilterListView(self.view.master_filter, self.view.ctx, self.view.base_results)
        view.set_item_index(self.view.page_index)
        embed = view.active_embed
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
        await self.function(view.master_filter, view.ctx, view.values[view.page_index], view.server, interaction)
        await log_usage('filter_detail_shortcut_button')


class FilterDetailView(UserRestrictedView):
    def __init__(self,
                 master_filter: 'MasterFilter',
                 ctx,
                 results: FilterResults,
                 source_info: Optional['CommandSourceInfo'] = None,
                 **kwargs):
        allowed_users = {ctx.bot.owner_id, ctx.author.id, *ctx.bot.owner_ids}
        super(FilterDetailView, self).__init__(allowed_users=allowed_users, **kwargs)
        source_info = source_info or results.command_source_info or master_filter.command_sources[0]
        self.master_filter = master_filter
        self.ctx = ctx
        self.base_results = results
        self.values = results.values
        self.server = results.server
        self.source_info = source_info
        self.embed_source = source_info.embed_source if source_info.tabs is not None else self.wrap_tabless_source(
            source_info.embed_source)
        self._page_index = results.start_index
        self.max_page_index = len(results.values) - 1
        if source_info.tabs is not None:
            # The original results might have been with a source that had different tabs
            if results.start_tab_name in source_info.suffix_tab_aliases:
                self._tab = source_info.suffix_tab_aliases[results.start_tab_name]
            else:
                self._tab = source_info.default_tab
        else:
            self._tab = None
        self.active_embed = self.embed_source(master_filter,
                                              ctx,
                                              self.values[self.page_index],
                                              self.tab,
                                              ctx.preferences.server)

        self.tab_buttons = []
        if (tabs := source_info.tabs) is not None:
            for i, tab_emoji in enumerate(tabs):
                tab_button = DetailTabButton(i, emoji=tab_emoji, row=0)
                self.tab_buttons.append(tab_button)
                self.add_item(tab_button)

        self.prev_button = PageChangeButton(-1, log_name='filter_detail_page_change',
                                            emoji='<:prev:860683672382603294>', row=1)
        self.next_button = PageChangeButton(1, log_name='filter_detail_page_change',
                                            emoji='<:next:860683672402526238>', row=1)
        self.add_item(self.prev_button)
        self.add_item(self.next_button)
        self.detail_to_list_button = DetailToListButton(row=1)
        self.add_item(self.detail_to_list_button)
        self.command_change_button = DetailCommandChangeButton(row=1)
        self.add_item(self.command_change_button)
        if len(master_filter.command_sources) <= 1:
            self.command_change_button.disabled = True
        self.add_item(DeleteButton(row=1))
        self.large_decr_button = PageChangeButton(-20, log_name='filter_detail_page_change_extra',
                                                  label='-20', row=2)
        self.small_decr_button = PageChangeButton(-5, log_name='filter_detail_page_change_extra',
                                                  label='-5', row=2)
        self.small_incr_button = PageChangeButton(5, log_name='filter_detail_page_change_extra',
                                                  label='+5', row=2)
        self.large_incr_button = PageChangeButton(20, log_name='filter_detail_page_change_extra',
                                                  label='+20', row=2)
        self.page_display_button = Button(disabled=True, style=discord.ButtonStyle.secondary, row=2)
        self.add_item(self.large_decr_button)
        self.add_item(self.small_decr_button)
        self.add_item(self.small_incr_button)
        self.add_item(self.large_incr_button)
        self.add_item(self.page_display_button)

        self.server_buttons = []
        for server in SERVER_EMOJI.keys():
            server_button = DetailServerShortcutButton(server=server, row=3)
            self.server_buttons.append(server_button)
            self.add_item(server_button)

        self.shortcut_buttons = []
        for shortcut in source_info.shortcut_buttons:
            button = ShortcutButton(function=shortcut.function, check=shortcut.check,
                                    label=master_filter.l10n[ctx.preferences.language].format_value(shortcut.name),
                                    emoji=shortcut.emoji, row=4)
            self.shortcut_buttons.append(button)
            self.add_item(button)

        # Run setters
        self.page_index = self.page_index
        self.tab = self.tab

    @property
    def active_value(self):
        return self.values[self.page_index]

    @property
    def page_index(self):
        return self._page_index

    @page_index.setter
    def page_index(self, value):
        self._page_index = max(0, min(value, self.max_page_index))
        self.update()

    @property
    def tab(self):
        return self._tab

    @tab.setter
    def tab(self, value):
        if self.tab_buttons:
            self.tab_buttons[self._tab].disabled = False
            self.tab_buttons[value].disabled = True
        self._tab = value
        self.update()

    def server_available(self, server):
        return self.master_filter.get_by_id(self.active_value.id, self.ctx, server) is not None

    def update(self):
        value = self.values[self.page_index]
        self.active_embed = self.embed_source(self.master_filter, self.ctx, value, self.tab, self.server)
        self.prev_button.disabled = self._page_index == 0
        self.large_decr_button.disabled = self._page_index == 0
        self.small_decr_button.disabled = self._page_index == 0
        self.next_button.disabled = self._page_index == self.max_page_index
        self.large_incr_button.disabled = self._page_index == self.max_page_index
        self.small_incr_button.disabled = self._page_index == self.max_page_index
        self.page_display_button.label = f'{self._page_index + 1}/{self.max_page_index + 1}'
        for server_button in self.server_buttons:
            if server_button.server == self.server:
                server_button.style = discord.ButtonStyle.success
                server_button.disabled = True
            else:
                if self.server_available(server_button.server):
                    server_button.style = discord.ButtonStyle.success
                    server_button.disabled = False
                else:
                    server_button.style = discord.ButtonStyle.secondary
                    server_button.disabled = True
        for shortcut_button in self.shortcut_buttons:
            shortcut_button.disabled = not shortcut_button.check(self.master_filter, value)

    @staticmethod
    def wrap_tabless_source(source: 'EmbedSourceCallable') -> 'EmbedSourceCallable':
        def wrapped(self, ctx, value, tab, server):
            return source(self, ctx, value, server)

        return wrapped
