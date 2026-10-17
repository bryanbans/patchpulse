import json

import joblib
import numpy as np
import pytest

from patchpulse import experiments
from patchpulse.core import ROOT, digest


def manifest(parts):
    value = {"partitions": parts, "locked_test_opened": False}
    value["split_hash"] = digest(json.dumps(value, sort_keys=True))
    return value


def test_frozen_partitions_reject_tampering_and_do_not_read_final_labels():
    value = manifest({"train": ["train"], "validation": ["validation"], "locked_temporal_test": ["locked"]})
    records = [
        {"version_id": "train", "text": "training"},
        {"version_id": "validation", "text": "validation"},
        {"version_id": "locked"},
    ]
    train, valid = experiments.frozen_development(records, value)
    assert train[0]["text"] == "training" and valid[0]["text"] == "validation"
    value["partitions"]["train"] = ["locked"]
    with pytest.raises(ValueError, match="hash mismatch"):
        experiments.frozen_development(records, value)


def test_overlapping_frozen_ids_are_rejected_even_with_updated_hash():
    value = manifest({"train": ["same"], "validation": ["same"], "locked_temporal_test": ["locked"]})
    with pytest.raises(ValueError, match="overlapping"):
        experiments.frozen_development([{"version_id": "same"}, {"version_id": "locked"}], value)


def test_tuned_threshold_changes_decisions_without_changing_scores():
    scores = np.array([0.3, 0.1, 0.8, 0.02])
    np.testing.assert_array_equal(experiments.recommendation_labels(scores, 0.2), [False, True, False, True])
    threshold, _ = experiments.choose_threshold([False, True, False, True], scores, [0.1, 0.2, 0.5])
    assert threshold == 0.2
    assert experiments.metrics([False, True, False, True], scores, threshold)["negative_recall"] == 1


@pytest.mark.parametrize("family", ["word", "char", "hybrid"])
def test_feature_families_round_trip_and_fit_training_only(family, tmp_path):
    rows = json.loads((ROOT / "data/fixtures/synthetic.json").read_text())["records"][:20]
    pipeline = experiments.make_pipeline({"features": family, "C": 1, "class_weight": "balanced"})
    texts = [r["text"] for r in rows]
    pipeline.fit(texts, [r["voted_up"] for r in rows])
    assert "validationonlysentinel" not in pipeline[:-1].get_feature_names_out()
    original = experiments.negative_scores(pipeline, ["The game crashes but the missions are fun"])
    joblib.dump(pipeline, tmp_path / "model.joblib")
    np.testing.assert_allclose(
        original,
        experiments.negative_scores(
            joblib.load(tmp_path / "model.joblib"), ["The game crashes but the missions are fun"]
        ),
    )
