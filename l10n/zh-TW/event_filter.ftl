info = 資訊
info-desc =
    持續時間: { $duration-days }日, { $duration-hours }小時 ({ $duration-total-hours } 小時)
    開始: { $start-date }
    關閉: { $close-date }
    等級修正: { $rank-fix-date }
    結算: { $results-date }
    結束: { $end-date }
    故事解鎖: { $story-unlock-date }
    狀態: { status-name }

status-name = { $status ->
    [Upcoming] 即將上線
    [Open] 開啟
    [Closing] 關閉
    [Ranks_Fixed] 等級修正
    [Results] 結算
    [Ended] 已結束
   *[other] Unknown
}

event-type = 活動類型
event-type-name = { $event-type ->
    [Bingo] Bingo
    [Medley] 組曲
    [Poker] 德州撲克
    [Raid] 討伐
   *[other] { $event-type }
}

bonus-characters = 加成角色

bonus-attribute = 加成屬性

point-bonus = Pt加成
parameter-bonus = 能力值加成
attribute = 屬性
character = 角色
both = 屬性+角色

bonus-description =
    { attribute }: { $attribute }
    { character }: { $character }
    { both }: { $both  ->
        [None] 無加成
       *[other] { $both }
    }

parameter-point-bonus = 能力值加成

parameter-point-bonus-description =
     每 { $parameter-bonus-rate } { $parameter-emoji }

no-parameter-point-bonus = 無加成

event-id = 活動ID: { $event-id }

event-search = 活動搜尋
