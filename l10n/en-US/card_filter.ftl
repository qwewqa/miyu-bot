info = Info

info-desc =
    Rarity: { $rarity }
    Character: { $character }
    Attribute: { $attribute }
    Unit: { $unit }
    Release Date: { $release_date }
    Event: { $event }
    Gacha: { $gacha }
    Availability: { $availability ->
        [Permanent] Permanant
        [Limited] Limited
        [Collab] Collab
        [Birthday] Birthday
        [Welfare] Reward
        *[other] Unknown
    }