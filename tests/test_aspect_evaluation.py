import json

import pytest

from patchpulse.aspect_evaluation import evaluate, fingerprint
from patchpulse.aspects import analyze_feedback
from patchpulse.core import ROOT


def test_development_challenges_keep_known_limits_visible():
    suite = json.loads((ROOT / "data/fixtures/aspect-challenge.json").read_text(encoding="utf-8"))
    result = evaluate(suite["records"])
    assert not suite["human_reviewed"]
    assert result["reviews"] == 48
    assert {r["id"] for r in result["failures"]} == {"challenge-047", "challenge-048"}
    assert result["recommendation_invariance"] == {"passed": 48, "total": 48}
    assert result["exact_evidence_substrings"] == {"passed": 55, "total": 55}
    published = json.loads((ROOT / "reports/aspect-challenge.json").read_text(encoding="utf-8"))
    assert published["rules"] == result
    assert published["suite_sha256"] == fingerprint(ROOT / "data/fixtures/aspect-challenge.json")
    assert published["detector_sha256"] == fingerprint(ROOT / "src/patchpulse/aspects.py")


def test_source_fingerprints_survive_git_line_ending_normalization(tmp_path):
    a, b = tmp_path / "a.py", tmp_path / "b.py"
    a.write_bytes(b"first\r\nsecond\r\n")
    b.write_bytes(b"first\nsecond\n")
    assert fingerprint(a) == fingerprint(b)


def test_abstentions_and_wrong_aspects_do_not_count_as_detected_complaints():
    records = [
        {"id": "a", "phenomenon": "scope", "text": "a", "expected": {"Gameplay": "mixed"}},
        {"id": "b", "phenomenon": "scope", "text": "b", "expected": {"Multiplayer": "negative"}},
    ]

    def analyzer(text):
        # An abstention misses both directions of mixed feedback. A wrong topic is a
        # false complaint plus a missed real topic, even when polarity is negative.
        aspect, polarity = ("Gameplay", "uncertain") if text.endswith("a") else ("Value", "negative")
        return {"aspects": [{"aspect": aspect, "polarity": polarity, "evidence": []}]}

    result = evaluate(records, analyzer)
    assert result["end_to_end_complaint"] == {"tp": 0, "fp": 1, "fn": 2, "precision": 0, "recall": 0, "f1": 0}
    assert result["end_to_end_praise"]["fn"] == 1
    assert result["aspect_detection"]["tp"] == 1
    assert result["aspect_detection"]["fp"] == 1
    assert result["aspect_detection"]["fn"] == 1


class AlwaysPositive:
    """A deliberately overconfident model must not bypass assertion/attribution guards."""

    classes_ = ["positive", "negative"]

    def __getitem__(self, key):
        return self

    def transform(self, texts):
        raise AssertionError("Guarded passages must not reach the classifier")


@pytest.mark.parametrize(
    "text",
    [
        "Are the servers good?",
        "Are the servers good?!",
        "I hope the servers are good tomorrow.",
        "If the patch arrives, the servers might be reliable.",
        "Great combat with terrible servers.",
    ],
)
def test_learned_classifier_cannot_override_nonassertion_or_ambiguous_scope(text):
    result = analyze_feedback(text, AlwaysPositive())
    assert result["aspects"]
    assert all(a["polarity"] == "uncertain" for a in result["aspects"])
    assert all("score" not in e for a in result["aspects"] for e in a["evidence"])


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Crashes weren't fixed.", "negative"),
        ("The patch hasn't fixed crashes.", "negative"),
        ("Crashes were fixed without a restart.", "positive"),
        ("The update fixed crashes but new crashes still occur.", "mixed"),
        ("Crashes were eliminated.", "positive"),
    ],
)
def test_resolution_scope_with_contractions_and_later_failures(text, expected):
    result = analyze_feedback(text)
    assert {a["aspect"]: a["polarity"] for a in result["aspects"]}["Stability"] == expected


def test_evaluation_api_returns_traceable_synthetic_checks_and_rejects_stale_report(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from patchpulse import api

    client = TestClient(api.app)
    result = client.get("/api/feedback-evaluation")
    assert result.status_code == 200
    assert result.json()["real_world_quality_established"] is False
    assert result.json()["rules"]["reviews"] == 48
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports/aspect-challenge.json").write_text('{"detector_sha256":"stale"}')
    (tmp_path / "src/patchpulse").mkdir(parents=True)
    (tmp_path / "src/patchpulse/aspects.py").write_text("changed")
    monkeypatch.setattr(api, "ROOT", tmp_path)
    assert client.get("/api/feedback-evaluation").status_code == 503
