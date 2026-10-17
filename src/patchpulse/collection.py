"""Conservative single-worker collector; private cache and explicit completion state."""

import json
import random
import subprocess
import time
from datetime import UTC, datetime

import httpx

from .core import API_URL, PRIVATE, connect, digest, ingest, parse_review, windows


def fetch(client, query, sleep=time.sleep):
    for attempt in range(5):
        try:
            response = client.get(API_URL, params={"input_json": json.dumps(query)})
        except httpx.TransportError:
            if attempt == 4:
                raise
            sleep(2**attempt + random.random())
            continue
        if response.status_code == 429 or 500 <= response.status_code < 600:
            if attempt == 4:
                response.raise_for_status()
            retry = response.headers.get("Retry-After", "")
            sleep(float(retry) if retry.replace(".", "", 1).isdigit() else 2**attempt + random.random())
            continue
        response.raise_for_status()
        payload = response.json().get("response")
        if (
            isinstance(payload, dict)
            and "reviews" not in payload
            and payload.get("query_summary", {}).get("num_reviews") == 0
        ):
            # Protobuf JSON omits repeated fields when empty. Require explicit zero-page metadata.
            payload["reviews"] = []
        if not isinstance(payload, dict) or not isinstance(payload.get("reviews"), list):
            raise ValueError("API response schema changed")
        return payload
    raise RuntimeError("Retry budget exhausted")


def collect(config, cap=500, pace=1.1, resume_run=None):
    if not 1 <= cap <= 7500:
        raise ValueError("Cap must be between 1 and 7500 per period")
    PRIVATE.mkdir(exist_ok=True)
    keypath = PRIVATE / "author-hmac.key"
    if not keypath.exists():
        import secrets

        keypath.write_bytes(secrets.token_bytes(32))
    secret = keypath.read_bytes()
    db = connect(PRIVATE / "reviews.sqlite")
    all_records, coverage = [], {}
    if resume_run and (not resume_run.isalnum() or len(resume_run) > 30):
        raise ValueError("Invalid resume run ID")
    run = resume_run or datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = PRIVATE / "collections" / run
    run_dir.mkdir(parents=True, exist_ok=bool(resume_run))
    manifest = {
        "schema_version": 1,
        "dataset_version": run,
        "source_url": API_URL,
        "started_at": datetime.now(UTC).isoformat(),
        "app_id": config["app_id"],
        "code_commit": subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"], capture_output=True, text=True, check=False
        ).stdout.strip()
        or "uncommitted",
        "selection": "Recent order, independent equal record caps per window; no label balancing",
        "periods": coverage,
        "status": "running",
    }
    manifest_path = run_dir / "manifest.json"
    if resume_run:
        manifest = json.loads(manifest_path.read_text())
        if manifest["app_id"] != config["app_id"]:
            raise ValueError("Resume game does not match")
        coverage = manifest["periods"]
        manifest["status"] = "running"
        manifest["resumed_at"] = datetime.now(UTC).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2))
    try:
        with httpx.Client(timeout=45, headers={"User-Agent": "PatchPulse/0.1 personal research"}) as client:
            for period, (start, end) in windows(config["date"]).items():
                cursor, seen, records = "*", set(), {}
                state = {
                    "status": "running",
                    "pages": 0,
                    "count": 0,
                    "cap": cap,
                    "cursor_checkpoint": cursor,
                    "start": start,
                    "end_exclusive": end,
                }
                if period in coverage:
                    state = coverage[period]
                    if (state["start"], state["end_exclusive"]) != (start, end):
                        raise ValueError("Resume windows do not match")
                    for key, checksum in state.get("page_checksums", {}).items():
                        cached = (run_dir / f"{key}.json").read_text(encoding="utf-8")
                        if digest(cached) != checksum:
                            raise ValueError("Private cache checksum mismatch")
                        for r in json.loads(cached)["records"]:
                            records[r["review_id"]] = r
                    if state["status"] == "complete":
                        all_records.extend(records.values())
                        continue
                    cursor = state["cursor_checkpoint"]
                    seen.update(state.get("seen_cursors", []))
                    state["cap"] = cap
                    if len(records) >= cap:
                        raise ValueError("Resume cap must exceed existing record count")
                coverage[period] = state
                state["status"] = "running"
                while True:
                    query = {
                        "appid": config["app_id"],
                        "filter": 1,
                        "languages": ["english"],
                        "review_type": 0,
                        "purchase_type": 1,
                        "filter_offtopic_activity": True,
                        "num_per_page": min(100, cap - len(records)),
                        "cursor": cursor,
                        "date_range_start": start,
                        "date_range_end": end - 1,
                    }
                    state["query_config"] = query
                    cache_key = digest(json.dumps(query, sort_keys=True))
                    page = fetch(client, query)
                    observed = int(time.time())
                    parsed = [
                        parse_review(raw, config["app_id"], observed, secret) for raw in page["reviews"]
                    ]
                    # Cache minimized versions, never raw author profiles or SteamIDs.
                    cache_text = json.dumps({"records": parsed, "cursor": page.get("cursor")})
                    (run_dir / f"{cache_key}.json").write_text(cache_text, encoding="utf-8")
                    state.setdefault("page_checksums", {})[cache_key] = digest(cache_text)
                    state["pages"] += 1
                    for r in parsed:
                        ingest(db, r)
                        records[r["review_id"]] = r
                    state["count"] = len(records)
                    state["source_total_matching"] = page.get("total_matching")
                    next_cursor = page.get("cursor")
                    state["cursor_checkpoint"] = next_cursor
                    manifest_path.write_text(json.dumps(manifest, indent=2))
                    if not parsed:
                        expected = state.get("source_total_matching")
                        state["status"] = (
                            "complete"
                            if expected in {None, len(records)}
                            else "exhausted_source_count_mismatch"
                        )
                        state["terminal_empty_page_verified"] = True
                        break
                    if len(records) >= cap:
                        state["status"] = "capped_incomplete"
                        break
                    if not next_cursor or next_cursor == cursor or next_cursor in seen:
                        state["status"] = "repeated_cursor_error"
                        raise ValueError("Pagination did not advance; collection remains incomplete")
                    seen.add(cursor)
                    state.setdefault("seen_cursors", []).append(cursor)
                    cursor = next_cursor
                    time.sleep(pace)
                all_records.extend(records.values())
                if records:
                    state["observed_creation_range"] = [
                        min(r["created_at"] for r in records.values()),
                        max(r["created_at"] for r in records.values()),
                    ]
                manifest_path.write_text(json.dumps(manifest, indent=2))
        manifest["status"] = (
            "complete" if all(s["status"] == "complete" for s in coverage.values()) else "partial"
        )
    except Exception:
        manifest["status"] = "error"
        raise
    finally:
        manifest["completed_at"] = datetime.now(UTC).isoformat()
        manifest_path.write_text(json.dumps(manifest, indent=2))
        db.close()
    (PRIVATE / "current.json").write_text(
        json.dumps({"records": all_records, "coverage": coverage, "manifest": manifest}), encoding="utf-8"
    )
    return manifest
