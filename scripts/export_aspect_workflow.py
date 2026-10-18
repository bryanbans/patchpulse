"""Publish synthetic-only workflow evidence; never copy real text or human-review claims."""

import hashlib
import json
from pathlib import Path

from patchpulse.aspects import analyze_feedback

root = Path(__file__).resolve().parents[1]
folder = root / "private/synthetic"
active = json.loads((folder / "aspect-model.json").read_text())
report = json.loads((folder / active["report"]).read_text())
assert report["mode"] == "synthetic" and report["real_world_quality_established"] is False
example = "I recommend the game. Great missions, but our co-op sessions keep disconnecting."
result = {
    "status": "synthetic workflow evidence only; not real-player accuracy",
    "label_source": "original authored synthetic reviews; no independent human review claimed",
    "review_records": 48,
    "human_reviewed_records": 0,
    "example": {
        "text": example,
        "synthetic_overall_recommendation": True,
        "analysis": analyze_feedback(example),
    },
    "supervised_passage_workflow": report,
    "source_sha256": {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in [
            "data/fixtures/aspect-polarity.json",
            "configs/aspects.json",
            "src/patchpulse/aspects.py",
            "src/patchpulse/aspect_model.py",
        ]
    },
    "real_world_quality_established": False,
    "final_tests_opened": False,
}
(root / "reports/aspect-synthetic-workflow.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({"status": result["status"], "review_records": 48, "human_reviewed_records": 0}))
