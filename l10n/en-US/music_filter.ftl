artist = Artist
artist-desc =
    Lyricist: { $lyricist }
    Composer: { $composer }
    Arranger: { $arranger }
    Unit: { $unit-name }
    Special Unit Name: { special-unit-name }

special-unit-name = { $special-unit-name ->
    [None] { none }
   *[other] { $special-unit-name }
}

info = Information
song-info-desc =
    Category: { song-category-name }
    Duration: { $duration }
    BPM: { $bpm }
    Section Trend: { section-trend-name }
    Sort Order: { $sort-order }
    Levels: { $levels }
    Chart Designers: { $chart-designers }
    Release Date: { $release-date }
    Hidden: { $hidden ->
        [0] { no }
       *[1] { yes }
    }
    Fair Use: { $fair-use ->
        [0] { no }
       *[1] { yes }
    }

section-full = Full
section-begin = Begin
section-middle = Middle
section-end = End

section-trend-name = { $section-trend ->
   *[Full] { section-full }
    [Begin] { section-begin }
    [Middle] { section-middle }
    [End] { section-end }
}

song-category-name = { $song-category ->
    [Original] Original
    [Cover] Cover
    [Game] Game
    [Instrumental] Instrumental
    [Collab] Collab
   *[other] Unknown
}

song-id = Song Id: { $song-id }

song-search = Song Search

chart-info-desc =
    Level: { $level }
    Duration: { $duration }
    Unit: { $unit-name }
    Category: { song-category-name }
    BPM: { $bpm }
    Designer: { $designer }
    Skills: { $skills }
    Fever: { $fever }

combo = Combo
combo-desc =
    Max Combo: { $max-combo }
    Taps: { $tap } (dark: { $tap1 }, light: { $tap2 })
    Scratches: { $scratch } (left: { $scratch_left }, right: { $scratch_right })
    Stops: { $stop } (head: { $stop_start }, tail: { $stop_end })
    Longs: { $long } (head: { $long_start }, tail: { $long_end })
    Slides: { $slide } (tick: { $slide_tick }, flick: { $slide_flick })

ratings = Ratings

chart-id = Chart Id: { $chart-id }; 1 column = 12 seconds, 9 second skills

sections-info-desc =
    Level: { $level }
    Unit: { $unit-name }
    BPM: { $bpm }
    Section Trend: { section-trend-name }
    
section-desc =
    Time: { $time }
    Combo: { $combo }
