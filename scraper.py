#!/usr/bin/env python3
import json
import os
import re
import subprocess
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

EVENTS_URL = "https://hkrk.jp/event/"
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "events.json")


def scrape_events():
    resp = requests.get(EVENTS_URL, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events = []
    for li in soup.select("ul.g__list--article > li"):
        post_id = li.get("id", "")
        if not post_id:
            continue

        h3 = li.find("h3")
        if not h3:
            continue
        title = h3.get_text(strip=True)

        date_dd = li.find("dd", class_="g__list--article_date")
        if not date_dd:
            continue
        date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_dd.get_text())
        if not date_match:
            continue
        date_str = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"

        detail_url = f"https://hkrk.jp/contents/contents-{post_id}/"

        # Ticket URL from article body
        ticket_url = ""
        article = li.find("article")
        if article:
            for a in article.find_all("a", href=True):
                href = a["href"]
                if any(d in href for d in ["eplus", "tiget", "livepocket", "ticket"]):
                    ticket_url = href
                    break

        # Venue
        venue = ""
        if article:
            body = article.get_text(" ", strip=True)
            venue_match = re.search(r"会場[：:]\s*(.+?)(?:\s+TEL|\s+〒|\s*$)", body)
            if venue_match:
                venue = venue_match.group(1).strip()[:40]

        events.append(
            {
                "id": post_id,
                "title": title,
                "date": date_str,
                "venue": venue,
                "url": ticket_url or detail_url,
                "detail_url": detail_url,
                "discovered_at": datetime.now().strftime("%Y-%m-%d"),
            }
        )

    return events


def load_stored():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_events(events):
    payload = sorted(events, key=lambda e: e["date"])
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def notify_discord(new_events, webhook_url):
    for event in new_events:
        embed = {
            "title": f"🎤 新しいイベント: {event['title']}",
            "description": f"📅 {event['date']}",
            "url": event["url"],
            "color": 16744448,
        }
        if event.get("venue"):
            embed["description"] += f"\n📍 {event['venue']}"
        requests.post(webhook_url, json={"embeds": [embed]}, timeout=10)


def git_push():
    repo = os.path.dirname(__file__)
    subprocess.run(["git", "-C", repo, "add", "data/events.json"], check=True)
    result = subprocess.run(["git", "-C", repo, "diff", "--cached", "--quiet"])
    if result.returncode != 0:
        subprocess.run(
            ["git", "-C", repo, "commit", "-m", f"update events {datetime.now().strftime('%Y-%m-%d')}"],
            check=True,
        )
        subprocess.run(["git", "-C", repo, "push", "--set-upstream", "origin", "main"], check=True)
        return True
    return False


def main():
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Fetching {EVENTS_URL}")
    events = scrape_events()
    print(f"  Found {len(events)} events on page")

    stored = load_stored()
    stored_ids = {e["id"] for e in stored}

    new_events = [e for e in events if e["id"] not in stored_ids]
    print(f"  New events: {len(new_events)}")

    # Merge: keep stored events not on page (past), add new ones
    merged = {e["id"]: e for e in stored}
    for e in events:
        merged[e["id"]] = e
    save_events(list(merged.values()))

    if new_events:
        for e in new_events:
            print(f"  + {e['date']} {e['title']}")
        if webhook_url:
            notify_discord(new_events, webhook_url)
            print(f"  Discord 通知送信済み")
        else:
            print("  DISCORD_WEBHOOK_URL 未設定のため通知スキップ")

    pushed = git_push()
    if pushed:
        print("  GitHub Pages 更新完了")


if __name__ == "__main__":
    main()
