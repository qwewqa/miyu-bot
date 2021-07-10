from typing import List

import discord.ui
from discord import Interaction, SelectOption

from miyu_bot.bot.models import log_usage
from miyu_bot.commands.common.paged_message import PagedMessageView


class FilterListItemSelect(discord.ui.Select['FilterListView']):
    async def callback(self, interaction: Interaction):
        assert self.view is not None
        index = int(self.values[0])
        view, embed = self.view.manager.get_detail_view(index)
        await interaction.response.send_message(embed=embed, view=view)
        await log_usage('filter_list_item_select')


class FilterListView(PagedMessageView):
    def __init__(self, manager, select_option_details: List, page_size: int, *args, **kwargs):
        self.manager = manager
        self.select_option_details = [(f'{i}. {name[0][:19]}', name[1][:50], name[2])
                                      for i, name in enumerate(select_option_details, 1)]
        self.page_size = page_size
        self.item_select = FilterListItemSelect(placeholder='Details', row=3)
        super(FilterListView, self).__init__(*args, **kwargs)
        self.add_item(self.item_select)

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
