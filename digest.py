# -*- coding: utf-8 -*-
"""
Ранковий дайджест у Telegram.

Як обираються головні новини:
  1. Схожі заголовки з різних джерел об'єднуються в одну "тему".
  2. Чим більше незалежних джерел пишуть про тему — тим вона важливіша.
  3. Щоб не було бульбашки, в дайджест обов'язково потрапляє
     хоча б одна новина з кожного розділу.

Потрібні налаштування (GitHub → Settings → Secrets and variables → Actions):
  TELEGRAM_TOKEN   — токен бота від @BotFather
  TELEGRAM_CHAT_ID — твій числовий ID у Telegram
"""
import html
import os
import re
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from fetch_news import collect

DIGEST_SIZE = 10        # скільки новин у дайджесті
HOURS = 24              # беремо новини за останню добу
KYIV = ZoneInfo("Europe/Kyiv")

STOP = set("""
the a an and or of to in on for with at by from as is are was were be been has have had
it its this that after over into about amid says said new will could would more than not
та і й в у на з із до за про що як це від для по при після через його її їх вже ще
""".split())


def stems(title):
    """Ключові "корені" слів заголовка — щоб порівнювати схожі новини."""
    words = re.findall(r"[a-zа-яіїєґ0-9']+", title.lower())
    return {w[:5] for w in words if len(w) >= 4 and w not in STOP}


def same_story(a, b):
    common = a & b
    if len(common) < 2:
        return False
    return len(common) / min(len(a), len(b)) >= 0.4


def cluster(items):
    """Групує новини з різних джерел, які розповідають про одну подію."""
    groups = []
    for it in items:
        st = stems(it["title"])
        if not st:
            continue
        for g in groups:
            if same_story(st, g["stems"]):
                g["items"].append(it)
                g["stems"] |= st
                break
        else:
            groups.append({"stems": set(st), "items": [it]})
    for g in groups:
        g["sources"] = {i["source"] for i in g["items"]}
        g["main"] = g["items"][0]                # найсвіжіша новина теми
        g["cat"] = g["main"]["cat"]
        g["score"] = len(g["sources"])
        g["ts"] = max(i["ts"] for i in g["items"])
    return groups


def pick(groups, categories):
    ranked = sorted(groups, key=lambda g: (g["score"], g["ts"]), reverse=True)
    chosen = []
    # 1) по одній найкращій темі з кожного розділу — проти бульбашки
    for c in categories:
        best = next((g for g in ranked if g["cat"] == c["id"]), None)
        if best:
            chosen.append(best)
    # 2) решту місць займають теми, про які пише найбільше джерел
    for g in ranked:
        if len(chosen) >= DIGEST_SIZE:
            break
        if g not in chosen:
            chosen.append(g)
    return sorted(chosen[:DIGEST_SIZE], key=lambda g: (g["score"], g["ts"]), reverse=True)


def format_message(chosen, categories, site_url):
    titles = {c["id"]: c["title"] for c in categories}
    today = datetime.now(KYIV)
    months = ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня",
              "серпня", "вересня", "жовтня", "листопада", "грудня"]
    lines = [f"☕ <b>Ранковий дайджест · {today.day} {months[today.month - 1]}</b>", ""]
    for n, g in enumerate(chosen, 1):
        m = g["main"]
        tag = f"🔥 {g['score']} джерела · " if g["score"] >= 2 else ""
        lang = " 🇬🇧" if m["lang"] == "en" else ""
        lines.append(f"{n}. <b>{html.escape(m['title'])}</b>{lang}")
        lines.append(f"<i>{tag}{titles.get(g['cat'], '')} · </i>"
                     f"<a href=\"{html.escape(m['link'] or '')}\">{html.escape(m['source'])}</a>")
        lines.append("")
    if site_url:
        lines.append(f"📰 <a href=\"{html.escape(site_url)}\">Усі новини →</a>")
    return "\n".join(lines)


def send(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Немає TELEGRAM_TOKEN або TELEGRAM_CHAT_ID — показую дайджест тут:\n")
        print(text)
        return
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=20, json={
        "chat_id": chat, "text": text, "parse_mode": "HTML",
        "disable_web_page_preview": True,
    })
    if not r.ok:
        sys.exit(f"Telegram не прийняв повідомлення: {r.status_code} {r.text[:200]}")
    print("Дайджест надіслано ✅")


def right_time():
    """
    GitHub рахує час у UTC, а в Україні він змінюється (зимовий/літній).
    Тому розклад має два запуски, і тут вирішуємо, який із них — справжні 8:00 за Києвом.
    """
    trigger = os.environ.get("SCHEDULE", "")
    if not trigger:                       # ручний запуск кнопкою — надсилаємо завжди
        return True
    offset = datetime.now(KYIV).utcoffset().total_seconds() / 3600
    utc_hour = int(trigger.split()[1])
    return utc_hour + offset == 8


def main():
    if not right_time():
        print("Зараз не 8:00 за Києвом — пропускаю цей запуск.")
        return
    data = collect()
    fresh = [i for i in data["items"] if time.time() - i["ts"] <= HOURS * 3600]
    chosen = pick(cluster(fresh), data["categories"])
    if not chosen:
        print("Немає свіжих новин.")
        return
    send(format_message(chosen, data["categories"], os.environ.get("SITE_URL", "")))


if __name__ == "__main__":
    main()
