"""Supervised polarity on reviewed evidence passages, separate from recommendation labels."""

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime

import joblib
from sklearn.model_selection import GroupShuffleSplit

from .annotations import audit_annotations
from .core import PRIVATE, ROOT
from .experiments import frozen_development, make_pipeline


def passage_rows(annotations, authors=None):
    authors = authors or {}
    return [
        {
            "text": span["passage"],
            "label": span["polarity"],
            "aspect": span["aspect"],
            "version_id": row["version_id"],
            "group": authors.get(row["version_id"]) or row["version_id"],
        }
        for row in annotations
        for span in row["annotations"]
    ]


def freeze_passage_split(rows, config):
    """Group all passages from the same review/author; quarantine exact cross-group duplicates."""
    owners, duplicated, labels = {}, set(), {}
    for row in rows:
        key = " ".join(row["text"].casefold().split())
        if key in labels and labels[key] != row["label"]:
            raise ValueError(
                "Conflicting polarity labels on identical passages require aspect-conditioned modeling or span review"
            )
        labels[key] = row["label"]
        if key in owners and owners[key] != row["group"]:
            duplicated.add(key)
        owners[key] = row["group"]
    clean = [r for r in rows if " ".join(r["text"].casefold().split()) not in duplicated]
    if len({r["group"] for r in clean}) < 4:
        raise ValueError("At least four independent review/author groups are required")
    train, valid = next(
        GroupShuffleSplit(
            n_splits=1, test_size=config["validation_fraction"], random_state=config["seed"]
        ).split(clean, groups=[r["group"] for r in clean])
    )
    training, validation = [clean[i] for i in train], [clean[i] for i in valid]
    support = {
        label: len({r["group"] for r in training if r["label"] == label}) for label in config["classes"]
    }
    if min(support.values()) < config["minimum_review_groups_per_training_class"]:
        raise ValueError(
            f"Insufficient independent training support by polarity: {support}. Collect labels; do not search seeds for a favorable split."
        )
    return (
        training,
        validation,
        {
            "quarantined_duplicate_passages": len(rows) - len(clean),
            "policy": "Fixed grouped split; exact normalized cross-group duplicate passages quarantined; semantic duplicates not guaranteed removed",
        },
    )


def fit_passage_model(training):
    model = make_pipeline({"features": "hybrid", "C": 1.0, "class_weight": "balanced"})
    model.fit([r["text"] for r in training], [r["label"] for r in training])
    return model


def run(mode="synthetic"):
    config = json.loads((ROOT / "configs/aspects.json").read_text(encoding="utf-8-sig"))
    folder = PRIVATE / mode
    if mode == "real":
        if not config["taxonomy_frozen"]:
            raise ValueError(
                "Real supervised training requires the human pilot and an explicitly frozen annotation guide"
            )
        labels_path = folder / "human-annotations.json"
        if not labels_path.exists():
            raise ValueError(
                "Import actual human-reviewed training annotations before fitting aspect polarity"
            )
        annotations = json.loads(labels_path.read_text(encoding="utf-8"))
        case = json.loads((folder / "case.json").read_text(encoding="utf-8"))
        manifest = json.loads((folder / "split.json").read_text())
        audit_annotations(annotations, case["evidence"], manifest)
        training_records, _ = frozen_development(case["evidence"], manifest)
        authors = {r["version_id"]: r.get("author_group") for r in training_records}
        parent_split_hash = manifest["split_hash"]
    else:
        labels_path = ROOT / "data/fixtures/aspect-polarity.json"
        data = json.loads(labels_path.read_text(encoding="utf-8"))
        if data["label_source"] != "original synthetic fixtures; not human ground truth":
            raise ValueError("Synthetic fixture provenance is invalid")
        annotations, authors, parent_split_hash = data["records"], {}, None
    annotation_hash = hashlib.sha256(labels_path.read_bytes()).hexdigest()
    rows = passage_rows(annotations, authors)
    training, validation, policy = freeze_passage_split(rows, config)
    from sklearn.metrics import classification_report, confusion_matrix

    model = fit_passage_model(training)
    pred = model.predict([r["text"] for r in validation])
    metric = classification_report(
        [r["label"] for r in validation], pred, labels=config["classes"], output_dict=True, zero_division=0
    )
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = folder / "aspect-models" / run_id
    output.mkdir(parents=True)
    model_path = output / "polarity.joblib"
    joblib.dump(model, model_path)
    split = {
        "train": sorted({r["version_id"] for r in training}),
        "validation": sorted({r["version_id"] for r in validation}),
        "annotation_sha256": annotation_hash,
        "parent_recommendation_split_hash": parent_split_hash,
        **policy,
    }
    split_hash = hashlib.sha256(json.dumps(split, sort_keys=True).encode()).hexdigest()
    report = {
        "mode": mode,
        "task": "polarity classification given an evidence passage",
        "status": "synthetic workflow check only"
        if mode == "synthetic"
        else "development pilot only; not final aspect evaluation",
        "real_world_quality_established": False,
        "label_source": "synthetic authored"
        if mode == "synthetic"
        else "human review attestations; provenance requires verification",
        "run_id": run_id,
        "config": config,
        "split_hash": split_hash,
        "train_passages": len(training),
        "validation_passages": len(validation),
        "training_class_support": dict(Counter(r["label"] for r in training)),
        "validation_class_support": dict(Counter(r["label"] for r in validation)),
        "macro_f1": metric["macro avg"]["f1-score"],
        "classification_report": metric,
        "confusion_matrix": confusion_matrix(
            [r["label"] for r in validation], pred, labels=config["classes"]
        ).tolist(),
        "class_order": config["classes"],
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "limitations": [
            "Gold-passage polarity does not establish end-to-end aspect detection or evidence relevance.",
            "No uncertainty calibration; short annotated spans may differ from detector clauses.",
            "Pilot taxonomy may change; final temporal and unseen-game sets remain unopened.",
        ],
        "final_tests_opened": False,
    }
    (output / "split.json").write_text(json.dumps(split, indent=2), encoding="utf-8")
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    pointer = folder / "aspect-model.tmp"
    pointer.write_text(
        json.dumps(
            {
                "artifact": str(model_path.relative_to(folder)).replace("\\", "/"),
                "sha256": report["model_sha256"],
                "report": str((output / "report.json").relative_to(folder)).replace("\\", "/"),
                "mode": mode,
                "split_hash": split_hash,
                "guide_version": config["guide_version"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    pointer.replace(folder / "aspect-model.json")
    print(
        json.dumps(
            {
                "status": report["status"],
                "training_passages": len(training),
                "validation_passages": len(validation),
                "final_tests_opened": False,
            }
        )
    )
    return report
