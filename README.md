# Abracada What Bot

> A Abracada What game bot inspired by [mau_mau_bot](https://github.com/jh0ker/mau_mau_bot)

## 遊玩

將 [@AbracadaWhatBot](https://t.me/abracadawhatbot) 加到群組中即可遊玩！

## 自架

1. 找 BotFather (@BotFather) 建 Bot
2. 將 token 填入 `config.json`
3. 將 Bot 的 inlinemode 設為 Enable 並將 placeholder 設成 `🔼 選牌 🔼`
4. 將 inlinefeedback 設為 Enable
5. 設定 command list 從 `commandlist.txt` 複製
6. 安裝依賴 `pip install -r requirements.txt`
7. 執行 `python bot.py`

## 流程

1. 初始化

   - 系統分配每人 5 張魔法石
   - 決定當前玩家並建一個循環鏈結串列

2. 當前玩家選擇要施展的魔法

   - 成功可繼續施展或跳過
   - 失敗自動跳過並扣 1 點血
   - 換下一位玩家直到有人死亡或有人將魔法施展完畢
