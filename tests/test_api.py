from fastapi.testclient import TestClient

from patchpulse.api import app, case

client = TestClient(app)


def test_api_coverage_filter_denominators_and_bounds():
    response = client.get("/api/case-studies/drg-season-05")
    assert response.status_code == 200
    assert "evidence" not in response.json()
    filtered = client.get("/api/evidence?period=before&recommendation=positive").json()
    assert filtered["denominator"] == 24
    assert filtered["total"] == 12
    assert "author_group" not in str(filtered)
    for url in [
        "/api/evidence?limit=1000",
        "/api/evidence?period=tomorrow",
        "/api/evidence?unknown=1",
        "/api/evidence?polarity=negative",
    ]:
        assert client.get(url).status_code == 422
    assert client.get("/api/case-studies/missing").status_code == 404


def test_predict_does_not_accept_label_features_or_unknown_models():
    assert client.post("/api/predict", json={"text": "great", "voted_up": True}).status_code == 422
    assert client.post("/api/predict", json={"text": "great", "model_id": "other"}).status_code == 422
    assert client.post("/api/predict", json={"text": "x" * 8001}).status_code == 422
    assert client.post("/api/predict", content=b"x" * 40001).status_code == 413


def test_predictions_and_abstention():
    result = client.post("/api/predict", json={"text": "The game crashes and I cannot recommend it"}).json()
    assert result["task"] == "recommendation prediction"
    assert not result["calibrated"] and not result["input_stored"]
    assert 0 <= result["score_recommended"] <= 1
    assert client.post("/api/predict", json={"text": "zzqxyzzqxy"}).json()["abstention_reason"]


def test_brief_numbers_and_exact_evidence():
    brief = client.get("/api/briefs/drg-season-05").json()
    assert "SYNTHETIC" in brief["text"]
    assert "12/24" in brief["text"]
    assert set(brief["evidence_ids"]) == {r["version_id"] for r in case()["evidence"]}
    assert "does not establish patch causation" in brief["text"]


def test_model_registry_and_selected_alias():
    values = client.get("/api/models").json()
    assert any(v["id"] == "selected" for v in values)
    result = client.post("/api/predict", json={"text": "A wonderful game", "model_id": "selected"}).json()
    selected = next(v for v in values if v["id"] == "selected")
    assert result["model_id"] == selected["resolved_id"]
    assert result["negative_threshold"] == selected["negative_threshold"]


def test_api_applies_selected_negative_threshold(monkeypatch):
    import numpy as np

    from patchpulse import api

    class Features:
        def transform(self, text):
            class Matrix:
                nnz = 1

            return Matrix()

    class Controlled:
        classes_ = np.array([False, True])

        def __getitem__(self, item):
            return Features()

        def predict_proba(self, text):
            return np.array([[0.3, 0.7]])

    monkeypatch.setattr(api, "model_info", lambda name: {"id": "controlled", "negative_threshold": 0.2})
    monkeypatch.setattr(api, "model", lambda name: Controlled())
    monkeypatch.setattr(api, "model_revision", lambda name: "0" * 64)
    result = client.post("/api/predict", json={"text": "Mixed feedback"}).json()
    assert result["score_recommended"] == 0.7
    assert result["prediction"] == "not recommended"


def test_annotation_sample_is_training_only_and_blinded():
    import json

    from patchpulse.api import FOLDER

    sample = client.get("/api/annotation-pilot").json()
    split = json.loads((FOLDER / "split.json").read_text())
    assert len(sample["records"]) == min(60, len(split["partitions"]["train"]))
    assert {r["version_id"] for r in sample["records"]} <= set(split["partitions"]["train"])
    assert all(set(r) == {"version_id", "text", "annotations", "human_reviewed"} for r in sample["records"])
    assert all(r["human_reviewed"] is False and not r["annotations"] for r in sample["records"])


def test_public_neural_report_contains_only_aggregate_evaluation():
    from patchpulse.api import ROOT

    if not (ROOT / "reports/transformer-real.json").exists():
        return
    response = client.get("/api/neural-evaluation")
    assert response.status_code == 200
    report = response.json()
    assert report["task"] == "recommendation prediction, not aspect sentiment"
    assert report["final_tests_opened"] is False
    assert len(report["results"]) == 12
    assert all("text" not in row and "version_id" not in row for row in report["results"])


def test_feedback_api_separates_praise_and_complaint_without_recommendation_input():
    result = client.post(
        "/api/analyze-feedback", json={"text": "Great missions, but multiplayer is broken."}
    ).json()
    assert {a["aspect"]: a["polarity"] for a in result["aspects"]} == {
        "Gameplay": "positive",
        "Multiplayer": "negative",
    }
    assert result["method"] == "aspect-rules-v1"
    assert result["input_stored"] is False
    assert "provisional" in result["validation_status"]
    assert (
        client.post("/api/analyze-feedback", json={"text": "Great missions", "voted_up": True}).status_code
        == 422
    )
    assert client.post("/api/analyze-feedback", json={"text": "x" * 8001}).status_code == 422
    assert client.post("/api/analyze-feedback", json={"text": " "}).status_code == 422
    assert (
        client.post("/api/analyze-feedback", json={"text": "missions", "method": "magic"}).status_code == 422
    )


def test_feedback_status_and_supervised_artifact_integrity(monkeypatch):
    from patchpulse import api

    status = client.get("/api/feedback-status").json()
    assert not status["real_world_quality_established"]
    monkeypatch.setattr(
        api, "aspect_manifest", lambda: {"mode": api.MODE, "artifact": "baseline.joblib", "sha256": "bad"}
    )
    api.aspect_polarity_model.cache_clear()
    result = client.post("/api/analyze-feedback", json={"text": "Great missions", "method": "supervised"})
    assert result.status_code == 503
    api.aspect_polarity_model.cache_clear()


def test_supervised_feedback_is_separate_from_overall_recommendation():
    from patchpulse import api

    if not api.aspect_manifest():
        return
    response = client.post(
        "/api/analyze-feedback", json={"text": "Our lobby disconnects every night.", "method": "supervised"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["method"] == "supervised-passage-v1"
    assert "synthetic" in result["label_source"]
    assert "recommendation" not in result
    assert len(result["model_revision"]) == 64
