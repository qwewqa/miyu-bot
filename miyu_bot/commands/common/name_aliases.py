from main import asset_manager

characters_by_name = {}
for character in asset_manager.character_master.values():
    for name in character.full_name_english.split():
        characters_by_name[name.lower()] = character

attributes_by_name = {attribute.en_name: attribute for attribute in asset_manager.attribute_master.values()}

units_by_name = {unit.name.lower().replace(' ', '_'): unit for unit in asset_manager.unit_master.values()}
units_by_name['rondo'] = units_by_name['燐舞曲']
units_by_name['special'] = units_by_name['スペシャル']
units_by_name['other'] = units_by_name['その他']
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
    'll': 'lyrical_lily',
    'fuhifumi': 'lyrical_lily',
}
