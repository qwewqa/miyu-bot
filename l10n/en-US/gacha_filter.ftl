too-many-results = Too Many Results

info = Information
info-desc =
    Start: { $start-date }
    End: { $end-date }
    Event: { $event-name }
    Pity Requirement: { $pity-requirement ->
        [None] { none }
       *[other] { $pity-requirement }
    }
    Sub-Pity Requirement: { $sub-pity-requirement ->
        [None] { none }
       *[other] { $sub-pity-requirement }
    }
    Select Requirement: { $select-requirement ->
        [None] { none }
       *[other] { $select-requirement }
    }
    Type: { gacha-type }
    Category: { category }

gacha-type = { $gacha-type ->
    [Normal] Normal
    [StepUp] Step Up
    [Audition] Audition
    [Guaranteed] Guaranteed
   *[other] Unknown
}

category = { $category ->
    [Normal] Normal
    [Tutorial] Tutorial
    [Event] Event
    [Birthday] Birthday
    [StartDash] Start Dash
    [Revival] Revival
    [Special] Special
   *[other] Unknown
}

summary = Summary
featured = Featured
featured-text = { $featured-text ->
    [None] { none }
   *[other] { $featured-text }
}
selectable = Selectable
selectable-text = { $selectable-text ->
    [None] { none }
   *[other] { $selectable-text }
}

too-many = Too many
none-or-too-many = None or too many

costs = Costs
draw-cost-desc = { $pull-count } Pull: { $draw-cost }x { draw-item-name }
limit-draw-cost-desc = { draw-cost-desc }, Limit: { $draw-limit }, Refresh: { $refresh ->
    [0] { no }
   *[1] { yes }
}

draw-item-name = { $draw-item-name ->
    [diamond] Diamond
    [paid-diamond] Paid Diamond
    [single-ticket] Single Pull Ticket
    [ten-pull-ticket] Ten Pull Ticket
    [four-star-ticket] 4★ Ticket
   *[other] { $draw-item-name }
}

gacha-id = Gacha Id: { $gacha-id }

gacha-search = Gacha Search
