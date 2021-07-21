info = イベント詳細
info-desc =
    期間: { $duration-days } 日, { $duration-hours } 時間 ({ $duration-total-hours } 時間)
    開始: { $start-date }
    終了: { $close-date }
    集計: { $rank-fix-date }
    結果: { $results-date }
    結果終了: { $end-date }
    ストーリー解放: { $story-unlock-date }
    状態: { status-name }

status-name = { $status ->
    [Upcoming] 未開催
    [Open] 開催中
    [Closing] 終了
    [Ranks_Fixed] 集計中
    [Results] 結果発表
    [Ended] 終了
   *[other] Unknown
}

event-type = イベント形式
event-type-name = { $event-type ->
    [Bingo] ビンゴ
    [Medley] メドレー
    [Poker] ポーカー
    [Raid] レイド
   *[other] { $event-type }
}

bonus-characters = キャラ特攻

bonus-attribute = タイプ特攻

point-bonus = ポイントボーナス
parameter-bonus = 総合力ボーナス
attribute = タイプ
character = キャラクター
both = 両方

bonus-description =
    { attribute }: { $attribute }
    { character }: { $character }
    { both }: { $both  ->
        [None] ボーナスなし
       *[other] { $both }
    }

parameter-point-bonus = パラメーターボーナス

parameter-point-bonus-description =
     { $parameter-bonus-rate } { $parameter-emoji } につき 1 ポイント

no-parameter-point-bonus = なし

event-id = イベントID: { $event-id }

event-search = イベント検索
