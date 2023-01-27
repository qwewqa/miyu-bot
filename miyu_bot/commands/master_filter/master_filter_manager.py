from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from miyu_bot.commands.master_filter.card_filter import CardFilter
    from miyu_bot.commands.master_filter.event_filter import EventFilter
    from miyu_bot.commands.master_filter.gacha_filter import GachaFilter
    from miyu_bot.commands.master_filter.login_bonus_filter import LoginBonusFilter
    from miyu_bot.commands.master_filter.music_filter import MusicFilter
    from miyu_bot.commands.master_filter.stamp_filter import StampFilter
    from miyu_bot.commands.master_filter.chart_filter import ChartFilter

# The list of modules to import/reload.
# Format is {'module_name': [('class_name', 'master_class_name', 'attribute_name_for_filter_manager', 'name')]}
_MODULES = {
    "miyu_bot.commands.master_filter.card_filter": [
        ("CardFilter", "CardMaster", "cards", "card_filter")
    ],
    "miyu_bot.commands.master_filter.gacha_filter": [
        ("GachaFilter", "GachaMaster", "gacha", "gacha_filter")
    ],
    "miyu_bot.commands.master_filter.event_filter": [
        ("EventFilter", "EventMaster", "events", "event_filter")
    ],
    "miyu_bot.commands.master_filter.music_filter": [
        ("MusicFilter", "MusicMaster", "music", "music_filter")
    ],
    "miyu_bot.commands.master_filter.chart_filter": [
        ("ChartFilter", "ChartMaster", "charts", "chart_filter")
    ],
    "miyu_bot.commands.master_filter.login_bonus_filter": [
        ("LoginBonusFilter", "LoginBonusMaster", "login_bonuses", "login_bonus_filter")
    ],
    "miyu_bot.commands.master_filter.stamp_filter": [
        ("StampFilter", "StampMaster", "stamps", "stamp_filter")
    ],
}


class MasterFilterManager:
    cards: CardFilter
    gacha: GachaFilter
    events: EventFilter
    music: MusicFilter
    login_bonuses: LoginBonusFilter
    stamps: StampFilter
    charts: ChartFilter

    def __init__(self, bot):
        self.bot = bot
        self.filters = []
        for module, values in _MODULES.items():
            module = importlib.import_module(module)
            for class_name, master_name, attribute_name, name in values:
                master_filter_class = getattr(module, class_name)
                master_filter = master_filter_class(self.bot, master_name, name)
                self.filters.append(master_filter)
                setattr(self, attribute_name, master_filter)

    def reload(self):
        self.filters.clear()
        for module, values in _MODULES.items():
            module = importlib.import_module(module)
            module = importlib.reload(module)
            for class_name, master_name, attribute_name, name in values:
                master_filter_class = getattr(module, class_name)
                master_filter = master_filter_class(self.bot, master_name, name)
                self.filters.append(master_filter)
                setattr(self, attribute_name, master_filter)
