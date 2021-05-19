artist = 作者資訊
artist-desc =
    作詞: { $lyricist }
    作曲: { $composer }
    改編: { $arranger }
    團體: { $unit-name }
    特殊團體: { special-unit-name }

special-unit-name = { $special-unit-name ->
    [None] { none }
   *[other] { $special-unit-name }
}

info = 資訊
song-info-desc =
    類別: { song-category-name }
    長度: { $duration }
    BPM: { $bpm }
    組曲選段: { section-trend-name }
    排序依據: { $sort-order }
    難度: { $levels }
    譜面制作: { $chart-designers }
    實裝日期: { $release-date }
    隱藏譜: { $hidden ->
        [0] { no }
       *[1] { yes }
    }
    是否適合直播: { $fair-use ->
        [0] { no }
       *[1] { yes }
    }

section-full = 全曲
section-begin = 開頭
section-middle = 中段
section-end = 尾段

section-trend-name = { $section-trend ->
   *[Full] { section-full }
    [Begin] { section-begin }
    [Middle] { section-middle }
    [End] { section-end }
}

song-category-name = { $song-category ->
    [Original] 原創
    [Cover] Cover
    [Game] 遊戲
    [Instrumental] 純樂曲
    [Collab] 合作
   *[other] Unknown
}

song-id = 歌曲ID: { $song-id }

song-search = 歌曲搜尋

chart-info-desc =
    難度: { $level }
    長度: { $duration }
    團體: { $unit-name }
    類別: { song-category-name }
    BPM: { $bpm }
    譜面制作: { $designer }
    技能時間: { $skills }
    時間Groovy: { $fever }

combo = 物量分析
combo-desc =
    總Note數: { $max-combo }
    Taps: { $tap } (暗: { $tap1 }, 亮: { $tap2 })
    轉盤: { $scratch } (左: { $scratch_left }, 右: { $scratch_right })
    轉盤長壓: { $stop } (頭: { $stop_start }, 尾: { $stop_end })
    長壓: { $long } (頭: { $long_start }, 尾: { $long_end })
    滑軌: { $slide } (拍點: { $slide_tick }, 滑鍵: { $slide_flick })

ratings = Ratings

chart-id = 譜面ID: { $chart-id }；1行 = 10秒, 技能9秒

sections-info-desc =
    難度: { $level }
    團體: { $unit-name }
    BPM: { $bpm }
    組曲選段: { section-trend-name }
    
section-desc =
    長度: { $time }
    Note數: { $combo }
