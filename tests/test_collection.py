import httpx
import pytest

from patchpulse import collection
from patchpulse.collection import fetch


def test_429_retry_after_and_empty_page():
    statuses = [429, 200]

    def handler(request):
        status = statuses.pop(0)
        return httpx.Response(
            status, headers={"Retry-After": "2"}, json={"response": {"reviews": [], "cursor": "done"}}
        )

    waits = []
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert fetch(client, {}, sleep=waits.append)["reviews"] == []
    assert waits == [2]


def test_schema_change_fails_loudly():
    with httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"response": {"unexpected": []}}))
    ) as client:
        with pytest.raises(ValueError, match="schema"):
            fetch(client, {})


def test_protobuf_omitted_empty_array_requires_explicit_zero_metadata():
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, json={"response": {"query_summary": {"num_reviews": 0}, "cursor": "last"}}
            )
        )
    ) as client:
        assert fetch(client, {})["reviews"] == []


def test_retry_budget_bounded():
    waits = []
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503))) as client:
        with pytest.raises(httpx.HTTPStatusError):
            fetch(client, {}, sleep=waits.append)
    assert len(waits) == 4


def test_repeated_cursor_is_error_not_completion(tmp_path, monkeypatch):
    import json

    from patchpulse.core import windows

    monkeypatch.setattr(collection, "PRIVATE", tmp_path)
    config = {"app_id": 548430, "date": "2024-06-13"}
    t = windows(config["date"])["before"][0]
    row = {
        "recommendationid": "synthetic-cursor",
        "review": "Synthetic cursor test",
        "language": "english",
        "voted_up": True,
        "timestamp_created": t,
        "timestamp_updated": t,
    }
    monkeypatch.setattr(
        collection, "fetch", lambda *_: {"reviews": [row], "cursor": "*", "total_matching": 2}
    )
    with pytest.raises(ValueError, match="Pagination"):
        collection.collect(config, cap=10, pace=0)
    manifest = json.loads(next((tmp_path / "collections").glob("*/manifest.json")).read_text())
    assert manifest["status"] == "error"
    assert manifest["periods"]["before"]["status"] == "repeated_cursor_error"
    assert not (tmp_path / "current.json").exists()


def test_resume_reuses_verified_cache_and_marks_source_mismatch(tmp_path, monkeypatch):
    import json

    from patchpulse.core import windows

    monkeypatch.setattr(collection, "PRIVATE", tmp_path)
    config = {"app_id": 548430, "date": "2024-06-13"}
    t = windows(config["date"])["before"][0]
    row = {
        "recommendationid": "synthetic-resume",
        "review": "Synthetic resume example",
        "language": "english",
        "voted_up": True,
        "timestamp_created": t,
        "timestamp_updated": t,
    }
    calls = 0

    def interrupted(*_):
        nonlocal calls
        calls += 1
        if calls > 1:
            raise RuntimeError("interrupted")
        return {"reviews": [row], "cursor": "next", "total_matching": 2}

    monkeypatch.setattr(collection, "fetch", interrupted)
    with pytest.raises(RuntimeError):
        collection.collect(config, cap=10, pace=0)
    run = next((tmp_path / "collections").iterdir()).name
    monkeypatch.setattr(
        collection,
        "fetch",
        lambda _, q: {
            "reviews": [],
            "cursor": q["cursor"],
            "total_matching": 2 if q["cursor"] == "next" else 0,
        },
    )
    result = collection.collect(config, cap=10, pace=0, resume_run=run)
    assert result["status"] == "partial"
    assert result["periods"]["before"]["status"] == "exhausted_source_count_mismatch"
    assert len(json.loads((tmp_path / "current.json").read_text())["records"]) == 1
