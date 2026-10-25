# -*- coding: utf-8 -*-
"""
Список джерел новин.

Щоб додати нове джерело — просто додай ще один рядок у потрібний розділ.
  name      — як джерело підписане в програмі
  url       — адреса RSS-стрічки сайту (None, якщо в сайту її немає)
  site      — домен сайту. Якщо стрічка не працює, програма сама візьме
              новини цього сайту через Google News (запасний шлях)
  lang      — мова джерела: "uk" або "en"
"""

CATEGORIES = [
    {"id": "world",   "title": "Світ"},
    {"id": "ukraine", "title": "Україна"},
    {"id": "business","title": "Бізнес"},
    {"id": "fintech", "title": "Фінтех"},
    {"id": "miltech", "title": "Мілтех"},
    {"id": "opinion", "title": "Інша думка"},
]

SOURCES = [
    # ---------- Світ ----------
    {"cat": "world", "name": "AP", "url": None,
     "site": "apnews.com", "lang": "en"},
    {"cat": "world", "name": "Reuters", "url": None,
     "site": "reuters.com/world", "lang": "en"},
    {"cat": "world", "name": "The Guardian", "url": "https://www.theguardian.com/world/rss",
     "site": "theguardian.com/world", "lang": "en"},

    # ---------- Україна ----------
    {"cat": "ukraine", "name": "Kyiv Independent", "url": "https://kyivindependent.com/news-archive/rss/",
     "site": "kyivindependent.com", "lang": "en"},
    {"cat": "ukraine", "name": "Суспільне", "url": "https://suspilne.media/rss/all.rss",
     "site": "suspilne.media", "lang": "uk"},

    # ---------- Бізнес і економіка ----------
    {"cat": "business", "name": "Економічна правда", "url": "https://www.epravda.com.ua/rss/",
     "site": "epravda.com.ua", "lang": "uk"},
    {"cat": "business", "name": "Reuters Business", "url": None,
     "site": "reuters.com/business", "lang": "en"},
    {"cat": "business", "name": "AIN.ua", "url": "https://ain.ua/feed/",
     "site": "ain.ua", "lang": "uk"},

    # ---------- Фінтех ----------
    {"cat": "fintech", "name": "This Week in Fintech", "url": None,
     "site": "thisweekinfintech.com", "lang": "en"},
    {"cat": "fintech", "name": "Finextra", "url": "https://www.finextra.com/rss/headlines.aspx",
     "site": "finextra.com", "lang": "en"},

    # ---------- Мілтех ----------
    {"cat": "miltech", "name": "Defense Express", "url": None,
     "site": "defence-ua.com", "lang": "uk"},
    {"cat": "miltech", "name": "Breaking Defense", "url": "https://breakingdefense.com/feed/",
     "site": "breakingdefense.com", "lang": "en"},

    # ---------- Інша думка (колонки) ----------
    {"cat": "opinion", "name": "Guardian Opinion", "url": "https://www.theguardian.com/commentisfree/rss",
     "site": "theguardian.com/commentisfree", "lang": "en"},
    {"cat": "opinion", "name": "Reuters Breakingviews", "url": None,
     "site": "reuters.com/breakingviews", "lang": "en"},
]
