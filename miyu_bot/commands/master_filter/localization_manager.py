from fluent.runtime import FluentLocalization

locale_aliases = {
    'en': 'en-US',
    'cn-TW': 'zh-TW',
}
valid_locales = {'en-US', 'zh-TW'}
valid_locales_and_aliases = valid_locales.union(locale_aliases.keys())
lowercase_locale_mapping = {n.lower(): locale_aliases.get(n, n) for n in valid_locales_and_aliases}

class LocalizationManager:
    def __init__(self, loader, name):
        self.name = name
        self.loader = loader
        self._values = {}

    def __getitem__(self, item: str) -> FluentLocalization:
        item = locale_aliases.get(item, item)
        if item in self._values:
            return self._values[item]
        else:
            if item == 'en-US':
                localization = FluentLocalization(['en-US'], [self.name, 'common.ftl'], self.loader)
            else:
                localization = FluentLocalization([item, 'en-US'], [self.name, 'common.ftl'], self.loader)
            self._values[item] = localization
            return localization
