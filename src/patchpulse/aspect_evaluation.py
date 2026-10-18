"""Synthetic development diagnostics. These cases are not human ground truth or a held-out test."""

import hashlib
import json
from collections import Counter, defaultdict

from .aspects import analyze_feedback
from .core import PRIVATE, ROOT


def fingerprint(path):
    """Git normalizes source line endings; match fingerprints across Windows/Linux."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def decision_map(result):
    return {a["aspect"]: a["polarity"] for a in result["aspects"]}


def evaluate(records, analyzer=analyze_feedback):
    """Score detection separately from polarity; abstentions count as missed asserted labels."""
    correct, total, span_valid, span_total = 0, 0, 0, 0
    detected_tp, detected_fp, detected_fn = 0, 0, 0
    labels = {label: {"tp": 0, "fp": 0, "fn": 0} for label in ["positive", "negative"]}
    failures, slices = [], defaultdict(lambda: {"correct": 0, "total": 0})
    invariant = 0
    predicted_support, expected_support = Counter(), Counter()
    for row in records:
        result = analyzer(row["text"])
        predicted, expected = decision_map(result), row["expected"]
        predicted_support.update(predicted.values())
        expected_support.update(expected.values())
        exact = predicted == expected
        total += 1
        correct += exact
        slices[row["phenomenon"]]["total"] += 1
        slices[row["phenomenon"]]["correct"] += exact
        detected_tp += len(predicted.keys() & expected.keys())
        detected_fp += len(predicted.keys() - expected.keys())
        detected_fn += len(expected.keys() - predicted.keys())
        for label, counts in labels.items():
            # Mixed includes both praise and complaint; uncertain/neutral include neither.
            truth = {a for a, p in expected.items() if p in {label, "mixed"}}
            found = {a for a, p in predicted.items() if p in {label, "mixed"}}
            counts["tp"] += len(truth & found)
            counts["fp"] += len(found - truth)
            counts["fn"] += len(truth - found)
        for aspect in result["aspects"]:
            for span in aspect["evidence"]:
                span_total += 1
                span_valid += row["text"][span["start"] : span["end"]] == span["passage"]
        # Overall-recommendation sentences must not determine topic sentiment.
        variants = [
            decision_map(analyzer(prefix + row["text"]))
            for prefix in ["I recommend the game. ", "I do not recommend the game. "]
        ]
        invariant += all(v == predicted for v in variants)
        if not exact:
            failures.append({"id": row["id"], "expected": expected, "predicted": predicted})

    def rates(tp, fp, fn):
        return {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
        }

    return {
        "reviews": total,
        "exact_review_matches": correct,
        "expected_topic_label_support": dict(expected_support),
        "predicted_topic_label_support": dict(predicted_support),
        "abstentions": {
            "uncertain": predicted_support["uncertain"],
            "recognized_topics": sum(predicted_support.values()),
            "note": "Abstention counts are conditional on recognized topics; missed implicit topics are scored separately.",
        },
        "aspect_detection": rates(detected_tp, detected_fp, detected_fn),
        "end_to_end_praise": rates(**labels["positive"]),
        "end_to_end_complaint": rates(**labels["negative"]),
        "recommendation_invariance": {"passed": invariant, "total": total},
        "exact_evidence_substrings": {"passed": span_valid, "total": span_total},
        "phenomenon_slices": dict(slices),
        "failures": failures,
    }


def run():
    path = ROOT / "data/fixtures/aspect-challenge.json"
    suite = json.loads(path.read_text(encoding="utf-8"))
    from .aspects import VERSION

    report = {
        "suite_id": suite["suite_id"],
        "suite_sha256": fingerprint(path),
        "method": VERSION,
        "detector_sha256": fingerprint(ROOT / "src/patchpulse/aspects.py"),
        "fingerprint_policy": "UTF-8 bytes with CRLF normalized to LF",
        "provenance": suite["provenance"],
        "status": suite["purpose"],
        "human_reviewed": False,
        "real_world_quality_established": False,
        "final_tests_opened": False,
        "rules": evaluate(suite["records"]),
        "limitations": [
            "Public authored development cases were used to guide rule changes; scores are optimistic and not generalization estimates.",
            "Exact substring validity checks offsets, not whether the evidence supports the interpretation.",
            "Recommendation invariance covers only the two stated prefix templates, not every paraphrase.",
            "Real human-reviewed aspect, sentiment and evidence relevance evaluation remains required.",
        ],
    }
    baseline_path = ROOT / "reports/aspect-challenge-v1-baseline.json"
    if baseline_path.exists():
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        if baseline["suite_sha256"] != report["suite_sha256"]:
            raise ValueError("Challenge suite changed; do not compare mismatched development suites")
        report["baseline"] = {
            "method": baseline["method"],
            "detector_sha256": baseline["detector_sha256"],
            "rules": baseline["rules"],
        }
    # Optional comparison of a trusted locally trained synthetic artifact. Never
    # substitute it for real-mode evaluation or load an arbitrary uploaded pickle.
    folder = PRIVATE / "synthetic"
    pointer = folder / "aspect-model.json"
    if pointer.exists():
        import joblib

        manifest = json.loads(pointer.read_text(encoding="utf-8"))
        artifact = (folder / manifest["artifact"]).resolve()
        if manifest["mode"] != "synthetic" or not artifact.is_relative_to(folder.resolve()):
            raise ValueError("Only a trusted local synthetic artifact can enter this comparison")
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != manifest["sha256"]:
            raise ValueError("Synthetic artifact integrity check failed")
        model = joblib.load(artifact)
        report["synthetic_supervised"] = {
            "artifact_sha256": manifest["sha256"],
            "status": "Authored development scenarios may overlap training language; not held-out performance",
            "results": evaluate(suite["records"], lambda text: analyze_feedback(text, model)),
        }
    output = ROOT / "reports/aspect-challenge.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
