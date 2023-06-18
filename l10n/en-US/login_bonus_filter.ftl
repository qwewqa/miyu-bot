info = Information
info-desc =
    Start: { $start-date }
    End: { $end-date }
    Type: { login-bonus-type-name }
    Loop: { $loop ->
        [0] { no }
       *[1] { yes }
    }

login-bonus-type-name = { $login-bonus-type ->
    [Common] Common
    [Campaign] Campaign
    [Subscription] Subscription
    [VipBronze] Bronze Mileage
    [VipSilver] Silver Mileage
    [VipGold] Gold Mileage
    [VipPlatinum] Platinum Mileage
    [EventBingo] Bingo
    [EventMedley] Medley
    [EventPoker] Poker
    [EventRaid] Raid
    [EventSlot] Slot
    [EventGrow] Grow
    [EventRave] Rave
   *[other] Unknown
}

too-many-results = Too Many Results


rewards = Rewards

login-bonus-id = Login Bonus Id: { $login-bonus-id }

login-bonus-search = Login Bonus Search
