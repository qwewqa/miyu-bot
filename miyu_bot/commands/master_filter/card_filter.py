import re
from datetime import datetime
from typing import List

import discord
from PIL import ImageColor
from d4dj_utils.master.card_master import CardMaster
from d4dj_utils.master.event_specific_bonus_master import EventSpecificBonusMaster
from d4dj_utils.master.passive_skill_master import PassiveSkillMaster, PassiveSkillType
from d4dj_utils.master.skill_master import SkillMaster

from miyu_bot.bot.bot import PrefContext
from miyu_bot.commands.common.asset_paths import get_asset_filename
from miyu_bot.commands.common.emoji import (
    attribute_emoji_ids_by_attribute_id,
    unit_emoji_ids_by_unit_id,
    parameter_bonus_emoji_ids_by_parameter_id,
    rarity_emoji_ids,
)
from miyu_bot.commands.master_filter.master_filter import (
    MasterFilter,
    data_attribute,
    command_source,
    DataAttributeInfo,
    list_formatter,
)


class CardFilter(MasterFilter[CardMaster]):
    def get_name(self, value: CardMaster) -> str:
        return f"{value.name} {value.character.first_name_english} {value.rarity_id}"

    def get_select_name(self, value: CardMaster):
        emoji = attribute_emoji_ids_by_attribute_id[value.attribute_id]
        return value.name, value.character.full_name_english, emoji

    def is_released(self, value: CardMaster) -> bool:
        return value.is_available

    @data_attribute("name", aliases=["title"], is_sortable=True)
    def name(self, value: CardMaster):
        return value.name

    @data_attribute(
        "character",
        aliases=["char", "chara"],
        is_sortable=True,
        is_keyword=True,
        is_tag=True,
        is_eq=True,
    )
    def character(self, value: CardMaster):
        return value.character_id

    @character.init
    def init_character(self, info: DataAttributeInfo):
        info.value_mapping = {
            k: v.id for k, v in self.bot.aliases.characters_by_name.items()
        }

    @data_attribute("unit", is_sortable=True, is_tag=True, is_eq=True)
    def unit(self, value: CardMaster):
        return value.character.unit_id

    @unit.init
    def init_unit(self, info: DataAttributeInfo):
        info.value_mapping = {
            k: v.id for k, v in self.bot.aliases.units_by_name.items()
        }

    @data_attribute("attribute", is_sortable=True, is_tag=True, is_eq=True)
    def attribute(self, value: CardMaster):
        return value.attribute_id

    @attribute.init
    def init_attribute(self, info: DataAttributeInfo):
        info.value_mapping = {
            k: v.id for k, v in self.bot.aliases.attributes_by_name.items()
        }

    @data_attribute("id", is_sortable=True, is_comparable=True)
    def id(self, value: CardMaster):
        return value.id

    @id.formatter
    def format_id(self, value: CardMaster):
        return str(value.id).zfill(8)

    @data_attribute(
        "power",
        aliases=["pow", "bp"],
        is_default_display=True,
        is_sortable=True,
        is_comparable=True,
        reverse_sort=True,
        help_sample_argument="27649",
    )
    def power(self, value: CardMaster):
        return value.max_power_with_limit_break

    @power.formatter
    def format_power(self, value: CardMaster):
        return str(value.max_power_with_limit_break).rjust(5)

    @staticmethod
    def get_highest_parameter(value: CardMaster):
        return value.max_parameters.index(max(value.max_parameters))

    @data_attribute(
        "heart",
        aliases=["hrt"],
        is_sortable=True,
        is_comparable=True,
        is_flag=True,
        reverse_sort=True,
        help_sample_argument="9082",
    )
    def heart(self, value: CardMaster):
        return value.max_parameters_with_limit_break[0]

    @heart.flag_callback
    def heart_flag_callback(self, values: List[CardMaster]):
        return [v for v in values if self.get_highest_parameter(v) == 0]

    @heart.formatter
    def format_heart(self, value: CardMaster):
        return str(value.max_parameters_with_limit_break[0]).rjust(5)

    @data_attribute(
        "technique",
        aliases=["tech", "technical"],
        is_sortable=True,
        is_comparable=True,
        is_flag=True,
        reverse_sort=True,
        help_sample_argument="9219",
    )
    def technique(self, value: CardMaster):
        return value.max_parameters_with_limit_break[1]

    @technique.flag_callback
    def technique_flag_callback(self, values: List[CardMaster]):
        return [v for v in values if self.get_highest_parameter(v) == 1]

    @technique.formatter
    def format_technique(self, value: CardMaster):
        return str(value.max_parameters_with_limit_break[1]).rjust(5)

    @data_attribute(
        "physical",
        aliases=["phys", "physic", "physics"],
        is_sortable=True,
        is_comparable=True,
        is_flag=True,
        reverse_sort=True,
        help_sample_argument="9348",
    )
    def physical(self, value: CardMaster):
        return value.max_parameters_with_limit_break[2]

    @physical.flag_callback
    def physical_flag_callback(self, values: List[CardMaster]):
        return [v for v in values if self.get_highest_parameter(v) == 2]

    @physical.formatter
    def format_physical(self, value: CardMaster):
        return str(value.max_parameters_with_limit_break[2]).rjust(5)

    @data_attribute(
        "default_sort",
        is_default_sort=True,
        is_sortable=True,
    )
    def default_sort(self, ctx, value: CardMaster):
        is_special = value.start_datetime.year > 2099
        return is_special, -value.start_datetime.timestamp(), value.debut_order

    @data_attribute(
        "date",
        aliases=["release", "recent"],
        is_sortable=True,
        is_comparable=True,
        reverse_sort=True,
        help_sample_argument="2020/12/31",
    )
    def date(self, ctx, value: CardMaster):
        return ctx.convert_tz(value.start_datetime).date()

    @date.formatter
    def format_date(self, ctx, value: CardMaster):
        dt = ctx.convert_tz(value.start_datetime)
        return f"{dt.year % 100:02}/{dt.month:02}/{dt.day:02}"

    @date.compare_converter
    def date_compare_converter(self, ctx: PrefContext, s):
        match = re.fullmatch(r"(\d+)/(\d+)/(\d+)", s)
        if not match:
            raise
        y, m, d = (int(n) for n in match.groups())
        if y < 100:
            y += ctx.localize(datetime.now()).year // 100 * 100
        return ctx.localize(datetime(year=y, month=m, day=d)).date()

    @data_attribute(
        "permanent",
        aliases=["perm", "perma"],
        is_flag=True,
    )
    def permanent(self, value: CardMaster):
        return value.permanent

    @data_attribute(
        "limited",
        aliases=["lim", "limit"],
        is_flag=True,
    )
    def limited(self, value: CardMaster):
        return not value.permanent

    rarity_aliases = {
        r"7*": 7,
        r"7\*": 7,
        r"*7": 7,
        r"\*7": 7,
        r"SP": 7,
        r"sp": 7,
        r"6*": 6,
        r"6\*": 6,
        r"*6": 6,
        r"\*6": 6,
        r"NV": 6,
        r"nv": 6,
        r"nav": 6,
        r"navi": 6,
        r"5*": 5,
        r"5\*": 5,
        r"*5": 5,
        r"\*5": 5,
        r"CP": 5,
        r"cp": 5,
        r"4*": 4,
        r"4\*": 4,
        r"*4": 4,
        r"\*4": 4,
        r"3*": 3,
        r"3\*": 3,
        r"*3": 3,
        r"\*3": 3,
        r"2*": 2,
        r"2\*": 2,
        r"*2": 2,
        r"\*2": 2,
        r"1*": 1,
        r"1\*": 1,
        r"*1": 1,
        r"\*1": 1,
    }

    @data_attribute(
        "rarity_keyword",
        is_keyword=True,
        is_tag=True,
        value_mapping=rarity_aliases,
    )
    def rarity_keyword(self, value: CardMaster):
        return value.rarity_id

    @data_attribute(
        "rarity",
        aliases=["rare", "star", "stars"],
        is_comparable=True,
        is_sortable=True,
        reverse_sort=True,
        help_sample_argument="SP",
    )
    def rarity(self, value: CardMaster):
        return value.rarity.value

    @rarity.init
    def init_rarity(self, info: DataAttributeInfo):
        rarity_master = self.bot.assets[0].rarity_master
        aliases = {k: rarity_master[v].value for k, v in self.rarity_aliases.items()}
        for rarity in rarity_master.values():
            aliases[str(rarity.id)] = rarity.value
        info.value_mapping = aliases

    @data_attribute(
        "skill",
        aliases=["score_up", "score"],
        is_comparable=True,
        is_sortable=True,
        reverse_sort=True,
        help_sample_argument="50",
    )
    def skill(self, value: CardMaster):
        skill = value.skill
        return skill.score_up_rate + skill.perfect_score_up_rate

    @skill.formatter
    def skill_formatter(self, value: CardMaster):
        skill = value.skill
        if skill.perfect_score_up_rate:
            return f"{skill.score_up_rate + skill.perfect_score_up_rate:>2} ({skill.perfect_score_up_rate:>2}p)"
        else:
            return f"{skill.score_up_rate + skill.perfect_score_up_rate:>2}      "

    @data_attribute(
        "groovy_score",
        aliases=[
            "groovyscore",
            "groovy",
            "fever_score",
            "feverscore",
            "fever",
            "groovy_score_up",
            "groovyscoreup",
            "fever_score_up",
            "feverscoreup",
            "feverup",
            "groovyup",
            "fever_up",
            "groovy_up",
            "feverboost",
            "fever_boost",
            "groovyboost",
            "groovy_boost",
            "gtscore",
            "gtscoreup",
            "gt_score",
            "gt_score_up",
            "gtup",
            "gt_up",
        ],
        is_comparable=True,
        is_sortable=True,
        reverse_sort=True,
        is_flag=True,
        help_sample_argument="10",
    )
    def groovy_score(self, value: CardMaster):
        passive_skill = value.passive_skill
        if passive_skill.type == PassiveSkillType.FeverBonus:
            return passive_skill.max_value * 100
        return 0

    @groovy_score.formatter
    def groovy_score_formatter(self, value: CardMaster):
        if self.groovy_score(value) > 0:
            return f"{self.groovy_score(value):>5.2f}%"
        else:
            return f"   ---"

    @data_attribute(
        "groovy_support",
        aliases=[
            "groovysupport",
            "fever_support",
            "feversupport",
            "gtsupport",
            "gt_support",
        ],
        is_comparable=True,
        is_sortable=True,
        reverse_sort=True,
        is_flag=True,
        help_sample_argument="10",
    )
    def groovy_support(self, value: CardMaster):
        passive_skill = value.passive_skill
        if passive_skill.type == PassiveSkillType.FeverSupport:
            return passive_skill.max_value * 100
        return 0

    @groovy_support.formatter
    def groovy_support_formatter(self, value: CardMaster):
        if self.groovy_support(value) > 0:
            return f"{self.groovy_support(value):>5.2f}%"
        else:
            return f"   ---"

    @data_attribute(
        "solo_groovy",
        aliases=["solo_fever", "solo_gt", "sologroovy", "solofever", "sologt"],
        is_flag=True,
    )
    def solo_groovy(self, value: CardMaster):
        passive_skill = value.passive_skill
        return passive_skill.type == PassiveSkillType.FeverSupport

    @data_attribute(
        "constant_score",
        aliases=[
            "constantscore",
            "constant_score_up",
            "constantscoreup",
            "passive_score",
            "passivescore",
            "passive_score_up",
        ],
        is_comparable=True,
        is_sortable=True,
        reverse_sort=True,
        is_flag=True,
        help_sample_argument="2.5",
    )
    def constant_score(self, value: CardMaster):
        passive_skill = value.passive_skill
        if passive_skill.type == PassiveSkillType.ScoreUpWithDamage:
            return passive_skill.max_value * 100
        return 0

    @constant_score.formatter
    def constant_score_formatter(self, value: CardMaster):
        if self.constant_score(value) > 0:
            return f"{self.constant_score(value):>5.2f}%"
        else:
            return f"   ---"

    @data_attribute(
        "auto_score",
        aliases=[
            "autoscore",
            "auto_score_up",
            "autoscoreup",
            "auto_up",
            "auto_boost",
            "auto_support",
            "autoboost",
            "autosupport",
            "autoup",
        ],
        is_comparable=True,
        is_sortable=True,
        reverse_sort=True,
        is_flag=True,
        help_sample_argument="2.5",
    )
    def auto_score(self, value: CardMaster):
        passive_skill = value.passive_skill
        if passive_skill.type == PassiveSkillType.AutoScoreUp:
            return passive_skill.max_value * 100
        return 0

    @auto_score.formatter
    def auto_score_formatter(self, value: CardMaster):
        if self.auto_score(value) > 0:
            return f"{self.auto_score(value):>5.2f}%"
        else:
            return f"   ---"
        
    @data_attribute(
        "manual_up",
        aliases=[
            "manualup",
            "manual_score_up",
            "manualscoreup",
        ],
        is_comparable=True,
        is_sortable=True,
        reverse_sort=True,
        is_flag=True,
        help_sample_argument="2.5",
    )
    def manual_up(self, value: CardMaster):
        passive_skill = value.passive_skill
        if passive_skill.type == PassiveSkillType.ManualScoreUp:
            return passive_skill.max_value * 100
        return 0
    
    @manual_up.formatter
    def manual_up_formatter(self, value: CardMaster):
        if self.manual_up(value) > 0:
            return f"{self.manual_up(value):>5.2f}%"
        else:
            return f"   ---"
        
    @data_attribute(
        "score_up",
        aliases=[
            "scoreup",
            "support_score_up",
            "supportscoreup",
        ],
        is_comparable=True,
        is_sortable=True,
        reverse_sort=True,
        is_flag=True,
        help_sample_argument="4",
    )
    def score_up(self, value: CardMaster):
        passive_skill = value.passive_skill
        if passive_skill.type == PassiveSkillType.SupportableScoreUp:
            return passive_skill.max_value * 100
        return 0

    @score_up.formatter
    def score_up_formatter(self, value: CardMaster):
        if self.score_up(value) > 0:
            return f"{self.score_up(value):>5.2f}%"
        else:
            return f"   ---"
        
    @data_attribute(
        "skill_duration_up",
        aliases=[
            "skilldurationup",
            "skill_duration",
            "skillduration",
            "support_skill_duration_up",
            "supportskilldurationup",
        ],
        is_comparable=True,
        is_sortable=True,
        reverse_sort=True,
        is_flag=True,
        help_sample_argument="15",
    )
    def skill_duration_up(self, value: CardMaster):
        passive_skill = value.passive_skill
        if passive_skill.type == PassiveSkillType.SupportableSkillLonger:
            return passive_skill.max_value * 100
        return 0

    @skill_duration_up.formatter
    def skill_duration_up_formatter(self, value: CardMaster):
        if self.skill_duration_up(value) > 0:
            return f"{self.skill_duration_up(value):>5.2f}%"
        else:
            return f"   ---"
        
    @data_attribute(
        "sympathy",
        aliases=[
            "support_sympathy",
            "supportsympathy",
        ],
        is_comparable=True,
        is_sortable=True,
        reverse_sort=True,
        is_flag=True,
        help_sample_argument="2",
    )
    def sympathy(self, value: CardMaster):
        passive_skill = value.passive_skill
        if passive_skill.type == PassiveSkillType.SupportableSympathy:
            return passive_skill.max_value * 100
        return 0

    @sympathy.formatter
    def sympathy_formatter(self, value: CardMaster):
        if self.sympathy(value) > 0:
            return f"{self.sympathy(value):>5.2f}%"
        else:
            return f"   ---"

    @command_source(
        command_args=dict(
            name="card", description="Displays card info.", help="!card secretcage"
        ),
        tabs=list(rarity_emoji_ids.values()),
        default_tab=1,
        suffix_tab_aliases={"untrained": 0, "trained": 1},
    )
    def get_card_embed(self, ctx, card: CardMaster, limit_break, server):
        l10n = self.l10n[ctx]

        if card.rarity_id <= 2:
            limit_break = 0

        color_code = card.character.color_code
        color = (
            discord.Colour.from_rgb(*ImageColor.getcolor(color_code, "RGB"))
            if color_code
            else None
        )

        embed = discord.Embed(
            title=f"[{server.name}] {self.format_card_name(card)}", color=color
        )

        thumb_url = ctx.bot.asset_url + get_asset_filename(card.icon_path(limit_break))
        art_url = ctx.bot.asset_url + get_asset_filename(card.art_path(limit_break))

        embed.set_thumbnail(url=thumb_url)
        embed.set_image(url=art_url)

        embed.add_field(
            name=l10n.format_value("info"),
            value=l10n.format_value(
                "info-desc",
                {
                    "rarity": f"{card.rarity.rarity_name}",
                    "character": f"{card.character.full_name_english}",
                    "attribute": f"{attribute_emoji_ids_by_attribute_id[card.attribute_id]} {card.attribute.en_name.capitalize()}",
                    "unit": f"{unit_emoji_ids_by_unit_id[card.character.unit_id]} {card.character.unit.name}",
                    "release-date": discord.utils.format_dt(card.start_datetime),
                    "event": f'{card.event.name if card.event else "None"}',
                    "gacha": f'{card.gacha.name if card.gacha else "None"}',
                    "availability": card.availability.name,
                    "limited": not card.permanent,
                },
            ),
            inline=False,
        )
        embed.add_field(
            name=l10n.format_value("parameters"),
            value=l10n.format_value(
                "parameters-desc",
                {
                    "total": card.max_power_with_limit_break,
                    "heart": card.max_parameters_with_limit_break[0],
                    "technique": card.max_parameters_with_limit_break[1],
                    "physical": card.max_parameters_with_limit_break[2],
                    "heart-emoji": str(parameter_bonus_emoji_ids_by_parameter_id[1]),
                    "technique-emoji": str(
                        parameter_bonus_emoji_ids_by_parameter_id[2]
                    ),
                    "physical-emoji": str(parameter_bonus_emoji_ids_by_parameter_id[3]),
                },
            ),
            inline=True,
        )
        skill: SkillMaster = card.skill
        embed.add_field(
            name=l10n.format_value("skill"),
            value=l10n.format_value(
                "skill-desc",
                {
                    "name": card.skill_name,
                    "duration": f"{skill.min_seconds}-{skill.max_seconds}s",
                    "score-up": f"{skill.score_up_rate}%"
                    if not skill.perfect_score_up_rate
                    else f"{skill.score_up_rate}% + {skill.perfect_score_up_rate}% perfect",
                    "score-up-additional": (
                            "\n("
                            + ", ".join(f"+{v}%" for v in skill.group_bonus_rates)
                            + ")"
                    )
                    if skill.group_bonus_rates
                    else "",
                    "heal": (
                        f"{skill.min_recovery_value}-{skill.max_recovery_value}"
                        if skill.min_recovery_value != skill.max_recovery_value
                        else str(skill.min_recovery_value)
                    ),
                },
            ),
            inline=True,
        )
        passive: PassiveSkillMaster = card.passive_skill
        embed.add_field(
            name=l10n.format_value("passive"),
            value=l10n.format_value(
                "passive-desc",
                {
                    "type": passive.type.name,
                    "bonus-character": passive.bonus_character.first_name_english
                    if passive.bonus_character
                    else l10n.format_value("none"),
                    "min-value": f"{100 * passive.min_value:.2f}".rstrip("0").rstrip(
                        "."
                    ),
                    "max-value": f"{100 * passive.max_value:.2f}".rstrip("0").rstrip(
                        "."
                    ),
                    "sub-value": f"{100 * passive.sub_value:.2f}".rstrip("0").rstrip(
                        "."
                    ),
                },
            ),
            inline=False,
        )
        embed.set_footer(
            text=l10n.format_value("card-id", {"card-id": f"{card.id:0>8}"})
        )

        return embed

    def format_card_name(self, card):
        return f"{card.rarity.rarity_name} {card.name} {card.character.full_name_english}"

    @list_formatter(
        name="card-search",
        command_args=dict(name="cards", description="Lists cards.", help="!cards"),
    )
    def format_card_name_for_list(self, card):
        unit_emoji = unit_emoji_ids_by_unit_id[card.character.unit_id]
        attribute_emoji = attribute_emoji_ids_by_attribute_id[card.attribute_id]
        parameter_emoji = parameter_bonus_emoji_ids_by_parameter_id[
            self.get_highest_parameter(card) + 1
            ]
        return f"`{unit_emoji}`+`{attribute_emoji}`+`{parameter_emoji}` {card.rarity.rarity_name} {card.name} {card.character.first_name_english}"

    @get_card_embed.shortcut_button(name="Banner")
    async def gacha_shortcut(
            self, ctx, card: CardMaster, server, interaction: discord.Interaction
    ):
        f = ctx.bot.master_filters.gacha
        view, embed = f.get_simple_detail_view(
            ctx, [card.gacha], server, f.get_gacha_embed
        )
        await interaction.response.send_message(embed=embed, view=view)

    @gacha_shortcut.check
    def check_gacha_shortcut(self, card: CardMaster, _ctx):
        return card.gacha is not None

    def get_rateup_gachas(self, card: CardMaster, ctx):
        f = ctx.bot.master_filters.gacha
        return [g for g in f.values(ctx) if card in f.get_gacha_rateup_card_set(g)]

    @get_card_embed.shortcut_button(name="Banners")
    async def gacha_list_shortcut(
            self, ctx, card: CardMaster, server, interaction: discord.Interaction
    ):
        f = ctx.bot.master_filters.gacha
        view, embed = f.get_simple_list_view(
            ctx, self.get_rateup_gachas(card, ctx), server
        )
        await interaction.response.send_message(embed=embed, view=view)

    @gacha_list_shortcut.check
    def check_gacha_list_shortcut(self, card: CardMaster, ctx):
        return bool(self.get_rateup_gachas(card, ctx))

    @get_card_embed.shortcut_button(name="Event")
    async def event_shortcut(
            self, ctx, card: CardMaster, server, interaction: discord.Interaction
    ):
        f = ctx.bot.master_filters.events
        view, embed = f.get_simple_detail_view(
            ctx, [card.event], server, f.get_event_embed
        )
        await interaction.response.send_message(embed=embed, view=view)

    @event_shortcut.check
    def check_event_shortcut(self, card: CardMaster, _ctx):
        return card.event is not None
