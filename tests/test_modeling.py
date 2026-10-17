import json

import joblib

from patchpulse import modeling
from patchpulse.core import ROOT


def test_vocabulary_is_fitted_on_training_only(tmp_path, monkeypatch):
    records = json.loads((ROOT / "data/fixtures/synthetic.json").read_text())["records"]
    partitions, _ = modeling.split_records(records)
    validation_ids = {r["version_id"] for r in partitions["validation"]}
    sentinel = "validationonlysentinel"
    rows = [
        {**r, "text": r["text"] + (" " + sentinel if r["version_id"] in validation_ids else "")}
        for r in records
    ]
    monkeypatch.setattr(modeling, "PRIVATE", tmp_path)
    report = modeling.train(rows, "synthetic")
    pipeline = joblib.load(tmp_path / "synthetic/baseline.joblib")
    assert sentinel not in pipeline["tfidf"].vocabulary_
    assert report["counts"]["validation"] == 7
