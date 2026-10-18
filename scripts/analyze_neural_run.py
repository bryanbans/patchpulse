"""Describe fixed-threshold failure without searching thresholds or opening final tests."""

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score

from patchpulse.experiments import frozen_development

root = Path(__file__).resolve().parents[1]
folder = root / "private/real"
pointer = json.loads((folder / "neural-model.json").read_text())
report_path = folder / pointer["report"]
report = json.loads(report_path.read_text())
manifest = json.loads((folder / "split.json").read_text())
_, validation = frozen_development(json.loads((folder / "case.json").read_text())["evidence"], manifest)
assert report["split_hash"] == manifest["split_hash"]
labels = np.asarray([r["voted_up"] for r in validation], dtype=bool)
saved = json.loads((report_path.parent / "validation-scores.json").read_text())
rows = []
for key, values in saved.items():
    scores = np.asarray(values)
    assert len(scores) == len(labels) and np.isfinite(scores).all()
    row = {
        "checkpoint": key,
        "negative_average_precision": float(average_precision_score(~labels, scores)),
        "predicted_negative_at_fixed_threshold": int(sum(scores >= 0.5)),
        "score_summary_by_recorded_class": {},
    }
    for label, name in [(False, "not_recommended"), (True, "recommended")]:
        scores_for_class = scores[labels == label]
        row["score_summary_by_recorded_class"][name] = {
            "count": len(scores_for_class),
            "minimum": float(min(scores_for_class)),
            "median": float(np.median(scores_for_class)),
            "maximum": float(max(scores_for_class)),
        }
    rows.append(row)
result = {
    "experiment_id": report["experiment_id"],
    "run_id": report["run_id"],
    "split_hash": manifest["split_hash"],
    "status": "post-run development diagnostics, no additional selection",
    "checkpoints": rows,
    "threshold_search_performed": False,
    "final_tests_opened": False,
    "interpretation": "Ranking scores vary despite identical fixed-threshold predictions. This motivates a future training-only threshold study; no threshold is selected using these validation scores.",
}
(root / "reports/transformer-diagnostics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(
    json.dumps(
        {
            "all_checkpoints_predict_only_recommended": all(
                r["predicted_negative_at_fixed_threshold"] == 0 for r in rows
            ),
            "negative_average_precision_range": [
                min(r["negative_average_precision"] for r in rows),
                max(r["negative_average_precision"] for r in rows),
            ],
        }
    )
)
