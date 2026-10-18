"""Validate development annotations without treating an attestation as proof of human provenance."""

from collections import Counter

from .core import ASPECTS
from .experiments import frozen_development

POLARITIES = {"positive", "negative", "mixed", "neutral"}


def audit_annotations(rows, records, manifest):
    training, _ = frozen_development(records, manifest)
    known = {r["version_id"]: r["text"] for r in training}
    if not isinstance(rows, list) or not rows:
        raise ValueError("Provide a nonempty list of reviewed training annotations")
    seen, aspects, polarities = set(), Counter(), Counter()
    for row in rows:
        key = row.get("version_id")
        if key not in known or key in seen:
            raise ValueError("Unknown, held-out, or duplicate annotation record")
        seen.add(key)
        if (
            row.get("human_reviewed") is not True
            or not isinstance(row.get("reviewer_id"), str)
            or not row["reviewer_id"].strip()
        ):
            raise ValueError("Explicit human-review attestation and reviewer pseudonym required")
        if row.get("text") != known[key]:
            raise ValueError("Annotation text differs from the immutable source version")
        if not isinstance(row.get("annotations"), list):
            raise ValueError("Annotations must be a list; an explicitly reviewed empty list is valid")
        spans, present = set(), set()
        for span in row["annotations"]:
            if span.get("aspect") not in ASPECTS or span.get("polarity") not in POLARITIES:
                raise ValueError("Unknown aspect or polarity")
            start, end = span.get("start"), span.get("end")
            if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(known[key]):
                raise ValueError("Invalid Unicode evidence offsets")
            if span.get("passage") != known[key][start:end]:
                raise ValueError("Evidence is not the exact immutable source substring")
            identity = (span["aspect"], span["polarity"], start, end)
            if identity in spans:
                raise ValueError("Duplicate evidence span")
            spans.add(identity)
            present.add(span["aspect"])
            polarities[span["polarity"]] += 1
        aspects.update(present)
    return {
        "status": "training-only annotation audit; not an aspect quality evaluation",
        "split_hash": manifest["split_hash"],
        "reviewed_records": len(rows),
        "records_with_no_aspects": sum(not r["annotations"] for r in rows),
        "aspect_review_support": dict(aspects),
        "polarity_span_support": dict(polarities),
        "reviewer_count": len({r["reviewer_id"].strip() for r in rows}),
        "human_review": "User attestations validated structurally; actual provenance and assistance require verification.",
        "final_tests_opened": False,
    }
