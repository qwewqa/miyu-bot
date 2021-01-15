from d4dj_utils.master.chart_master import ChartDifficulty

difficulty_emoji_ids = {
    ChartDifficulty.Easy: 790050636568723466,
    ChartDifficulty.Normal: 790050636489555998,
    ChartDifficulty.Hard: 790050636548276252,
    ChartDifficulty.Expert: 790050636225052694,
}

# \:buff_power: \:buff_heart: \:buff_technique: \:buff_physical:
parameter_bonus_emoji_Ids = {
    'all': 792930826735583293,
    'heart': 792096971040620564,
    'technique': 792096971090558986,
    'physical': 792096971002216488,
}

parameter_bonus_emoji_ids_by_parameter_id = {i: v for i, v in enumerate(parameter_bonus_emoji_Ids.values())}

unit_emoji_ids = {
    'happy_around': 792069679442821121,
    'peaky_pkey': 792076165916524544,
    'photon_maiden': 792069679455535136,
    'merm4id': 792069679874310184,
    'rondo': 792069679770238976,
    'lyrical_lily': 792069679673114644,
}

unit_emoji_ids_by_unit_id = {i + 1: v for i, v in enumerate(unit_emoji_ids.values())}

attribute_emoji_ids = {
    'street': 791903477986361345,
    'party': 791903477999599677,
    'cute': 791903477743616003,
    'cool': 791903477700755466,
    'elegant': 791903477969321985,
}

attribute_emoji_ids_by_attribute_id = {i + 1: v for i, v in enumerate(attribute_emoji_ids.values())}

event_point_emoji_id = 792097816931598336

rarity_emoji_ids = {
    'base': 799650003659915294,
    'limit_break': 799650003303268393
}
