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
