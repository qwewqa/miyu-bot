from functools import cached_property

from d4dj_utils.master.asset_manager import AssetManager


class NameAliases:
    assets: AssetManager

    def __init__(self, assets):
        self.assets = assets

    @cached_property
    def characters_by_name(self):
        characters_by_name = {}
        for character in self.assets.character_master.values():
            for name in character.full_name_english.split():
                characters_by_name[name.lower()] = character
        return characters_by_name

    @cached_property
    def attributes_by_name(self):
        return {attribute.en_name: attribute for attribute in self.assets.attribute_master.values()}

    @cached_property
    def units_by_name(self):
        units_by_name = {unit.name.lower().replace(' ', '_'): unit for unit in self.assets.unit_master.values()}
        units_by_name['rondo'] = units_by_name['燐舞曲']
        units_by_name['special'] = units_by_name['スペシャル']
        units_by_name['other'] = units_by_name['その他']
        for alias, value in self.unit_aliases.items():
            units_by_name[alias] = units_by_name[value]
        return units_by_name

    unit_aliases = {
        'happyaround': 'happy_around!',
        'happy_around': 'happy_around!',
        'hapiara': 'happy_around!',
        'happy': 'happy_around!',
        'ha': 'happy_around',
        'peakyp-key': 'peaky_p-key',
        'peakypkey': 'peaky_p-key',
        'peaky': 'peaky_p-key',
        'p-key': 'peaky_p-key',
        'pkey': 'peaky_p-key',
        'pkpk': 'peaky_p-key',
        'pk': 'peaky_p-key',
        'photonmaiden': 'photon_maiden',
        'photome': 'photon_maiden',
        'photon': 'photon_maiden',
        'pm': 'photon_maiden',
        'mermaid': 'merm4id',
        'mmd': 'merm4id',
        'lyricallily': 'lyrical_lily',
        'riririri': 'lyrical_lily',
        'lililili': 'lyrical_lily',
        'lily': 'lyrical_lily',
        'lili': 'lyrical_lily',
        'riri': 'lyrical_lily',
        'll': 'lyrical_lily',
        'fuhifumi': 'lyrical_lily',
    }
