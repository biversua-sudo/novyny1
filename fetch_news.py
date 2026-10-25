# -*- coding: utf-8 -*-
"""
Збирає свіжі новини з усіх джерел і складає готовий сайт у папку site/.
GitHub запускає цей скрипт автоматично кожні 30 хвилин.

Запуск вручну:  python fetch_news.py
"""
import html
import json
import re
import shutil
import time
from calendar import timegm
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote_plus

import feedparser
import requests

from sources import CATEGORIES, SOURCES

MAX_AGE_HOURS = 48     # показувати новини не старші за 48 годин
MAX_PER_SOURCE = 15    # максимум новин з одного джерела
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NovynyReader/1.0; RSS reader)"}

ROOT = Path(__file__).parent
WEB = ROOT / "web"      # шаблон сайту
SITE = ROOT / "site"    # готовий сайт, який публікує GitHub


def google_news_url(site, lang):
    """Запасний шлях: новини конкретного сайту через Google News RSS."""
    q = quote_plus(f"site:{site} when:2d")
    if lang == "uk":
        return f"https://news.google.com/rss/search?q={q}&hl=uk&gl=UA&ceid=UA:uk"
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"


def clean_text(raw, limit=220):
    """Прибирає HTML-теги і обрізає текст до короткого опису."""
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def entry_time(e):
    for key in ("published_parsed", "updated_parsed"):
        if e.get(key):
            return timegm(e[key])
    return None


def entry_image(e):
    for key in ("media_content", "media_thumbnail"):
        for m in e.get(key) or []:
            if m.get("url"):
                return m["url"]
    for link in e.get("links") or []:
        if link.get("type", "").startswith("image"):
            return link.get("href")
    return None


def download(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.content


def parse(src, url, via_google):
    feed = feedparser.parse(download(url))
    now = time.time()
    items = []
    for e in feed.entries:
        ts = entry_time(e)
        if ts and now - ts > MAX_AGE_HOURS * 3600:
            continue
        title = clean_text(e.get("title"), 300)
        if via_google:
            # Google News дописує " - Назва сайту" в кінці заголовка — прибираємо
            site_name = (e.get("source") or {}).get("title")
            if site_name and title.endswith(" - " + site_name):
                title = title[: -len(site_name) - 3]
            elif " - " in title and len(title.rsplit(" - ", 1)[1]) <= 40:
                title = title.rsplit(" - ", 1)[0]
        if not title:
            continue
        items.append({
            "title": title,
            "link": e.get("link"),
            "summary": "" if via_google else clean_text(e.get("summary") or e.get("description")),
            "image": None if via_google else entry_image(e),
            "ts": int(ts or now),
            "source": src["name"],
            "cat": src["cat"],
            "lang": src["lang"],
        })
        if len(items) >= MAX_PER_SOURCE:
            break
    return items


def fetch_source(src):
    """Пробує основну стрічку, а якщо не вийшло — Google News по сайту."""
    attempts = []
    if src.get("url"):
        attempts.append((src["url"], False))
    if src.get("site"):
        attempts.append((google_news_url(src["site"], src["lang"]), True))
    last_error = "немає адреси"
    for url, via_google in attempts:
        try:
            items = parse(src, url, via_google)
            if items:
                return items, {"source": src["name"], "ok": True,
                               "via": "google" if via_google else "rss", "count": len(items)}
            last_error = "порожня стрічка"
        except Exception as ex:  # сайт недоступний, тайм-аут тощо
            last_error = type(ex).__name__
    return [], {"source": src["name"], "ok": False, "error": last_error, "count": 0}


def collect():
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(fetch_source, SOURCES))
    items, status, seen = [], [], set()
    for its, st in results:
        status.append(st)
        for it in its:
            key = it["title"].lower()[:80]
            if key in seen:          # прибираємо дублікати
                continue
            seen.add(key)
            items.append(it)
    items.sort(key=lambda x: x["ts"], reverse=True)
    return {"updated": int(time.time()), "categories": CATEGORIES, "items": items, "status": status}


def build():
    data = collect()
    if SITE.exists():
        shutil.rmtree(SITE)
    shutil.copytree(WEB, SITE)
    (SITE / "news.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    ok = sum(s["ok"] for s in data["status"])
    print(f"Готово: {len(data['items'])} новин, працює джерел {ok} з {len(data['status'])}")
    for s in data["status"]:
        print(("  ✓ " if s["ok"] else "  ✗ ") + s["source"] + (f" ({s.get('via')})" if s["ok"] else f" — {s['error']}"))


if __name__ == "__main__":
    build()
