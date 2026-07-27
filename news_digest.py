"""
news_digest.py

Pulls daily articles from behavioral health / addiction / mental health
trade press RSS feeds, filters for relevance (for the broader feeds that
aren't already niche-dedicated), tags each article by topic, and writes
a rolling digest to docs/articles.json for the dashboard to read.

No API key required -- these are public RSS feeds.
"""

import json
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import feedparser
import requests

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

# requires_filter=False means every article from this feed is kept (it's
# already dedicated to the field). requires_filter=True means an article
# only gets kept if it matches at least one of the TOPIC_KEYWORDS below --
# use this for broad general-healthcare feeds so they don't flood the digest
# with irrelevant stories.
FEEDS = [
    {"name": "Behavioral Health Business", "url": "https://bhbusiness.com/feed", "requires_filter": False},
    {"name": "Psychiatric Times", "url": "https://www.psychiatrictimes.com/rss.xml", "requires_filter": False},
    {"name": "MindSite News", "url": "https://mindsitenews.org/feed", "requires_filter": False},
    {"name": "Healthcare Dive", "url": "https://www.healthcaredive.com/feeds/news", "requires_filter": True},
]

# Topic tags: each list is scanned against the article's title + summary.
# An article can match multiple topics.
TOPIC_KEYWORDS = {
    "substance-use-disorder": [
        "substance use", "addiction", "opioid", "detox", "sober",
        "recovery center", "rehab", "sud ", "fentanyl", "alcohol use",
    ],
    "mental-health": [
        "mental health", "psychiatric", "depression", "anxiety",
        "behavioral health",
    ],
    "eating-disorder": [
        "eating disorder", "anorexia", "bulimia", "binge eating",
    ],
    "gambling": [
        "gambling disorder", "problem gambling", "gaming disorder",
    ],
    "deals-and-ma": [
        "acquisition", "acquires", "acquired", "merger", "private equity",
        "raises $", "funding round", "series a", "series b", "series c",
        "investment", "ipo", "divest",
    ],
    "policy-and-regulation": [
        "legislation", "regulation", "cms ", "medicaid", "medicare",
        " bill ", "congress", "policy", "reimbursement",
    ],
}

MAX_AGE_DAYS = 30

DATA_DIR = Path(__file__).parent / "docs"
ARTICLES_FILE = DATA_DIR / "articles.json"
SEEN_FILE = Path(__file__).parent / "seen_article_ids.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PersonalNewsDigestBot/1.0; +https://github.com/)"
}

# ---------------------------------------------------------------------------


def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return default
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def parse_published(entry):
    for key in ("published", "updated"):
        val = entry.get(key)
        if val:
            try:
                return parsedate_to_datetime(val).astimezone(timezone.utc).isoformat()
            except (TypeError, ValueError):
                continue
    return datetime.now(timezone.utc).isoformat()


def tag_topics(text):
    text = text.lower()
    return [topic for topic, keywords in TOPIC_KEYWORDS.items()
            if any(kw in text for kw in keywords)]


def fetch_feed(feed_conf):
    try:
        resp = requests.get(feed_conf["url"], headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[warn] could not fetch {feed_conf['name']!r}: {e}")
        return []

    parsed = feedparser.parse(resp.content)
    if parsed.bozo and not parsed.entries:
        print(f"[warn] feed for {feed_conf['name']!r} didn't parse cleanly: {parsed.bozo_exception}")
    return parsed.entries


def normalize(entry, feed_conf):
    title = (
        entry.get("title")
        or entry.get("title_detail", {}).get("value")
        or ""
    ).strip()

    summary = (
        entry.get("summary")
        or entry.get("description")
        or entry.get("summary_detail", {}).get("value")
        or (entry.get("content", [{}])[0].get("value") if entry.get("content") else None)
        or ""
    ).strip()

    if not title:
        print(f"[warn] empty title from {feed_conf['name']!r}. "
              f"Available entry keys: {list(entry.keys())} | "
              f"link: {entry.get('link')}")

    combined_text = f"{title} {summary}"
    topics = tag_topics(combined_text)

    if feed_conf["requires_filter"] and not topics:
        return None  # not relevant enough to keep from a broad feed

    return {
        "id": entry.get("id") or entry.get("link"),
        "title": title or "(untitled -- see apply link)",
        "link": entry.get("link"),
        "source": feed_conf["name"],
        "published_at": parse_published(entry),
        "summary": summary[:500],
        "topics": topics,
        "first_seen": datetime.now(timezone.utc).isoformat(),
    }


def main():
    seen_ids = set(load_json(SEEN_FILE, []))
    existing = load_json(ARTICLES_FILE, [])

    new_articles = []
    for feed_conf in FEEDS:
        entries = fetch_feed(feed_conf)
        kept = 0
        for entry in entries:
            article = normalize(entry, feed_conf)
            if article is None:
                continue
            if not article["id"] or article["id"] in seen_ids:
                continue
            seen_ids.add(article["id"])
            new_articles.append(article)
            kept += 1
        print(f"{feed_conf['name']}: {len(entries)} entries fetched, {kept} new & relevant")
        time.sleep(1)

    combined = new_articles + existing
    cutoff = time.time() - MAX_AGE_DAYS * 86400
    combined = [a for a in combined if _parse_ts(a.get("first_seen")) > cutoff]
    combined.sort(key=lambda a: a.get("published_at") or "", reverse=True)

    save_json(ARTICLES_FILE, combined)
    save_json(SEEN_FILE, list(seen_ids))

    print(f"Added {len(new_articles)} new article(s). Total tracked: {len(combined)}.")


def _parse_ts(iso_str):
    if not iso_str:
        return 0
    try:
        return datetime.fromisoformat(iso_str).timestamp()
    except ValueError:
        return 0


if __name__ == "__main__":
    main()
