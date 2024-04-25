info = Information
info-desc =
    Rarity: { $rarity }
    Character: { $character }
    Attribute: { $attribute }
    Unit: { $unit }
    Release Date: { $release-date }
    Gacha: { $gacha }
    Limited: { $limited ->
        [0] { no }
       *[1] { yes }
    }

availability-name = { $availability ->
    [Permanent] Permanent
    [Limited] Limited
    [Collab] Collab
    [Birthday] Birthday
    [Welfare] Reward
   *[other] Unknown
}

parameters = Parameters
parameters-desc =
    Total: { $total }
    { $heart-emoji } Heart: { $heart }
    { $technique-emoji } Technique: { $technique }
    { $physical-emoji } Physical: { $physical }

skill = Skill
skill-desc =
    Name: { $name }
    Duration: { $duration }
    Score Up: { $score-up } { $score-up-additional }
    Heal: { $heal }

passive = Passive
passive-desc = { $type ->
    [FeverBonus] { groovy-bonus-desc }
    [FeverSupport] { groovy-support-desc }
    [ScoreUpWithDamage] { life-boost-desc }
    [AutoScoreUp] { auto-support-desc }
    [ManualScoreUp] { manual-support-desc }
    [SupportableScoreUp] { supportable-score-up-desc }
    [SupportableSkillLonger] { supportable-skill-longer-desc }
    [SupportableSympathy] { supportable-sympathy-desc }
   *[other] None
}
groovy-bonus-desc =
    Groovy Score Up: { $min-value }-{ $max-value }%
groovy-support-desc =
    Solo Groovy
    Groovy Charge Boost: { $min-value }-{ $max-value }%
life-boost-desc =
    Tension Reduction Up: { $sub-value }%
    Constant Score Up: { $min-value }-{ $max-value }%
auto-support-desc =
    Auto Score Up: { $min-value }-{ $max-value }%
manual-support-desc =
    Manual Score Up: { $min-value }-{ $max-value }%
supportable-score-up-desc =
    Support Available
    Score Up: { $min-value }-{ $max-value }%
    Bonus Value: {$sub-value}%
    Bonus Character: { $bonus-character }
supportable-skill-longer-desc =
    Support Available
    Skill Duration Up: { $min-value }-{ $max-value }%
    Bonus Value: {$sub-value}%
    Bonus Character: { $bonus-character }
supportable-sympathy-desc =
    Support Available at +1
    Sympathy: { $min-value }-{ $max-value }%
    Multiplied by # of cards with Sympathy on team

card-id = Card Id: { $card-id }

card-search = Card Search
