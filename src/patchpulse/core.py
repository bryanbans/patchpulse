"""Versioned ingestion, conservative retrospective cohorts, and transparent rules."""

import hashlib
import hmac
import json
import re
import sqlite3
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / "private"
API_URL = "https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/"
ASPECTS = {
    "Performance": r"\b(fps|stutter\w*|performance|frame\w*|lag\w*)\b",
    "Stability": r"\b(crash\w*|freez\w*|frozen|stability)\b",
    "Multiplayer": r"\b(multiplayer|disconnect\w*|server\w*|lobby|lobbies|co-op|connection)\b",
    "Gameplay": r"\b(balance|combat|weapon\w*|difficulty|mission\w*)\b",
    "Interface": r"\b(control\w*|interface|menu|menus|keybind\w*|ui)\b",
    "Accessibility": r"\b(accessibility|colorblind|subtitles|screen reader|remap\w*)\b",
    "Value": r"\b(price|expensive|monetization|dlc|value)\b",
    "Progression": r"\b(content|progression|unlock\w*|grind\w*|biome\w*)\b",
    "Other issue": r"(?!)",  # Human annotation only; never fabricated by keyword matching.
}


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def windows(date):
    day = datetime.fromisoformat(date).replace(tzinfo=UTC)
    return {
        "before": (int((day - timedelta(days=14)).timestamp()), int(day.timestamp())),
        "after": (int((day + timedelta(days=1)).timestamp()), int((day + timedelta(days=15)).timestamp())),
    }


def normalize(text):
    # No stop-word removal: retain not, punctuation, contrast and gaming vocabulary.
    return re.sub(r"\s+", " ", re.sub(r"\[/?[a-zA-Z]+(?:=[^\]]*)?\]", "", text)).strip()


def parse_review(raw, app_id, observed_at, secret):
    required = {
        "recommendationid",
        "review",
        "language",
        "voted_up",
        "timestamp_created",
        "timestamp_updated",
    }
    if not required.issubset(raw) or type(raw["voted_up"]) is not bool:
        raise ValueError("Review schema changed or required field missing")
    if not isinstance(raw["review"], str) or not isinstance(raw["language"], str):
        raise ValueError("Invalid review text or language")
    created, updated = raw["timestamp_created"], raw["timestamp_updated"]
    if type(created) is not int or type(updated) is not int or created < 0 or updated < created:
        raise ValueError("Invalid creation/update timestamp")
    text_hash = digest(raw["review"])
    identity = str(raw["recommendationid"])
    version_id = digest(json.dumps([identity, text_hash, updated, raw["voted_up"]]))
    author = raw.get("author", {}).get("steamid")
    return {
        "review_id": identity,
        "version_id": version_id,
        "app_id": app_id,
        "text": raw["review"],
        "text_hash": text_hash,
        "language": raw["language"],
        "voted_up": raw["voted_up"],
        "created_at": created,
        "updated_at": updated,
        "observed_at": observed_at,
        "author_group": hmac.new(secret, str(author).encode(), "sha256").hexdigest() if author else None,
        "source_url": f"https://steamcommunity.com/app/{app_id}/reviews/",
    }


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute(
        "CREATE TABLE IF NOT EXISTS review_versions (version_id TEXT PRIMARY KEY, review_id TEXT, payload TEXT)"
    )
    db.execute(
        "CREATE TRIGGER IF NOT EXISTS immutable_update BEFORE UPDATE ON review_versions BEGIN SELECT RAISE(ABORT,'immutable version'); END"
    )
    db.execute(
        "CREATE TRIGGER IF NOT EXISTS immutable_delete BEFORE DELETE ON review_versions BEGIN SELECT RAISE(ABORT,'immutable version'); END"
    )
    return db


def ingest(db, record):
    db.execute(
        "INSERT OR IGNORE INTO review_versions VALUES (?,?,?)",
        (record["version_id"], record["review_id"], json.dumps(record)),
    )
    db.commit()


def eligibility(record, start, end):
    if record["language"] != "english":
        return "language"
    if not start <= record["created_at"] < end:
        return "outside_window"
    if record["updated_at"] >= end:
        return "edited_after_cutoff"
    if not record["text"].strip():
        return "empty_text"
    return None


def aspects(text):
    """Keyword mentions only. No polarity is inferred from recommendation labels."""
    found = []
    for name, pattern in ASPECTS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Exact offsets in raw version; sentence selection retains all original characters.
            start = max(text.rfind(".", 0, match.start()) + 1, 0)
            end = text.find(".", match.end())
            end = len(text) if end < 0 else end + 1
            found.append(
                {
                    "aspect": name,
                    "polarity": "unreviewed",
                    "start": start,
                    "end": end,
                    "passage": text[start:end],
                    "method": "keyword-mentions-v1",
                }
            )
    return found


def stats(records):
    n = len(records)
    positive = sum(r["voted_up"] for r in records)
    rate = positive / n if n else None
    interval = None
    if n:
        z = 1.96
        center = (rate + z * z / (2 * n)) / (1 + z * z / n)
        margin = z * ((rate * (1 - rate) / n + z * z / (4 * n * n)) ** 0.5) / (1 + z * z / n)
        interval = [center - margin, center + margin]
    return {
        "count": n,
        "positive": positive,
        "negative": n - positive,
        "rate": rate,
        "wilson_95": interval,
        "interval_note": "Sampling variability only; excludes selection and model error.",
    }


def build_case(records, config, coverage, mode):
    bounds = windows(config["date"])
    periods = {}
    evidence = []
    exclusions = Counter()
    # Only the latest observed version per review enters this retrospective snapshot.
    latest = {}
    for record in sorted(records, key=lambda r: (r["observed_at"], r["updated_at"], r["version_id"])):
        latest[record["review_id"]] = record
    for period, (start, end) in bounds.items():
        cohort = []
        for r in latest.values():
            if not start <= r["created_at"] < end:
                continue
            reason = eligibility(r, start, end)
            if reason:
                exclusions[reason] += 1
                continue
            cohort.append(r)
            evidence.append(
                {
                    **r,
                    "period": period,
                    "mentions": aspects(r["text"]),
                    "quality_flags": ["short"] if len(r["text"].split()) < 4 else [],
                }
            )
        periods[period] = {**stats(cohort), "start": start, "end": end, "coverage": coverage[period]}
    before, after = periods["before"]["rate"], periods["after"]["rate"]
    mentions = []
    for aspect in ASPECTS:
        counts = {
            p: sum(any(m["aspect"] == aspect for m in e["mentions"]) for e in evidence if e["period"] == p)
            for p in bounds
        }
        mentions.append({"aspect": aspect, **counts, "method": "keyword mentions; polarity not evaluated"})
    return {
        "id": "drg-season-05",
        "mode": mode,
        "game": config,
        "snapshot_date": datetime.fromtimestamp(max((r["observed_at"] for r in records), default=0), UTC)
        .date()
        .isoformat()
        if records
        else datetime.now(UTC).date().isoformat(),
        "periods": periods,
        "change_pp": (after - before) * 100 if before is not None and after is not None else None,
        "exclusions": dict(exclusions),
        "mentions": mentions,
        "evidence": evidence,
        "limitations": [
            "Retrospective snapshot: original historical text is unavailable.",
            "Association within collected reviews does not establish patch causation.",
            "Keyword mentions are exploratory; aspect polarity awaits human annotation.",
        ],
    }
