"""Review collection from Google Play and the Apple App Store.

Both endpoints are public and need no credentials. Google Play is queried
through google-play-scraper per language (Arabic first, with its own budget,
so the Arabic pass is never starved by the larger English volume); the App
Store is read from the public RSS customer-reviews feed, ten pages per app.

The run is resumable: completed apps are written to a checkpoint file and the
dedup sets are rebuilt from whatever is already on disk. The raw file this
produced on 2026-07-19 is data/raw/reviews_dataset.csv and is not regenerated
by the later notebooks.
"""

from __future__ import annotations

import csv
import hashlib
import os
import time
from collections import Counter

import requests
from google_play_scraper import Sort
from google_play_scraper import reviews as gp_reviews

from .aspects import tag_aspects
from .config import APP_LIST, RAW_FILE
from .preprocessing import detect_language, normalise

OUT_PATH = str(RAW_FILE)
CHECKPOINT_PATH = str(RAW_FILE.parent / "scrape_checkpoint.txt")
CAP_PER_APP = 20000

GP_LANGS = ("ar", "en")          # Arabic first so it is never starved
GP_COUNTRIES = ("ae",)
AS_COUNTRIES = ("ae",)           # UAE storefront only

FIELDS = ["review_id", "app_name", "platform", "review_text", "language",
          "star_rating", "review_date", "clean_text", "satisfaction_label",
          "aspect_tags"]


def label_from_stars(stars):
    """Three-way label as written to the raw file; the neutral band is
    dropped later in preprocessing."""
    if not stars:
        return ""
    if stars >= 4:
        return "Satisfied"
    if stars == 3:
        return "Neutral"
    return "Dissatisfied"


def make_row(app_name, platform, text, stars, date, uid):
    text = (text or "").strip()
    clean = normalise(text)
    return {
        "review_id": hashlib.md5(
            f"{platform}:{app_name}:{uid}".encode()).hexdigest()[:16],
        "app_name": app_name,
        "platform": platform,
        "review_text": text,
        "language": detect_language(text),
        "star_rating": stars if stars else "",
        "review_date": date,
        "clean_text": clean,
        "satisfaction_label": label_from_stars(stars),
        "aspect_tags": "|".join(tag_aspects(clean, text)),
    }

# ---------------------------------------------------------------- scrapers


def scrape_google_play(app_name, pkg, budget):
    """Each language gets its own budget so the Arabic pass is never skipped."""
    rows, seen_text = [], set()
    per_lang = max(budget // len(GP_LANGS), 1)

    for lang in GP_LANGS:
        got = 0
        for country in GP_COUNTRIES:
            token = None
            while got < per_lang:
                try:
                    batch, token = gp_reviews(
                        pkg, lang=lang, country=country, sort=Sort.NEWEST,
                        count=200, continuation_token=token)
                except Exception as e:
                    print(f"  [GP] {app_name} {lang}/{country} error: {e}")
                    break
                if not batch:
                    break

                for r in batch:
                    if got >= per_lang:
                        break
                    try:
                        row = make_row(
                            app_name, "Google Play", r.get("content"),
                            r.get("score"),
                            r["at"].date().isoformat() if r.get("at") else "",
                            r.get("reviewId"))
                    except Exception:
                        continue
                    if not row["review_text"] or row["clean_text"] in seen_text:
                        continue
                    seen_text.add(row["clean_text"])
                    rows.append(row)
                    got += 1

                print(f"  [GP] {app_name} {lang}/{country} -> {got}/{per_lang}")
                if token is None:
                    break
                time.sleep(0.3)
    return rows


def scrape_app_store(app_name, app_id, budget):
    """Dedups on text across storefronts because Apple reissues IDs per country."""
    rows, seen_text = [], set()

    for c in AS_COUNTRIES:
        for page in range(1, 11):
            url = (f"https://itunes.apple.com/{c}/rss/customerreviews/"
                   f"page={page}/id={app_id}/sortby=mostrecent/json")
            try:
                feed = requests.get(url, timeout=20).json().get("feed", {})
                entries = feed.get("entry", [])
            except Exception as e:
                print(f"  [AS] {app_name} {c} p{page} error: {e}")
                break

            if isinstance(entries, dict):      # Apple returns a bare dict for 1 entry
                entries = [entries]
            if not isinstance(entries, list) or not entries:
                break

            if page == 1 and isinstance(entries[0], dict) and "im:name" in entries[0]:
                entries = entries[1:]          # first entry is app metadata

            for e in entries:
                if len(rows) >= budget:
                    break
                if not isinstance(e, dict):
                    continue
                try:
                    text = f"{e['title']['label']}. {e['content']['label']}"
                    row = make_row(app_name, "App Store", text,
                                   int(e["im:rating"]["label"]),
                                   e["updated"]["label"][:10], e["id"]["label"])
                except (KeyError, TypeError, ValueError):
                    continue
                if not row["review_text"] or row["clean_text"] in seen_text:
                    continue
                seen_text.add(row["clean_text"])
                rows.append(row)

            print(f"  [AS] {app_name} {c} p{page} -> {len(rows)}/{budget}")
            if len(rows) >= budget:
                return rows
            time.sleep(0.4)
    return rows

# ---------------------------------------------------------------- checkpoint


def load_checkpoint():
    if not os.path.exists(CHECKPOINT_PATH):
        return set()
    with open(CHECKPOINT_PATH, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def mark_done(app_name):
    with open(CHECKPOINT_PATH, "a", encoding="utf-8") as f:
        f.write(app_name + "\n")


def load_existing_keys(path):
    """Rebuild dedup sets from a partial CSV so a resumed run stays consistent."""
    ids, texts = set(), set()
    if not os.path.exists(path):
        return ids, texts
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            ids.add(r["review_id"])
            texts.add(r["clean_text"])
    return ids, texts

# ---------------------------------------------------------------- summary


def summarise(path=OUT_PATH):
    with open(path, encoding="utf-8-sig") as f:
        data = list(csv.DictReader(f))

    print("\n--- per app ---")
    for app, n in Counter(r["app_name"] for r in data).most_common():
        print(f"  {app:<26} {n}")

    print("\n--- distributions ---")
    print("platform:", dict(Counter(r["platform"] for r in data)))
    print("language:", dict(Counter(r["language"] for r in data)))
    print("label:   ", dict(Counter(r["satisfaction_label"] for r in data)))

    aspect_counts = Counter()
    for r in data:
        for a in filter(None, r["aspect_tags"].split("|")):
            aspect_counts[a] += 1
    print("aspects: ", dict(aspect_counts.most_common()))

    untagged = sum(1 for r in data if not r["aspect_tags"])
    print(f"untagged: {untagged} ({untagged / max(len(data), 1):.0%})")

    texts = [r["clean_text"] for r in data]
    print(f"unique texts: {len(set(texts))} / {len(texts)}")
    return data

# ---------------------------------------------------------------- main


def main(apps=APP_LIST):
    done = load_checkpoint()
    seen_ids, seen_texts = load_existing_keys(OUT_PATH)
    resuming = bool(done)
    total = len(seen_ids)

    if resuming:
        print(f"Resuming: {len(done)} apps done, {total} rows on disk.")

    mode = "a" if resuming else "w"
    with open(OUT_PATH, mode, newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not resuming:
            writer.writeheader()

        for name, pkg, asid in apps:
            if name in done:
                print(f"--- skipping {name} (already done)")
                continue

            print(f"\n=== {name} ===")
            app_rows = []

            if pkg:
                try:
                    app_rows += scrape_google_play(name, pkg, CAP_PER_APP)
                except Exception as e:
                    print(f"  !! GP failed for {name}: {e}")

            remaining = CAP_PER_APP - len(app_rows)
            if asid and remaining > 0:
                try:
                    app_rows += scrape_app_store(name, asid, remaining)
                except Exception as e:
                    print(f"  !! AS failed for {name}: {e}")

            fresh = 0
            for r in app_rows:
                if (r["review_id"] in seen_ids
                        or r["clean_text"] in seen_texts
                        or not r["review_text"]):
                    continue
                seen_ids.add(r["review_id"])
                seen_texts.add(r["clean_text"])
                writer.writerow(r)
                fresh += 1

            f.flush()
            mark_done(name)
            total += fresh
            print(f"  == {name}: {fresh} written (running total {total})")

    print(f"\nSaved {total} reviews -> {OUT_PATH}")
    summarise()
