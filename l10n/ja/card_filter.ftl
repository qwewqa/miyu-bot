info = メンバー詳細
info-desc =
    レアリティ: { $rarity }
    キャラクター: { $character }
    スタイル: { $attribute }
    ユニット: { $unit }
    初登場: { $release-date }
    イベント: { $event }
    ガチャ: { $gacha }
    入手方法: { availability-name }

availability-name = { $availability ->
    [Permanent] 恒常
    [Limited] 期間限定
    [Collab] コラボ
    [Birthday] 誕生日
    [Welfare] 報酬
   *[other] 不明
}

parameters = ステータス
parameters-desc =
    総合力: { $total }
    { $heart-emoji } ハート: { $heart }
    { $technique-emoji } テクニック: { $technique }
    { $physical-emoji } フィジカル: { $physical }

skill = ステータス
skill-desc =
    スキル名: { $name }
    スキル時間: { $duration }
    スコアUP: { $score-up }
    回復: { $heal }

card-id = メンバーID: { $card-id }

card-search = メンバー検索