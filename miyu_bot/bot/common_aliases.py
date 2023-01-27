from functools import cached_property

from d4dj_utils.master.asset_manager import AssetManager


class CommonAliases:
    assets: AssetManager

    def __init__(self, assets):
        self.assets = assets[0]

    @cached_property
    def characters_by_name(self):
        characters_by_name = {}
        for character in self.assets.character_master.values():
            if any(
                card.character == character for card in self.assets.card_master.values()
            ):
                characters_by_name[character.first_name_english.lower()] = character
        return characters_by_name

    @cached_property
    def attributes_by_name(self):
        attributes_by_name = {
            attribute.en_name.lower(): attribute
            for attribute in self.assets.attribute_master.values()
        }
        attributes_by_name["purple"] = attributes_by_name["street"]
        attributes_by_name["yellow"] = attributes_by_name["party"]
        attributes_by_name["orange"] = attributes_by_name["party"]
        attributes_by_name["pink"] = attributes_by_name["cute"]
        attributes_by_name["red"] = attributes_by_name["cute"]
        attributes_by_name["blue"] = attributes_by_name["cool"]
        attributes_by_name["green"] = attributes_by_name["elegant"]
        return attributes_by_name

    @cached_property
    def units_by_name(self):
        units_by_name = {
            unit.name.lower().replace(" ", "_"): unit
            for unit in self.assets.unit_master.values()
        }
        units_by_name["rondo"] = self.assets.unit_master[5]
        units_by_name["unichord"] = self.assets.unit_master[8]
        units_by_name["special"] = self.assets.unit_master[30]
        units_by_name["other"] = self.assets.unit_master[50]
        for alias, value in self.unit_aliases.items():
            units_by_name[alias] = units_by_name[value]
        return units_by_name

    unit_aliases = {
        "happyaround": "happy_around!",
        "happy_around": "happy_around!",
        "hapiara": "happy_around!",
        "happy": "happy_around!",
        "ha": "happy_around",
        "peakyp-key": "peaky_p-key",
        "peakypkey": "peaky_p-key",
        "peaky": "peaky_p-key",
        "p-key": "peaky_p-key",
        "pkey": "peaky_p-key",
        "pkpk": "peaky_p-key",
        "pk": "peaky_p-key",
        "photonmaiden": "photon_maiden",
        "photome": "photon_maiden",
        "photon": "photon_maiden",
        "pm": "photon_maiden",
        "mermaid": "merm4id",
        "mmd": "merm4id",
        "m4": "merm4id",
        "lyricallily": "lyrical_lily",
        "riririri": "lyrical_lily",
        "lililili": "lyrical_lily",
        "lily": "lyrical_lily",
        "lili": "lyrical_lily",
        "riri": "lyrical_lily",
        "ll": "lyrical_lily",
        "callofartemis": "call_of_artemis",
        "coa": "call_of_artemis",
        "c.o.a.": "call_of_artemis",
        "uc": "unichord",
        "1c": "unichord",
        "uni": "unichord",
        "am": "abyssmare",
        "abyss": "abyssmare",
    }
