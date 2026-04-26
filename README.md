# ほくりくアイドル部 イベントトラッカー

公式サイト [hkrk.jp/event/](https://hkrk.jp/event/) からイベント情報を収集し、Discord通知とGitHub Pages公開を行うスクリプト。

**Web:** https://takafoi.github.io/hkrk-events/

---

## セットアップ（初回のみ）

### 1. パッケージインストール

```bash
pip3 install requests beautifulsoup4 python-dotenv
```

### 2. Discord Webhook URLの設定

1. 通知を受け取りたいDiscordチャンネルを開く
2. チャンネル設定 → 連携サービス → Webhookを作成
3. URLをコピーして `.env` に貼り付ける

```bash
# /Users/taka/Work/Claude/hkrk/.env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx/yyyyy
```

---

## 実行方法

```bash
cd /Users/taka/Work/Claude/hkrk
python3 scraper.py
```

新しいイベントが見つかった場合:
- Discordに通知が届く
- `data/events.json` が更新される
- GitHub Pages (`https://takafoi.github.io/hkrk-events/`) が自動更新される

新しいイベントがなければ何も起きない（通知なし・pushなし）。

---

## ログの確認

実行結果はターミナルに表示される。直近の `data/events.json` の日付で最終実行日がわかる。

```bash
# 最終更新日を確認
python3 -c "import json; d=json.load(open('data/events.json')); print(sorted(d, key=lambda e: e['discovered_at'])[-1]['discovered_at'])"
```

---

## ファイル構成

```
hkrk/
├── scraper.py        # メインスクリプト
├── .env              # DISCORD_WEBHOOK_URL（gitignore済み）
├── data/
│   └── events.json  # 収集したイベントデータ
└── index.html        # GitHub Pagesビューワー（このファイルは直接編集不要）
```
