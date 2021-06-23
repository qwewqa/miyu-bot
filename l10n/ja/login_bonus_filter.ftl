info = 詳細
info-desc =
    開始: { $start-date }
    終了: { $end-date }
    形式: { login-bonus-type-name }
    恒常: { $loop ->
        [0] { no }
       *[1] { yes }
    }

login-bonus-type-name = { $login-bonus-type ->
    [Common] 通常
    [Campaign] キャンペーン
    [Subscription] サブスクリプション
    [VipBronze] ブロンズマイレージ
    [VipSilver] シルバーマイレージ
    [VipGold] ゴールドマイレージ
    [VipPlatinum] プラチナマイレージ
   *[other] Unknown
}

too-many-results = 結果多すぎる

rewards = 報酬

login-bonus-id = ログインボーナスID: { $login-bonus-id }

login-bonus-search = ログインボーナス検索
