# 📰 每日新聞爬蟲

自動抓取國內外重大新聞，每天 **台北時間 8:30** 推送至 Telegram。

## 功能

- 🕷️ 從多個 RSS 來源抓取新聞
  - **國內：** 中央社即時、政治、科技
  - **國際：** BBC 國際、BBC 科技
- 📡 每日 8:30 (台北時間) 自動執行
- 📱 透過 Telegram Bot 推播 10 則重點新聞
- 📁 歷史記錄自動存檔（`history/` 目錄）

## 使用方式

### 1. Fork / Clone

```bash
git clone <你的 repo 網址>
cd news-crawler
```

### 2. 設定 GitHub Secrets

在 GitHub Repo → Settings → Secrets and variables → Actions → **New repository secret** 新增：

| Secret | 說明 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | 你的 Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | 你的 Telegram Chat ID |

### 3. 手動測試

到 GitHub → Actions → **每日新聞爬蟲** → **Run workflow** 即可立即執行。

## RSS 來源

| 來源 | 類型 | 語言 |
|---|---|---|
| [BBC 國際](https://feeds.bbci.co.uk/news/world/rss.xml) | 國際 | 英文 |
| [BBC 科技](https://feeds.bbci.co.uk/news/technology/rss.xml) | 科技 | 英文 |
| [中央社 國際](https://feeds.feedburner.com/rsscna/intworld) | 國際 | 繁體中文 |
| [中央社 政治](https://feeds.feedburner.com/rsscna/politics) | 政治 | 繁體中文 |
| [中央社 產經](https://feeds.feedburner.com/rsscna/finance) | 財經 | 繁體中文 |
| [中央社 科技](https://feeds.feedburner.com/rsscna/technology) | 科技 | 繁體中文 |
| [中央社 生活](https://feeds.feedburner.com/rsscna/lifehealth) | 生活 | 繁體中文 |

## 自訂

編輯 `news_crawler.py` 頂部的 `RSS_FEEDS` 列表即可增減新聞來源。
