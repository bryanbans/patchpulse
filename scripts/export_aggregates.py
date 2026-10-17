"""Export review-free research aggregates. Never export source rows or author groups."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

root = Path(__file__).resolve().parents[1]
case = json.loads((root / "private/real/case.json").read_text(encoding="utf-8"))
evaluation = json.loads((root / "private/real/evaluation.json").read_text())
split = json.loads((root / "private/real/split.json").read_text())
source = json.loads((root / "private/current.json").read_text(encoding="utf-8"))
coverage_keys = {
    "status",
    "count",
    "pages",
    "source_total_matching",
    "observed_creation_range",
    "terminal_empty_page_verified",
}
result = {
    "scope": "Local exploratory research. Aggregates only; source text and models excluded. Not final evaluation.",
    "snapshot_date": case["snapshot_date"],
    "dataset_version": source["manifest"]["dataset_version"],
    "game": case["game"],
    "periods": {
        name: {k: v for k, v in period.items() if k != "coverage"}
        | {"coverage": {k: v for k, v in period["coverage"].items() if k in coverage_keys}}
        for name, period in case["periods"].items()
    },
    "exclusions": case["exclusions"],
    "change_pp": case["change_pp"],
    "evaluation": evaluation,
    "duplicates_excluded": len(split["excluded_duplicates"]),
    "author_overlap_train_validation": split["author_overlap_train_validation"],
    "split_boundaries_utc": [
        datetime.fromtimestamp(t, UTC).isoformat() for t in split["boundaries_utc_unix"]
    ],
    "locked_test_opened": split["locked_test_opened"],
    "model_artifact_sha256": hashlib.sha256((root / "private/real/baseline.joblib").read_bytes()).hexdigest(),
    "python_lock_sha256": hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest(),
    "code_state": "Initial implementation before first commit; see Git history for source.",
    "limitations": case["limitations"]
    + [
        "After-window source count exceeds returned distinct records by one.",
        "Public distribution and model-training permission questions remain unresolved. This is not an open dataset.",
        "One seed and baseline only; no final-test, transformer, or human aspect-quality claims.",
    ],
}
out = root / "reports/milestone1-real-aggregates.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(result, indent=2), encoding="utf-8")
print("Exported aggregate-only research report.")
