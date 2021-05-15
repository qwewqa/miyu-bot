info = Info
info-desc =
    Rarity: { $rarity }
    Character: { $character }
    Attribute: { $attribute }
    Unit: { $unit }
    Release Date: { $release-date }
    Event: { $event }
    Gacha: { $gacha }
    { availability }

availability =
    Availability: { $availability ->
            [Permanent] Permanant
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
