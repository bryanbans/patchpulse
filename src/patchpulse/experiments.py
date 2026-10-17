"""Bounded, split-preserving comparison. Final-test rows are never evaluated here."""

import hashlib
import json
import platform
import subprocess
import time
from collections import Counter
from datetime import UTC, datetime

import joblib
import numpy as np
import sklearn
from sklearn.base import clone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline
from threadpoolctl import threadpool_limits

from .core import PRIVATE, ROOT, digest, normalize


def frozen_development(records, manifest):
    """Verify membership using IDs, then expose training and validation only."""
    if manifest.get("locked_test_opened") is not False:
        raise ValueError("This workflow requires unopened final tests")
    claimed_hash = manifest.get("split_hash")
    actual_hash = digest(json.dumps({k: v for k, v in manifest.items() if k != "split_hash"}, sort_keys=True))
    if claimed_hash != actual_hash:
        raise ValueError("Frozen split hash mismatch")
    partitions = manifest["partitions"]
    names = ["train", "validation", "locked_temporal_test"]
    if set(partitions) != set(names):
        raise ValueError("Unexpected frozen split schema")
    seen = set()
    for name in names:
        ids = partitions[name]
        if not ids or len(set(ids)) != len(ids) or seen.intersection(ids):
            raise ValueError("Empty or overlapping frozen partitions")
        seen.update(ids)
    lookup = {r["version_id"]: r for r in records}
    if len(lookup) != len(records) or not seen.issubset(lookup):
        raise ValueError("Frozen versions are missing or duplicated")
    # No recomputation, rebalancing, or access to final-test text/labels.
    return [lookup[k] for k in partitions["train"]], [lookup[k] for k in partitions["validation"]]


def make_pipeline(config, seed=42):
    word = TfidfVectorizer(ngram_range=(1, 2), max_features=30000, sublinear_tf=True)
    char = TfidfVectorizer(
        analyzer="char_wb", ngram_range=(3, 5), max_features=60000, min_df=2, sublinear_tf=True
    )
    features = word if config["features"] == "word" else char
    if config["features"] == "hybrid":
        features = FeatureUnion([("word", word), ("char", char)])
    elif config["features"] not in {"word", "char"}:
        raise ValueError("Unsupported feature family")
    return Pipeline(
        [
            ("features", features),
            (
                "classifier",
                LogisticRegression(
                    C=config["C"], class_weight=config["class_weight"], max_iter=500, random_state=seed
                ),
            ),
        ]
    )


def negative_scores(model, texts):
    return model.predict_proba(texts)[:, list(model.classes_).index(False)]


def recommendation_labels(scores, negative_threshold):
    return np.asarray(scores) < negative_threshold


def choose_threshold(labels, scores, thresholds):
    candidates = []
    for threshold in thresholds:
        pred = recommendation_labels(scores, threshold)
        candidates.append(
            (
                f1_score(labels, pred, labels=[False, True], average="macro", zero_division=0),
                f1_score(labels, pred, pos_label=False, zero_division=0),
                -abs(threshold - 0.5),
                threshold,
            )
        )
    best = max(candidates)
    return float(best[-1]), {"macro_f1": float(best[0]), "negative_f1": float(best[1])}


def metrics(labels, scores, threshold):
    pred = recommendation_labels(scores, threshold)
    report = classification_report(
        labels,
        pred,
        labels=[False, True],
        target_names=["not_recommended", "recommended"],
        output_dict=True,
        zero_division=0,
    )
    return {
        "macro_f1": report["macro avg"]["f1-score"],
        "accuracy": report["accuracy"],
        "negative_precision": report["not_recommended"]["precision"],
        "negative_recall": report["not_recommended"]["recall"],
        "negative_f1": report["not_recommended"]["f1-score"],
        "negative_average_precision": average_precision_score(~np.asarray(labels, dtype=bool), scores),
        "confusion_matrix": confusion_matrix(labels, pred, labels=[False, True]).tolist(),
        "classification_report": report,
    }


def paired_bootstrap(labels, selected, original, repetitions, seed):
    """Label-stratified paired resampling of validation review versions."""
    rng = np.random.default_rng(seed)
    labels = np.asarray(labels, dtype=bool)
    groups = [np.flatnonzero(labels == label) for label in [False, True]]
    values, deltas = [], []
    for _ in range(repetitions):
        ids = np.concatenate([rng.choice(group, len(group), replace=True) for group in groups])
        score = f1_score(labels[ids], selected[ids], labels=[False, True], average="macro", zero_division=0)
        previous = f1_score(
            labels[ids], original[ids], labels=[False, True], average="macro", zero_division=0
        )
        values.append(score)
        deltas.append(score - previous)
    return {
        "method": "Label-stratified paired bootstrap of validation review versions; percentile interval",
        "repetitions": repetitions,
        "seed": seed,
        "macro_f1_interval_95": np.quantile(values, [0.025, 0.975]).tolist(),
        "macro_f1_difference_from_v1_interval_95": np.quantile(deltas, [0.025, 0.975]).tolist(),
        "limitations": "Exploratory: same validation set selected the model. Does not account for selection optimism, source bias, or other-game generalization.",
    }


def compare(mode="real"):
    folder = PRIVATE / mode
    case = json.loads((folder / "case.json").read_text(encoding="utf-8"))
    manifest_path = folder / "split.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    baseline_report = json.loads((folder / "evaluation.json").read_text())
    if baseline_report["split_hash"] != manifest["split_hash"]:
        raise ValueError("Frozen split differs from the original baseline")
    train_rows, validation = frozen_development(case["evidence"], manifest)
    config_bytes = (ROOT / "configs/negative_detection.json").read_bytes()
    config = json.loads(config_bytes)
    x = [normalize(r["text"]) for r in train_rows]
    y = np.asarray([r["voted_up"] for r in train_rows], dtype=bool)
    vx = [normalize(r["text"]) for r in validation]
    vy = np.asarray([r["voted_up"] for r in validation], dtype=bool)
    if min(Counter(y).values()) < config["inner_folds"] or len(set(y)) != 2 or len(set(vy)) != 2:
        raise ValueError("Both classes and sufficient training support are required")
    groups = [r.get("author_group") or r["review_id"] for r in train_rows]
    cv = StratifiedGroupKFold(config["inner_folds"], shuffle=True, random_state=config["seed"])
    folds = list(cv.split(x, y, groups))
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    run = folder / "experiments" / run_id
    run.mkdir(parents=True)
    results, models, scores = [], {}, {}
    with threadpool_limits(limits=4):
        for candidate in config["candidates"]:
            started = time.perf_counter()
            estimator = make_pipeline(candidate, config["seed"])
            threshold, training_selection = 0.5, None
            if candidate["tune_threshold"]:
                oof = np.full(len(x), np.nan)
                for fit_ids, score_ids in folds:
                    if set(np.asarray(groups)[fit_ids]) & set(np.asarray(groups)[score_ids]):
                        raise ValueError("Author leakage in training CV")
                    inner = clone(estimator).fit([x[i] for i in fit_ids], y[fit_ids])
                    oof[score_ids] = negative_scores(inner, [x[i] for i in score_ids])
                if np.isnan(oof).any():
                    raise ValueError("Incomplete out-of-fold predictions")
                threshold, training_selection = choose_threshold(y, oof, config["negative_threshold_grid"])
            estimator.fit(x, y)
            current_scores = negative_scores(estimator, vx)
            feature_count = estimator[:-1].transform([x[0]]).shape[1]
            elapsed = time.perf_counter() - started
            result = {
                "id": candidate["id"],
                "configuration": candidate,
                "negative_threshold": threshold,
                "threshold_training_oof": training_selection,
                "feature_count": feature_count,
                "fit_and_cv_seconds": elapsed,
                **metrics(vy, current_scores, threshold),
            }
            results.append(result)
            models[result["id"]] = estimator
            scores[result["id"]] = current_scores
            print(
                json.dumps(
                    {
                        k: result[k]
                        for k in [
                            "id",
                            "negative_threshold",
                            "macro_f1",
                            "negative_precision",
                            "negative_recall",
                            "fit_and_cv_seconds",
                        ]
                    }
                ),
                flush=True,
            )
    selected = max(
        results, key=lambda r: (r["macro_f1"], r["negative_f1"], r["negative_precision"], -r["feature_count"])
    )
    model_path = run / "selected.joblib"
    joblib.dump(models[selected["id"]], model_path)
    artifact_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()
    available_models = {}
    for result in results:
        path = run / f"{result['id']}.joblib"
        joblib.dump(models[result["id"]], path)
        available_models[result["id"]] = {
            "artifact": str(path.relative_to(folder)).replace("\\", "/"),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "negative_threshold": result["negative_threshold"],
            "configuration": result["configuration"],
        }
    selected_pred = recommendation_labels(scores[selected["id"]], selected["negative_threshold"])
    original_pred = recommendation_labels(scores["word-default-v1"], 0.5)
    report = {
        "experiment_id": config["experiment_id"],
        "run_id": run_id,
        "mode": mode,
        "status": "development validation only; final tests remain locked",
        "task": "recommendation prediction",
        "created_at": datetime.now(UTC).isoformat(),
        "split_hash": manifest["split_hash"],
        "frozen_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "experiment_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "python_lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
        "code_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
        ).stdout.strip(),
        "code_state": "working tree experiment implementation; see next source commit",
        "counts": {
            "train": len(train_rows),
            "validation": len(validation),
            "locked_temporal_test": len(manifest["partitions"]["locked_temporal_test"]),
        },
        "training_class_support": dict(Counter("recommended" if v else "not_recommended" for v in y)),
        "validation_class_support": dict(Counter("recommended" if v else "not_recommended" for v in vy)),
        "threshold_method": config["threshold_source"],
        "inner_cv": config["inner_split"],
        "inner_folds": config["inner_folds"],
        "seed": config["seed"],
        "seed_note": "Fixed deterministic lbfgs configuration; seed is recorded, not evidence of multi-seed robustness.",
        "selection_rule": config["selection"],
        "candidate_count": len(results),
        "candidates": results,
        "selected_id": selected["id"],
        "selected": selected,
        "model_artifact_sha256": artifact_hash,
        "calibrated": False,
        "uncertainty": paired_bootstrap(
            vy, selected_pred, original_pred, config["bootstrap_repetitions"], config["seed"]
        ),
        "environment": {
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
            "platform": platform.platform(),
            "threads": 4,
            "hardware": "AMD Ryzen 7 7800X3D; CPU training; approximately 63.1 GiB RAM",
        },
        "final_tests_opened": False,
        "limitations": [
            "Only 12 negative validation examples in the primary real-data study; minority estimates are fragile.",
            "Inner folds shuffle within the training period; outer validation remains chronological.",
            "The validation split selects among six predeclared candidates; scores are not final test performance.",
            "No claims about aspect polarity, unseen games, or causal patch effects.",
        ],
    }
    (run / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Private review-level errors aid human analysis; never publish raw text or source IDs.
    errors = [
        {
            "version_id": r["version_id"],
            "text": r["text"],
            "recorded_recommendation": bool(label),
            "predicted_recommendation": bool(pred),
            "negative_score": float(score),
            "human_reviewed": False,
            "error_category": None,
            "notes": "",
        }
        for r, label, pred, score in zip(validation, vy, selected_pred, scores[selected["id"]], strict=True)
        if label != pred
    ]
    (run / "errors-for-human-review.json").write_text(json.dumps(errors, indent=2), encoding="utf-8")
    if manifest_path.read_bytes() != manifest_bytes:
        raise ValueError("Frozen split was unexpectedly modified")
    # Atomic pointer update; original baseline and prior experiments remain intact.
    active = {
        "model_id": selected["id"],
        "artifact": str(model_path.relative_to(folder)).replace("\\", "/"),
        "report": str((run / "report.json").relative_to(folder)).replace("\\", "/"),
        "negative_threshold": selected["negative_threshold"],
        "sha256": artifact_hash,
        "split_hash": manifest["split_hash"],
        "run_id": run_id,
        "models": available_models,
    }
    temporary = folder / "active-model.tmp"
    temporary.write_text(json.dumps(active, indent=2))
    temporary.replace(folder / "active-model.json")
    public = ROOT / "reports" / f"negative-detection-{mode}.json"
    public.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "selected_id": selected["id"],
                "report": str(public),
                "errors_for_human_review": len(errors),
                "final_tests_opened": False,
            }
        ),
        flush=True,
    )
    return report
