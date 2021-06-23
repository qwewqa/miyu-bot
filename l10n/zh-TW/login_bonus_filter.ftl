info = 資訊
info-desc =
    開始: { $start-date }
    結束: { $end-date }
    獎勵類型: { login-bonus-type-name }
    更新: { $loop ->
        [0] { no }
       *[1] { yes }
    }

login-bonus-type-name = { $login-bonus-type ->
    [Common] 週登入
    [Campaign] 活動
    [Subscription] 月卡
    [VipBronze] 銅里程卡
    [VipSilver] 銀里程卡
    [VipGold] 金里程卡
    [VipPlatinum] 白金里程卡
   *[other] Unknown
}

rewards = 獎勵

too-many-results = 結果過多

login-bonus-id = 登入獎勵ID: { $login-bonus-id }

login-bonus-search = 登入獎勵搜尋
