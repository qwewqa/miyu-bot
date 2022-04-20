info = Information
info-desc =
    Rarity: { $rarity }
    Character: { $character }
    Attribute: { $attribute }
    Unit: { $unit }
    Release Date: { $release-date }
    Gacha: { $gacha }

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
    Score Up: { $score-up }
    Heal: { $heal }

passive = Passive
passive-desc = { $type ->
    [FeverBonus] { groovy-bonus-desc }
    [FeverSupport] { groovy-support-desc }
    [ScoreUpWithDamage] { life-boost-desc }
    [AutoScoreUp] { auto-support-desc }
   *[other] None
}
groovy-bonus-desc =
    Groovy Score Up: { $min-value }% - { $max-value }%
groovy-support-desc =
    Solo Groovy
    Groovy Charge Boost: { $min-value }% - { $max-value }%
life-boost-desc =
    Tension Reduction Up: { $sub-value }%
    Constant Score Up: { $min-value }% - { $max-value }%
auto-support-desc =
    Auto Score Up: { $min-value }% - { $max-value }%

card-id = Card Id: { $card-id }

card-search = Card Search
