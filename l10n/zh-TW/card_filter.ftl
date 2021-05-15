info = 資訊

info-desc =
    星數: { $rarity }
    角色: { $character }
    屬性: { $attribute }
    組合: { $unit }
    上架日期: { $release-date }
    活動: { $event }
    抽池: { $gacha }
    { availability }

availability =
    取得方法: { $availability ->
        [Permanent] 恆常
        [Limited] 限定
        [Collab] 合作限定
        [Birthday] 生日限定
        [Welfare] 活動報酬
        *[other] Unknown
    }

parameters = 卡片能力
parameters-desc =
    總合: { $total }
    { $heart-emoji } Heart: { $heart }
    { $technique-emoji } Technique: { $technique }
    { $physical-emoji } Physical: { $physical }

skill = 技能
skill-desc =
    名稱: { $name }
    發動時間: { $duration }
    加分: { $score-up }
    體力回復: { $heal }
