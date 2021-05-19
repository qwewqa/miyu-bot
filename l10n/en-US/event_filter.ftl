info = Information
info-desc =
    Duration: { $duration-days } days, { $duration-hours } hours ({ $duration-total-hours } hours)
    Start: { $start-date }
    Close: { $close-date }
    Rank Fix: { $rank-fix-date }
    Results: { $results-date }
    End: { $end-date }
    Story Unlock: { $story-unlock-date }
    Status: { status-name }

status-name = { $status ->
    [Upcoming] Upcoming
    [Open] Open
    [Closing] Closing
    [Ranks_Fixed] Ranks Fixed
    [Results] Results
    [Ended] Ended
   *[other] Unknown
}

event-type = Event Type
event-type-name = { $event-type ->
    [Bingo] Bingo
    [Medley] Medley
    [Poker] Poker
    [Raid] Raid
   *[other] Unknown
}

bonus-characters = Bonus Characters

bonus-attribute = Bonus Attribute

point-bonus = Point Bonus
parameter-bonus = Parameter Bonus
attribute = Attribute
character = Character
both = Both

bonus-description =
    { attribute }: { $attribute }
    { character }: { $character }
    { both }: { $both  ->
        [None] { none }
       *[other] { $both }
    }

event-id = Event Id: { $event-id }

event-search = Event Search
