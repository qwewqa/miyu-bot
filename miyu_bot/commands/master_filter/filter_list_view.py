from typing import List, TYPE_CHECKING

import discord.ui
from discord import Interaction, SelectOption

from miyu_bot.bot.bot import PrefContext
from miyu_bot.bot.models import log_usage
from miyu_bot.commands.common.paged_message import PagedMessageView
from miyu_bot.commands.master_filter import filter_detail_view
from miyu_bot.commands.master_filter.filter_result import FilterResults

if TYPE_CHECKING:
    from miyu_bot.commands.master_filter.master_filter import MasterFilter


class FilterListItemSelect(discord.ui.Select['FilterListView']):
    async def callback(self, interaction: Interaction):
        assert self.view is not None
        index = int(self.values[0])
        view = filter_detail_view.FilterDetailView(self.view.master_filter, self.view.ctx, self.view.base_results)
        view.page_index = index
        embed = view.active_embed
        await interaction.response.send_message(embed=embed, view=view)
        await log_usage('filter_list_item_select')


class FilterListView(PagedMessageView):
    def __init__(self,
                 master_filter: 'MasterFilter',
                 ctx: PrefContext,
                 results: FilterResults,
                 *args,
                 **kwargs):
        self.master_filter = master_filter
        self.ctx = ctx
        self.base_results = results
        self.values = results.values
        self.select_option_details = [self.master_filter.get_select_name(v) for v in self.values]
        self.page_size = 20
        base_embed = discord.Embed(
            title=f'[{ctx.preferences.server.name}] {self.master_filter.l10n[ctx].format_value(self.master_filter.list_formatter.name or "search")}',
        )
        display_formatter = results.display_formatter
        if display_formatter:
            entries = [
                f'{display_formatter(self.master_filter, self.ctx, value)} {self.master_filter.list_formatter(self.master_filter, self.ctx, value)}'
                for value in self.values]
        else:
            entries = [self.master_filter.list_formatter(self.master_filter, self.ctx, value) for value in self.values]

        max_item_number_length = len(str(len(entries)))

        def format_entry(number, entry):
            return f'`{number}.{" " * (max_item_number_length - len(str(number)))} {entry}`'

        entries = [format_entry(i, entry) for i, entry in enumerate(entries, 1)]

        paged_entries = [entries[i:i + self.page_size] for i in range(0, len(entries), self.page_size)]

        embeds = [discord.Embed.from_dict({**base_embed.to_dict(), 'description': '\n'.join(page), })
                      .set_footer(text=f'Page {i + 1}/{len(paged_entries)}')
                  for i, page in enumerate(paged_entries)]

        page_titles = [f'Page {i + 1}. #{i * 25 + 1}-{i * 25 + len(page)}' for i, page in enumerate(paged_entries)]

        self.item_select = FilterListItemSelect(placeholder='Details', row=3)
        super(FilterListView, self).__init__(embeds=embeds,
                                             page_titles=page_titles,
                                             allowed_users={self.ctx.bot.owner_id, self.ctx.author.id,
                                                            *self.ctx.bot.owner_ids},
                                             *args,
                                             **kwargs)
        self.add_item(self.item_select)
        self.set_item_index(results.start_index)

    def set_item_index(self, value):
        self.page_index = value // self.page_size

    @PagedMessageView.page_index.setter
    def page_index(self, value):
        PagedMessageView.page_index.fset(self, value)
        self.item_select.options = self.get_item_select_options()

    def get_item_select_options(self):
        return [SelectOption(label=self.select_option_details[i][0],
                             description=self.select_option_details[i][1],
                             emoji=self.select_option_details[i][2],
                             value=str(i))
                for i in range(self.page_index * self.page_size,
                               min(len(self.select_option_details), (self.page_index + 1) * self.page_size))]
