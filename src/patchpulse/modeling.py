"""Text-only baseline; validation results only. Release tests stay unopened."""

import json
import platform
import time
from collections import Counter

import joblib
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline

from .core import PRIVATE, digest, normalize


def shingles(text):
    tokens = normalize(text).casefold().split()
    return set(zip(tokens, tokens[1:], tokens[2:])) or {tuple(tokens)}


def split_records(records):
    """Latest review version; exact/near duplicates retained at earliest creation only.

    Greedy Jaccard >= .85 on token trigrams, frozen before fitting. Same creation
    timestamps remain together at chronological boundaries. No label-based selection.
    """
    latest = {}
    for r in sorted(records, key=lambda r: (r["observed_at"], r["updated_at"])):
        latest[r["review_id"]] = r
    kept, seen, excluded = [], [], []
    for r in sorted(latest.values(), key=lambda r: (r["created_at"], r["review_id"])):
        words = shingles(r["text"])
        if any(len(words & other) / len(words | other) >= 0.85 for other in seen):
            excluded.append(r["version_id"])
            continue
        kept.append(r)
        seen.append(words)
    if len(kept) < 12:
        raise ValueError("At least 12 distinct eligible records required for demonstration training")
    first = kept[int(len(kept) * 0.70)]["created_at"]
    second = kept[int(len(kept) * 0.85)]["created_at"]
    partitions = {"train": [], "validation": [], "locked_temporal_test": []}
    for r in kept:
        name = (
            "train"
            if r["created_at"] < first
            else "validation"
            if r["created_at"] < second
            else "locked_temporal_test"
        )
        partitions[name].append(r)
    if any(not v for v in partitions.values()):
        raise ValueError("Timestamp groups leave an empty partition; enlarge sample")
    # Private author audit, never a feature. Report rather than silently claiming author independence.
    train_authors = {r.get("author_group") for r in partitions["train"]} - {None}
    manifest = {
        "policy": "latest version; greedy trigram Jaccard >= .85; chronological 70/15/15; timestamp groups intact",
        "partitions": {k: [r["version_id"] for r in v] for k, v in partitions.items()},
        "boundaries_utc_unix": [first, second],
        "excluded_duplicates": excluded,
        "author_overlap_train_validation": len(
            train_authors & ({r.get("author_group") for r in partitions["validation"]} - {None})
        ),
        "locked_test_opened": False,
    }
    manifest["split_hash"] = digest(json.dumps(manifest, sort_keys=True))
    return partitions, manifest


def train(records, mode):
    partitions, manifest = split_records(records)
    train_rows, validation = partitions["train"], partitions["validation"]
    x = [normalize(r["text"]) for r in train_rows]
    y = [r["voted_up"] for r in train_rows]
    vx = [normalize(r["text"]) for r in validation]
    vy = [r["voted_up"] for r in validation]
    if len(set(y)) < 2:
        raise ValueError("Training sample contains only one recommendation class")
    started = time.perf_counter()
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=30000, sublinear_tf=True)),
            ("classifier", LogisticRegression(max_iter=500, random_state=42)),
        ]
    )
    model.fit(x, y)
    elapsed = time.perf_counter() - started
    predictions = model.predict(vx)
    majority = DummyClassifier(strategy="most_frequent").fit(x, y).predict(vx)
    report = {
        "mode": mode,
        "status": "development validation only; final tests locked",
        "task": "recommendation prediction",
        "model_id": "tfidf-logreg-v1",
        "features": "review text only; word unigram/bigram TF-IDF fitted on training",
        "selection": "fixed initial configuration, one seed (42); no hyperparameter search yet",
        "split_hash": manifest["split_hash"],
        "counts": {k: len(v) for k, v in partitions.items()},
        "validation_class_support": dict(Counter(str(v) for v in vy)),
        "macro_f1": f1_score(vy, predictions, average="macro", labels=[False, True], zero_division=0),
        "majority_macro_f1": f1_score(vy, majority, average="macro", labels=[False, True], zero_division=0),
        "classification_report": classification_report(
            vy,
            predictions,
            labels=[False, True],
            target_names=["not_recommended", "recommended"],
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(vy, predictions, labels=[False, True]).tolist(),
        "confusion_matrix_order": ["not_recommended", "recommended"],
        "train_seconds": elapsed,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "calibrated": False,
        "real_world_quality_claim": False if mode == "synthetic" else "exploratory validation only",
    }
    folder = PRIVATE / mode
    folder.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, folder / "baseline.joblib")
    (folder / "split.json").write_text(json.dumps(manifest, indent=2))
    (folder / "evaluation.json").write_text(json.dumps(report, indent=2))
    return report
