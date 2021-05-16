from typing import Union

from fluent.runtime import FluentLocalization

from miyu_bot.bot.bot import PrefContext
from miyu_bot.commands.master_filter.locales import locale_aliases


class LocalizationManager:
    def __init__(self, loader, names):
        if isinstance(names, str):
            names = [names]
        self.names = names
        self.loader = loader
        self._values = {}

    def __getitem__(self, item: Union[str, PrefContext]) -> FluentLocalization:
        if isinstance(item, PrefContext):
            return self[item.preferences.language]
        item = locale_aliases.get(item, item)
        if item in self._values:
            return self._values[item]
        else:
            if item == 'en-US':
                localization = FluentLocalization(['en-US'], [*self.names, 'common.ftl'], self.loader)
            else:
                localization = FluentLocalization([item, 'en-US'], [*self.names, 'common.ftl'], self.loader)
            self._values[item] = localization
            return localization
