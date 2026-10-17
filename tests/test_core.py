import json
import sqlite3

import pytest

from patchpulse.core import (
    ROOT,
    aspects,
    build_case,
    connect,
    eligibility,
    ingest,
    normalize,
    parse_review,
    stats,
    windows,
)
from patchpulse.modeling import split_records


def raw(**kwargs):
    return {
        "recommendationid": "1",
        "review": "Not bad, but the server disconnects.",
        "language": "english",
        "voted_up": True,
        "timestamp_created": 10,
        "timestamp_updated": 10,
        **kwargs,
    }


def record(**kwargs):
    return parse_review(raw(**kwargs), 548430, 100, b"test")


def test_versions_immutable_and_idempotent(tmp_path):
    db = connect(tmp_path / "reviews.sqlite")
    first, edited = record(), record(review="Changed text", timestamp_updated=20)
    ingest(db, first)
    ingest(db, first)
    ingest(db, edited)
    assert db.execute("SELECT count(*) FROM review_versions").fetchone()[0] == 2
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE review_versions SET payload='mutated'")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("DELETE FROM review_versions")


@pytest.mark.parametrize(
    "created,updated,expected",
    [(10, 10, None), (19, 19, None), (20, 20, "outside_window"), (10, 20, "edited_after_cutoff")],
)
def test_half_open_cutoff(created, updated, expected):
    assert eligibility(record(timestamp_created=created, timestamp_updated=updated), 10, 20) == expected


def test_windows_omit_release_date():
    bounds = windows("2024-06-13")
    assert bounds["after"][0] - bounds["before"][1] == 86400
    assert all(end - start == 14 * 86400 for start, end in bounds.values())


def test_schema_change_and_target_type_rejected():
    with pytest.raises(ValueError):
        record(voted_up="false")
    with pytest.raises(ValueError):
        record(timestamp_updated=5)


def test_author_identifier_minimization():
    r = record(author={"steamid": "synthetic-author-id", "num_reviews": 100})
    assert "synthetic-author-id" not in json.dumps(r)
    assert len(r["author_group"]) == 64


def test_recommendation_math_and_aspect_offsets():
    values = [record(), record(recommendationid="2", voted_up=False)]
    assert stats(values)["rate"] == 0.5
    assert stats([])["rate"] is None
    matches = aspects(values[0]["text"])
    assert matches[0]["aspect"] == "Multiplayer"
    for m in matches:
        assert m["passage"] == values[0]["text"][m["start"] : m["end"]]
        assert m["polarity"] == "unreviewed"
    assert "Not" in normalize(values[0]["text"])


def test_latest_version_cannot_evade_cutoff():
    config = {"date": "2024-06-13"}
    start, end = windows(config["date"])["before"]
    first = record(timestamp_created=start, timestamp_updated=start)
    last = record(timestamp_created=start, timestamp_updated=end + 1)
    last["observed_at"] = 101
    case = build_case([first, last], config, {"before": {}, "after": {}}, "synthetic")
    assert case["periods"]["before"]["count"] == 0
    assert case["exclusions"]["edited_after_cutoff"] == 1


def test_duplicate_versions_and_cross_split_leakage():
    rows = json.loads((ROOT / "data/fixtures/synthetic.json").read_text())["records"]
    duplicate = {
        **rows[0],
        "review_id": "copy",
        "version_id": "copy",
        "created_at": rows[-1]["created_at"] + 1,
    }
    parts, manifest = split_records(rows + [duplicate])
    assert "copy" in manifest["excluded_duplicates"]
    sets = [set(r["version_id"] for r in v) for v in parts.values()]
    assert not (sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])
    assert not manifest["locked_test_opened"]
    assert max(r["created_at"] for r in parts["train"]) < min(r["created_at"] for r in parts["validation"])
