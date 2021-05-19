artist = 作者詳細
artist-desc =
    作詞: { $lyricist }
    作曲: { $composer }
    編曲: { $arranger }
    ユニット: { $unit-name }
    スペシャル: { special-unit-name }

special-unit-name = { $special-unit-name ->
    [None] ユニット名なし
   *[other] { $special-unit-name }
}

info = 楽曲詳細
song-info-desc =
    カテゴリー: { song-category-name }
    時間: { $duration }
    BPM: { $bpm }
    Section Trend: { section-trend-name }
    ソート: { $sort-order }
    レベル: { $levels }
    譜面製作者: { $chart-designers }
    追加日時: { $release-date }
    非表示: { $hidden ->
        [0] { no }
       *[1] { yes }
    }
    配信可能: { $fair-use ->
        [0] { no }
       *[1] { yes }
    }

section-full = 全曲
section-begin = 序盤
section-middle = 中盤
section-end = 終盤

section-trend-name = { $section-trend ->
   *[Full] { section-full }
    [Begin] { section-begin }
    [Middle] { section-middle }
    [End] { section-end }
}

song-category-name = { $song-category ->
    [Original] オリジナル
    [Cover] カバー
    [Game] ゲーム
    [Instrumental] インスト
    [Collab] 原曲
   *[other] Unknown
}

song-id = 楽曲ID: { $song-id }

song-search = 譜面検索

chart-info-desc =
    レベル: { $level }
    時間: { $duration }
    ユニット: { $unit-name }
    カテゴリー: { song-category-name }
    BPM: { $bpm }
    譜面制作者: { $designer }
    スキルタイム: { $skills }
    グルービー: { $fever }

combo = ノーツ構成
combo-desc =
    総ノーツ数: { $max-combo }
    タップ: { $tap } (青: { $tap1 }, 水色: { $tap2 })
    スクラッチ: { $scratch } (左: { $scratch_left }, 右: { $scratch_right })
    ホールド: { $stop } (始: { $stop_start }, 終: { $stop_end })
    ロング: { $long } (始: { $long_start }, 終: { $long_end })
    スライダー: { $slide } (ノーマル: { $slide_tick }, フリック: { $slide_flick })

ratings = Ratings

chart-id = 譜面ID: { $chart-id }; 1 行 = 10 秒, スキル9秒

sections-info-desc =
    レベル: { $level }
    ユニット: { $unit-name }
    BPM: { $bpm }
    Section Trend: { section-trend-name }
    
section-desc =
    長さ: { $time }
    コンボ数: { $combo }
