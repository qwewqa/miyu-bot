too-many-results = 結果多すぎる

info = ガチャ詳細
info-desc =
    開始: { $start-date }
    終了: { $end-date }
    イベント: { $event-name }
    天井条件: { $pity-requirement ->
        [None] { none }
       *[other] { $pity-requirement }
    }
    セレクト条件: { $select-requirement ->
        [None] { none }
       *[other] { $select-requirement }
    }
    ガチャ形式: { gacha-type }

gacha-type = { $gacha-type ->
    [Normal] 恒常
    [Tutorial] チュートリアル
    [Event] イベント
    [Birthday] バースデー
    [Special] スペシャル
    [Revival] 復刻
   *[other] Unknown
}

summary = 概要
featured = ピックアップ
featured-text = { $featured-text ->
    [None] { none }
   *[other] { $featured-text }
}
selectable = セレクト
selectable-text = { $selectable-text ->
    [None] { none }
   *[other] { $selectable-text }
}

too-many = { none }
none-or-too-many = 結果多すぎる

costs = 消費
draw-cost-desc = { $pull-count }{ $pull-count-category ->
   *[few] 回引く
    [many] 連
}: { $draw-cost }x { draw-item-name }
limit-draw-cost-desc = { draw-cost-desc }, 上限: { $draw-limit }, 更新: { $refresh ->
    [0] { no }
   *[1] { yes }
}

draw-item-name = { $draw-item-name ->
    [diamond] ダイヤ
    [paid-diamond] 有償ダイヤ
    [single-ticket] ガチャチケット
    [ten-pull-ticket] 10連ガチャチケット
    [four-star-ticket] 4★確定チケット
   *[other] { $draw-item-name }
}

gacha-id = ガチャID: { $gacha-id }

gacha-search = ガチャ検索
