from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from miyu_bot.commands.master_filter.card_filter import CardFilter

_MODULES = {
    'miyu_bot.commands.master_filter.card_filter': [('CardFilter', 'card_master', 'card_filter')],
    'miyu_bot.commands.master_filter.gacha_filter': [('GachaFilter', 'gacha_master', 'gacha_filter')]
}


class MasterFilterManager:
    cards: CardFilter

    def __init__(self, bot):
        self.bot = bot
        self.filters = []
        for module, values in _MODULES.items():
            module = importlib.import_module(module)
            for class_name, master_name, name in values:
                master_filter_class = getattr(module, class_name)
                master_filter = master_filter_class(self.bot, getattr(self.bot.assets, master_name))
                self.filters.append(master_filter)
                setattr(self, name, master_filter)

    def reload(self):
        self.filters.clear()
        for module, values in _MODULES.items():
            module = importlib.import_module(module)
            module = importlib.reload(module)
            for class_name, master_name, name in values:
                master_filter_class = getattr(module, class_name)
                master_filter = master_filter_class(self.bot, getattr(self.bot.assets, master_name))
                self.filters.append(master_filter)
                setattr(self, name, master_filter)
