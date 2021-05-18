too-many-results = 結果過多

info = 資訊
info-desc =
    開始: { $start-date }
    結束: { $end-date }
    活動: { $event-name }
    保底抽數: { $pity-requirement ->
        [None] 無保底
       *[other] { $pity-requirement }
    }
    類型: { gacha-type }

gacha-type = { $gacha-type ->
    [Normal] 一般
    [Tutorial] 教學
    [Event] 活動限定
    [Birthday] 生日限定
    [Special] 新手池
    [Revival] 復刻
   *[other] -> Unknown
}

summary = 結果
featured = Pick up
featured-text = { $featured-text ->
    [None] { no-data }
   *[other] { $featured-text }
}

too-many = 太多
none-or-too-many = 沒有或太多

costs = 消費
draw-cost-desc = { $pull-count } 抽卡: { $draw-cost }x { draw-item-name }
limit-draw-cost-desc = { draw-cost-desc }, 上限: { $draw-limit }, 更新: { $refresh ->
    [0] { no }
   *[1] { yes }
}

draw-item-name = { $draw-item-name ->
    [diamond] 鑽石
    [paid-diamond] 支付鑽石
    [single-ticket] 單抽券
    [ten-pull-ticket] 十抽券
    [four-star-ticket] 四星券
   *[other] { $draw-item-name }
}

gacha-id = 卡池ID: { $gacha-id }

gacha-search = 卡池搜尋
