from collections import defaultdict

from d4dj_utils.master.chart_master import ChartDifficulty

difficulty_emoji_ids = {
    ChartDifficulty.Easy: "<:difficulty_easy:790050636568723466>",
    ChartDifficulty.Normal: "<:difficulty_normal:790050636489555998>",
    ChartDifficulty.Hard: "<:difficulty_hard:790050636548276252>",
    ChartDifficulty.Expert: "<:difficulty_expert:790050636225052694>",
    # For the future, if it ever comes
    # ChartDifficulty.Special: '<:difficulty_special:790050636556533820>',
}

parameter_bonus_emoji_ids = {
    "all": "<:param_power:792930826735583293>",
    "heart": "<:param_heart:792096971040620564>",
    "technique": "<:param_technique:792096971090558986>",
    "physical": "<:param_physical:792096971002216488>",
}

parameter_bonus_emoji_ids_by_parameter_id = {
    i: v for i, v in enumerate(parameter_bonus_emoji_ids.values())
}

unit_emoji_ids = defaultdict(
    lambda: common_unit_emoji_id,
    {
        "happy_around": "<:unit_happy_around:792069679442821121>",
        "peaky_pkey": "<:unit_peaky_pkey:792076165916524544>",
        "photon_maiden": "<:unit_photon_maiden:792069679455535136>",
        "merm4id": "<:unit_merm4id:792069679874310184>",
        "rondo": "<:unit_rondo:792069679770238976>",
        "lyrical_lily": "<:unit_lyrical_lily:792069679673114644>",
        "call_of_artemis": "<:unit_call_of_artemis:1059287417590403162>",
        "unichord": "<:unit_unichord:1059287416483106996>",
    },
)

common_unit_emoji_id = "<:unit_common:815670436544118785>"

unit_emoji_ids_by_unit_id = defaultdict(
    lambda: common_unit_emoji_id,
    {
        1: unit_emoji_ids["happy_around"],
        2: unit_emoji_ids["peaky_pkey"],
        3: unit_emoji_ids["photon_maiden"],
        4: unit_emoji_ids["merm4id"],
        5: unit_emoji_ids["rondo"],
        6: unit_emoji_ids["lyrical_lily"],
        7: unit_emoji_ids["call_of_artemis"],
        8: unit_emoji_ids["unichord"],
    },
)

attribute_emoji_ids = {
    "street": "<:type_street:791903477986361345>",
    "party": "<:type_party:791903477999599677>",
    "cute": "<:type_cute:791903477743616003>",
    "cool": "<:type_cool:791903477700755466>",
    "elegant": "<:type_elegant:791903477969321985>",
}

attribute_emoji_ids_by_attribute_id = {
    i + 1: v for i, v in enumerate(attribute_emoji_ids.values())
}

event_point_emoji_id = "<:event_point:792097816931598336>"

rarity_emoji_ids = {
    "base": "<:rarity_star:799650003659915294>",
    "limit_break": "<:rarity_star_trained:799650003303268393>",
}

grey_emoji_id = "<:grey:816549259541348372>"
