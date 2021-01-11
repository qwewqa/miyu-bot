from typing import Callable, Any, Optional

from d4dj_utils.master.master_asset import MasterDict
from discord.ext import commands

from miyu_bot.commands.common.fuzzy_matching import FuzzyFilteredMap


class MasterAssetManager:
    def __init__(self, masters: MasterDict, naming_function: Callable[[Any], str], filter_function=lambda _: True,
                 fallback_naming_function: Optional[Callable[[Any], str]] = None):
        self.masters = masters
        self.fuzzy_map = FuzzyFilteredMap(filter_function)
        self.unfiltered_fuzzy_map = FuzzyFilteredMap()
        for master in masters.values():
            name = naming_function(master)
            if self.fuzzy_map.has_exact(name) and fallback_naming_function:
                name = fallback_naming_function(master)
            if self.fuzzy_map.has_exact(name):
                continue
            self.fuzzy_map[name] = master
            self.unfiltered_fuzzy_map[name] = master

    def get(self, name_or_id: str, ctx: Optional[commands.Context]):
        if ctx and ctx.channel.id in no_filter_channels:
            try:
                return self.masters[int(name_or_id)]
            except (KeyError, ValueError):
                return self.unfiltered_fuzzy_map[name_or_id]
        else:
            try:
                master = self.masters[int(name_or_id)]
                if master not in self.fuzzy_map.values():
                    master = self.fuzzy_map[name_or_id]
                return master
            except (KeyError, ValueError):
                return self.fuzzy_map[name_or_id]

    def get_sorted(self, name: str, ctx: commands.Context):
        if name:
            if ctx.channel.id in no_filter_channels:
                return self.unfiltered_fuzzy_map.get_sorted(name)
            else:
                return self.fuzzy_map.get_sorted(name)
        else:
            if ctx.channel.id in no_filter_channels:
                return list(self.unfiltered_fuzzy_map.values())
            else:
                return list(self.fuzzy_map.values())

    def values(self, ctx: commands.Context):
        if ctx.channel.id in no_filter_channels:
            return self.unfiltered_fuzzy_map.values()
        else:
            return self.fuzzy_map.values()


no_filter_channels = {790033228600705048, 790033272376918027, 795640603114864640}
