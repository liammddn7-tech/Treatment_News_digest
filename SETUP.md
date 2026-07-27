# Behavioral Health Industry News Digest — Setup Guide

Pulls daily news from behavioral health / addiction / mental health trade
press (Behavioral Health Business, Psychiatric Times, MindSite News, plus
filtered stories from Healthcare Dive), and shows it on a dashboard you can
check whenever — deals & M&A, policy/regulation, and news specific to SUD,
mental health, eating disorder, and gambling treatment.

**No API key needed** — these are public RSS feeds, so setup is a bit
simpler than the job search agent.

## 1. Create a GitHub repo (or add this to a new folder in an existing one)

Create a new repo, e.g. `industry-news-digest`, and upload all the files
here (news_digest.py, `.github/workflows/`, and `docs/`), preserving the
folder structure. Since `.github` is a dot-folder, GitHub's drag-and-drop
upload can miss it — if that happens, use **Add file → Create new file**
and type the full path `.github/workflows/daily-news-digest.yml` into the
filename box (GitHub creates the folders automatically), then paste the
contents in.

## 2. Turn on GitHub Pages

1. **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: **main**, folder: **/docs** → Save
4. Your dashboard URL will show up as `https://yourusername.github.io/industry-news-digest/`

## 3. Run it once manually

**Actions** tab → **Daily News Digest** (left sidebar) → **Run workflow**
button → confirm. Wait ~30 seconds, then check the dashboard.

After that, it runs automatically every morning (7am ET / 11:00 UTC —
change the `cron:` line in the workflow file if you want a different time).

## Tuning it

Open `news_digest.py` and edit:
- **`FEEDS`** — add or remove RSS sources. Set `requires_filter: True` for
  any broad, non-specialized feed you add (so it only keeps relevant
  stories), or `False` for feeds already dedicated to behavioral health.
- **`TOPIC_KEYWORDS`** — add more keywords per category, or add a whole new
  topic category (just add a new key with its own keyword list — it'll
  automatically show up as a filter button on the dashboard).

## Honest limitations

- **RSS feed reliability varies.** Some sites occasionally change their feed
  URL or add bot protection. If a feed stops working, the log for that run
  will show a `[warn] could not fetch...` line — paste it back if you want
  help fixing it.
- **Keyword filtering isn't perfect.** The broad feeds (like Healthcare
  Dive) are filtered by keyword match, so an occasional relevant story might
  get missed if it doesn't use expected phrasing, or an occasional
  borderline story might sneak through.
