#!/usr/bin/env python3
"""
每日新聞爬蟲 — 抓取國內外重大新聞，推送到 Telegram
每天 8:30 (台北時間) 由 GitHub Actions 自動觸發
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import feedparser
import requests

# ── 設定 ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
HISTORY_DIR = Path(__file__).parent / "history"
MAX_NEWS = 10  # 要取幾則

# ── RSS 來源 ───────────────────────────────────────────
# 調權重讓重要的新聞更容易上榜
RSS_FEEDS = [
    # 國際新聞（英文）
    {"url": "https://feeds.bbci.co.uk/news/world/rss.xml",      "weight": 2, "lang": "en", "label": "BBC 國際"},
    {"url": "https://feeds.bbci.co.uk/news/technology/rss.xml", "weight": 1, "lang": "en", "label": "BBC 科技"},
    # 國內新聞（繁體中文）— 中央社 via FeedBurner
    {"url": "https://feeds.feedburner.com/rsscna/intworld",      "weight": 2, "lang": "zh", "label": "中央社 國際"},
    {"url": "https://feeds.feedburner.com/rsscna/politics",      "weight": 3, "lang": "zh", "label": "中央社 政治"},
    {"url": "https://feeds.feedburner.com/rsscna/finance",       "weight": 2, "lang": "zh", "label": "中央社 產經"},
    {"url": "https://feeds.feedburner.com/rsscna/technology",    "weight": 1, "lang": "zh", "label": "中央社 科技"},
    {"url": "https://feeds.feedburner.com/rsscna/lifehealth",    "weight": 1, "lang": "zh", "label": "中央社 生活"},
]


# ── Telegram 發送 ──────────────────────────────────────
def send_telegram(text: str) -> bool:
    """透過 Telegram Bot API 發送訊息"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  未設定 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID，略過 Telegram 發送")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        print(f"✅ Telegram 發送成功（message_id={resp.json().get('result', {}).get('message_id', '?')}）")
        return True
    except Exception as e:
        print(f"❌ Telegram 發送失敗: {e}")
        return False


# ── RSS 抓取 ────────────────────────────────────────────
def fetch_news() -> list[dict]:
    """從所有 RSS 來源抓取新聞，去重後依權重排序"""
    all_articles: list[dict] = []
    seen_links: set[str] = set()

    tz_taipei = timezone(timedelta(hours=8))
    now_taipei = datetime.now(tz_taipei)

    for feed_cfg in RSS_FEEDS:
        url = feed_cfg["url"]
        weight = feed_cfg["weight"]
        lang = feed_cfg["lang"]
        label = feed_cfg["label"]

        print(f"🌐 正在抓取: {label}  ({url})")
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"   ⚠️  解析失敗: {e}")
            continue

        if not feed.entries:
            print(f"   ⚠️  無任何條目")
            continue
        print(f"   ✅ 取得 {len(feed.entries)} 條")

        for entry in feed.entries:
            link = entry.get("link", "").strip()
            if not link or link in seen_links:
                continue
            seen_links.add(link)

            title = entry.get("title", "").strip()
            summary = entry.get("summary", "").strip()
            # 清理 summary 中的 HTML 標籤
            summary = summary.replace("<p>", "").replace("</p>", "\n").replace("<br/>", "\n").strip()
            # 摘要太長就截斷
            if len(summary) > 200:
                summary = summary[:200] + "..."

            published = entry.get("published", "")
            published_parsed = entry.get("published_parsed")

            all_articles.append({
                "title": title,
                "summary": summary,
                "link": link,
                "source": label,
                "lang": lang,
                "weight": weight,
                "published": published,
                "published_parsed": published_parsed,
                "fetched_at": now_taipei.isoformat(),
            })

    # 依權重 + 時間排序（權重高、時間新的在前）
    def sort_key(a: dict) -> tuple:
        # 使用 published_parsed 或預設為最新
        import time
        pub_time = 0
        if a["published_parsed"]:
            pub_time = time.mktime(a["published_parsed"])
        return (a["weight"], pub_time)

    all_articles.sort(key=sort_key, reverse=True)

    print(f"\n📊 共抓到 {len(all_articles)} 則不重複新聞")
    return all_articles[:MAX_NEWS]


# ── 格式化 ──────────────────────────────────────────────
def format_news(articles: list[dict]) -> str:
    """將新聞列表格式化為 Telegram HTML 訊息"""
    lines = []
    tz_taipei = timezone(timedelta(hours=8))
    now_str = datetime.now(tz_taipei).strftime("%Y-%m-%d %H:%M")

    lines.append(f"<b>📰 每日新聞早報</b>\n🗓️  {now_str} (台北時間)\n{'─' * 28}\n")

    for i, art in enumerate(articles, 1):
        title = art["title"]
        source = art["source"]
        link = art["link"]
        summary = art["summary"]

        # 標題太長截斷
        display_title = title if len(title) <= 80 else title[:80] + "…"
        # 若有摘要則補上
        summary_line = f"\n   <i>{summary}</i>" if summary else ""

        lines.append(
            f"<b>{i}.</b> {display_title}\n"
            f"   🔗 {link}"
            f"{summary_line}"
        )

    lines.append(f"\n{'─' * 28}")
    lines.append("🤖 由 GitHub Actions 自動抓取・每日 8:30 準時送達")

    return "\n".join(lines)


# ── 主程式 ──────────────────────────────────────────────
def main():
    print("=" * 50)
    print("📰 新聞爬蟲啟動")
    print(f"⏰ {datetime.now()}")
    print("=" * 50)

    # 1. 抓取新聞
    articles = fetch_news()
    if not articles:
        print("❌ 未能取得任何新聞")
        sys.exit(1)

    # 2. 存 JSON 歷史
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    tz_taipei = timezone(timedelta(hours=8))
    date_str = datetime.now(tz_taipei).strftime("%Y%m%d_%H%M")
    hist_file = HISTORY_DIR / f"news_{date_str}.json"
    hist_file.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8"
    )
    print(f"📁 歷史記錄已存: {hist_file}")

    # 3. 格式化並發送 Telegram
    message = format_news(articles)
    print("\n📝 訊息預覽:")
    print(message[:500] + "…" if len(message) > 500 else message)

    success = send_telegram(message)
    if not success:
        # 即使 Telegram 失敗，也存檔成功
        print("⚠️  Telegram 發送失敗，但新聞資料已存檔")
        sys.exit(1)

    print("\n✅ 任務完成！")


if __name__ == "__main__":
    main()
