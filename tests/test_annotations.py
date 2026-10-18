import copy
import json

import pytest

from patchpulse.annotations import audit_annotations
from patchpulse.core import digest


def examples():
    manifest = {
        "partitions": {"train": ["train"], "validation": ["validation"], "locked_temporal_test": ["locked"]},
        "locked_test_opened": False,
    }
    manifest["split_hash"] = digest(json.dumps(manifest, sort_keys=True))
    records = [
        {"version_id": "train", "text": "🚀 Crashes."},
        {"version_id": "validation"},
        {"version_id": "locked"},
    ]
    rows = [
        {
            "version_id": "train",
            "text": "🚀 Crashes.",
            "human_reviewed": True,
            "reviewer_id": "reviewer-01",
            "annotations": [
                {"aspect": "Stability", "polarity": "negative", "start": 2, "end": 9, "passage": "Crashes"}
            ],
        }
    ]
    return rows, records, manifest


def test_annotation_audit_uses_unicode_and_never_reads_test_labels():
    rows, records, manifest = examples()
    result = audit_annotations(rows, records, manifest)
    assert result["aspect_review_support"] == {"Stability": 1}
    assert result["final_tests_opened"] is False
    rows[0]["annotations"] = []
    assert audit_annotations(rows, records, manifest)["records_with_no_aspects"] == 1


@pytest.mark.parametrize(
    "change", ["heldout", "duplicate", "text", "offset", "attestation", "span", "reviewer"]
)
def test_annotation_audit_rejects_unusable_ground_truth(change):
    rows, records, manifest = examples()
    if change == "heldout":
        rows[0]["version_id"] = "locked"
    if change == "duplicate":
        rows.append(copy.deepcopy(rows[0]))
    if change == "text":
        rows[0]["text"] += "changed"
    if change == "offset":
        rows[0]["annotations"][0]["start"] = 3
    if change == "attestation":
        rows[0]["human_reviewed"] = False
    if change == "span":
        rows[0]["annotations"].append(copy.deepcopy(rows[0]["annotations"][0]))
    if change == "reviewer":
        rows[0]["reviewer_id"] = " "
    with pytest.raises(ValueError):
        audit_annotations(rows, records, manifest)
