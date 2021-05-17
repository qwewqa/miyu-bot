locale_aliases = {
    'en': 'en-US',
    'cn-TW': 'zh-TW',
    'tw': 'zh-TW',
    'jp': 'ja',
}
valid_locales = {'en-US', 'zh-TW', 'ja'}
valid_locales_and_aliases = valid_locales.union(locale_aliases.keys())
lowercase_locale_mapping = {n.lower(): locale_aliases.get(n, n) for n in valid_locales_and_aliases}
