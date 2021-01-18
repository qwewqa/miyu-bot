from main import asset_manager

characters_by_name = {}
for character in asset_manager.character_master.values():
    for name in character.full_name_english.split():
        characters_by_name[name.lower()] = character

attributes_by_name = {attribute.en_name: attribute for attribute in asset_manager.attribute_master.values()}

units_by_name = {unit.name.lower(): unit for unit in asset_manager.unit_master.values()}
units_by_name['rondo'] = units_by_name['燐舞曲']
