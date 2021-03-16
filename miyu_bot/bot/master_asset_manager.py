import hashlib
from typing import Callable, Any, Optional, Union

from d4dj_utils.master.asset_manager import AssetManager
from d4dj_utils.master.event_master import EventMaster, EventState
from d4dj_utils.master.master_asset import MasterDict, MasterAsset
from discord.ext import commands

from miyu_bot.bot.aliases.event import event_aliases
from miyu_bot.commands.common.fuzzy_matching import FuzzyFilteredMap, romanize

import datetime as dt


class MasterFilterManager:
    def __init__(self, manager: AssetManager):
        self.manager = manager
        self.music = MasterFilter(
            self.manager.music_master,
            naming_function=lambda m: f'{m.name} {m.special_unit_name}{" (Hidden)" if m.is_hidden else ""}',
            filter_function=lambda m: m.is_released,
            fallback_naming_function=lambda m: m.id,
        )
        self.events = EventFilter(
            self.manager.event_master,
            aliases=event_aliases,
            naming_function=lambda e: e.name,
            filter_function=lambda e: e.start_datetime < dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=12),
        )
        self.cards = MasterFilter(
            self.manager.card_master,
            naming_function=lambda c: f'{c.name} {c.character.first_name_english}',
            filter_function=lambda c: c.is_released,
        )
        self.gacha = MasterFilter(
            self.manager.gacha_master,
            naming_function=lambda g: f'{g.name}',
            filter_function=lambda g: g.is_released,
        )
        self.stamps = MasterFilter(
            self.manager.stamp_master,
            naming_function=lambda s: f'{s.name + " " + s.quote.replace("～", "ー") if s.quote else s.description}',
            filter_function=lambda s: s.is_released,
        )


class MasterFilter:
    def __init__(self, masters: MasterDict,
                 naming_function: Callable[[Any], str],
                 aliases: Optional[dict] = None,
                 filter_function=lambda _: True,
                 prefilter_function=lambda _: True,
                 fallback_naming_function: Optional[Callable[[Any], str]] = None):
        self.masters = masters
        self.default_filter = FuzzyFilteredMap(filter_function)
        self.unrestricted_filter = FuzzyFilteredMap()
        for master in masters.values():
            if prefilter_function(master):
                name = naming_function(master)
                if fallback_naming_function and self.default_filter.has_exact(name):
                    name = romanize(fallback_naming_function(master))
                    if self.default_filter.has_exact(name):
                        continue
                elif self.default_filter.has_exact(name):
                    continue
                self.default_filter[name] = master
                self.unrestricted_filter[name] = master
        if aliases:
            for alias, mid in aliases.items():
                self.add_alias(alias, mid)

    def add_alias(self, alias, master_id):
        master = self.masters[master_id]
        alias = romanize(alias)
        self.default_filter[alias] = master
        self.unrestricted_filter[alias] = master

    def get(self, name_or_id: Union[str, int], ctx: Optional[commands.Context]):
        if ctx and ctx.channel.id in no_filter_channels:
            try:
                return self.masters[int(name_or_id)]
            except (KeyError, ValueError):
                if isinstance(name_or_id, int):
                    return None
                return self.unrestricted_filter[name_or_id]
        else:
            try:
                master = self.masters[int(name_or_id)]
                if master not in self.default_filter.values():
                    master = self.default_filter[name_or_id]
                return master
            except (KeyError, ValueError):
                if isinstance(name_or_id, int):
                    return None
                return self.default_filter[name_or_id]

    def get_by_relevance(self, name: str, ctx: commands.Context):
        try:
            master = self.masters[int(name)]
            id_result = [master]
            if not ctx or (ctx.channel.id not in no_filter_channels and master not in self.default_filter.values()):
                if master not in self.default_filter.values():
                    id_result = []
        except (KeyError, ValueError):
            id_result = []

        if name:
            if ctx.channel.id in no_filter_channels:
                return id_result + self.unrestricted_filter.get_sorted(name)
            else:
                return id_result + self.default_filter.get_sorted(name)
        else:
            if ctx.channel.id in no_filter_channels:
                return list(self.unrestricted_filter.values())
            else:
                return list(self.default_filter.values())

    def values(self, ctx: Optional[commands.Context]):
        if ctx is not None and ctx.channel.id in no_filter_channels:
            return self.unrestricted_filter.values()
        else:
            return self.default_filter.values()


class EventFilter(MasterFilter):
    def get_latest_event(self, ctx: Optional[commands.Context]) -> EventMaster:
        """Returns the oldest event that has not ended or the newest event otherwise."""
        try:
            # NY event overlapped with previous event
            return min((v for v in self.values(ctx) if v.state() == EventState.Open),
                       key=lambda e: e.start_datetime)
        except ValueError:
            try:
                return min((v for v in self.values(ctx) if v.state() < EventState.Ended),
                           key=lambda e: e.start_datetime)
            except ValueError:
                return max(self.values(ctx), key=lambda v: v.start_datetime)


def hash_master(master: MasterAsset):
    return hashlib.md5(master.extended_description().encode('utf-8')).hexdigest()


no_filter_channels = {790033228600705048, 790033272376918027, 795640603114864640}
