import hashlib
from functools import lru_cache
from typing import Callable, Any, Optional

from d4dj_utils.manager.asset_manager import AssetManager
from d4dj_utils.master.master_asset import MasterDict, MasterAsset
from discord.ext import commands

from miyu_bot.commands.common.fuzzy_matching import FuzzyFilteredMap

import datetime as dt


class MasterFilterManager:
    def __init__(self, manager: AssetManager):
        self.manager = manager

    @property
    @lru_cache(None)
    def music(self):
        return MasterFilter(
            self.manager.music_master,
            naming_function=lambda m: f'{m.name} {m.special_unit_name}',
            filter_function=lambda m: m.is_released,
            fallback_naming_function=lambda m: m.id,
        )

    @property
    @lru_cache(None)
    def events(self):
        return MasterFilter(
            self.manager.event_master,
            naming_function=lambda e: e.name,
            filter_function=lambda e: e.start_datetime < dt.datetime.now(
                dt.timezone.utc) + dt.timedelta(hours=12),
        )

    @property
    @lru_cache(None)
    def cards(self):
        return MasterFilter(
            self.manager.card_master,
            naming_function=lambda c: c.name,
            filter_function=lambda c: c.is_released,
        )


class MasterFilter:
    def __init__(self, masters: MasterDict, naming_function: Callable[[Any], str], filter_function=lambda _: True,
                 fallback_naming_function: Optional[Callable[[Any], str]] = None):
        self.masters = masters
        self.default_filter = FuzzyFilteredMap(filter_function)
        self.unrestricted_filter = FuzzyFilteredMap()
        for master in masters.values():
            name = naming_function(master)
            if self.default_filter.has_exact(name) and fallback_naming_function:
                name = fallback_naming_function(master)
            if self.default_filter.has_exact(name):
                continue
            self.default_filter[name] = master
            self.unrestricted_filter[name] = master

    def get(self, name_or_id: str, ctx: Optional[commands.Context]):
        if ctx and ctx.channel.id in no_filter_channels:
            try:
                return self.masters[int(name_or_id)]
            except (KeyError, ValueError):
                return self.unrestricted_filter[name_or_id]
        else:
            try:
                master = self.masters[int(name_or_id)]
                if master not in self.default_filter.values():
                    master = self.default_filter[name_or_id]
                return master
            except (KeyError, ValueError):
                return self.default_filter[name_or_id]

    def get_sorted(self, name: str, ctx: commands.Context):
        if name:
            if ctx.channel.id in no_filter_channels:
                return self.unrestricted_filter.get_sorted(name)
            else:
                return self.default_filter.get_sorted(name)
        else:
            if ctx.channel.id in no_filter_channels:
                return list(self.unrestricted_filter.values())
            else:
                return list(self.default_filter.values())

    def values(self, ctx: commands.Context):
        if ctx.channel.id in no_filter_channels:
            return self.unrestricted_filter.values()
        else:
            return self.default_filter.values()


def hash_master(master: MasterAsset):
    return hashlib.md5(master.extended_description().encode('utf-8')).hexdigest()


no_filter_channels = {790033228600705048, 790033272376918027, 795640603114864640}
