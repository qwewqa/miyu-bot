from typing import TYPE_CHECKING, Tuple, Optional

import discord

from miyu_bot.bot.servers import Server
from miyu_bot.commands.common.deletable_message import DeletableMessageView
from miyu_bot.commands.master_filter.filter_detail_view import FilterDetailView
from miyu_bot.commands.master_filter.filter_list_view import FilterListView

if TYPE_CHECKING:
    from miyu_bot.commands.master_filter.master_filter import MasterFilter


class FilterDisplayManager:
    def __init__(self,
                 master_filter: 'MasterFilter',
                 ctx,
                 results,
                 source,
                 *,
                 page_size: int = 20,
                 target_server: Optional[Server] = None):
        values, index, tab, display = results
        self.master_filter = master_filter
        self.ctx = ctx
        self.l10n = master_filter.l10n
        self.values = values
        self.source = source
        self.page_size = page_size
        self.start_index = index
        self.start_tab = tab
        self.target_server = target_server
        self.allowed_users = {self.ctx.bot.owner_id, self.ctx.author.id, *self.ctx.bot.owner_ids}

        self.tabs = None
        if source.tabs is not None:
            self.tabs = [ctx.bot.get_emoji(e) if isinstance(e, int) else e for e in source.tabs]

        if master_filter.list_formatter:
            if display and display.formatter:
                self.list_entries = [
                    f'{display.formatter(self.master_filter, ctx, value)} {master_filter.list_formatter(self.master_filter, ctx, value)}'
                    for value in values]
            else:
                self.list_entries = [master_filter.list_formatter(self.master_filter, ctx, value) for value in values]
        else:
            self.list_entries = []

        self.base_list_embed = discord.Embed(
            title=f'[{ctx.preferences.server.name}] {self.master_filter.l10n[ctx].format_value(self.master_filter.list_formatter.name or "search")}')

    def get_detail_view(self,
                        start_index: Optional[int] = None,
                        start_tab: Optional[int] = None,
                        target_server: Optional[Server] = None) -> Tuple[discord.ui.View, discord.Embed]:
        if start_index is None:
            start_index = self.start_index
        if start_tab is None:
            start_tab = self.start_tab
        if target_server is None:
            target_server = self.target_server

        if not self.values:
            embed = discord.Embed(title='No Results', description='N/A')
            view = DeletableMessageView(allowed_users=self.allowed_users)
            return view, embed

        view = FilterDetailView(self,
                                self.master_filter,
                                self.ctx,
                                self.values,
                                self.source.embed_source,
                                shortcut_buttons=self.source.shortcut_buttons,
                                start_index=start_index,
                                tabs=self.tabs,
                                start_tab=start_tab,
                                start_target_server=target_server,
                                allowed_users=self.allowed_users)
        return view, view.active_embed

    def get_list_view(self, start_index: Optional[int] = None) -> Tuple[discord.ui.View, discord.Embed]:
        if start_index is None:
            start_index = self.start_index
        start_page = start_index // 20
        entries = self.list_entries
        base_embed = self.base_list_embed
        if not entries:
            embed = base_embed.copy().set_footer(text='Page 0/0')
            view = DeletableMessageView(allowed_users=self.allowed_users)
            return view, embed
        max_item_number_length = len(str(len(entries)))

        def format_entry(number, entry):
            return f'`{number}.{" " * (max_item_number_length - len(str(number)))} {entry}`'

        entries = [format_entry(i, entry) for i, entry in enumerate(entries, 1)]

        paged_entries = [entries[i:i + self.page_size] for i in range(0, len(entries), self.page_size)]

        embeds = [discord.Embed.from_dict({**base_embed.to_dict(), 'description': '\n'.join(page), })
                      .set_footer(text=f'Page {i + 1}/{len(paged_entries)}')
                  for i, page in enumerate(paged_entries)]

        page_titles = [f'Page {i + 1}. #{i * 25 + 1}-{i * 25 + len(page)}' for i, page in enumerate(paged_entries)]

        view = FilterListView(self,
                              select_option_details=[self.master_filter.get_select_name(v) for v in self.values],
                              page_size=self.page_size,
                              embeds=embeds,
                              page_titles=page_titles,
                              start_index=start_page,
                              allowed_users=self.allowed_users)
        return view, view.active_embed
