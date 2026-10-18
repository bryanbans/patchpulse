"""Transparent clause-scoped aspect sentiment. Provisional, never human ground truth."""

import re
from collections import defaultdict

from .core import ASPECTS

VERSION = "aspect-rules-v1"
ASPECT_PATTERNS = {
    **ASPECTS,
    "Stability": ASPECTS["Stability"] + r"|\b(unstable|stable|startup)\b",
    "Gameplay": ASPECTS["Gameplay"] + r"|\b(gameplay)\b",
    "Multiplayer": ASPECTS["Multiplayer"] + r"|\b(coop|cooperative|co-operative)\b",
    "Interface": ASPECTS["Interface"] + r"|\b(inventory|hud)\b",
    "Value": ASPECTS["Value"] + r"|\b(cost|bargain|worth|affordable|overpriced)\b",
    "Progression": ASPECTS["Progression"] + r"|\b(exploration)\b",
}

# Evaluative cues are explicit so a reviewer can inspect the rule's decision.
POSITIVE = re.compile(
    r"\b(great|good|excellent|amazing|awesome|fantastic|fun|smooth|stable|responsive|polished|fair|affordable|love\w*|enjoy\w*|favorite|favourite|fixed|resolved|improv\w*|reliable|works?|working|worth)\b",
    re.I,
)
NEGATIVE = re.compile(
    r"\b(bad|awful|terrible|broken|unplayable|unreliable|unresponsive|boring|repetitive|frustrat\w*|exhaust\w*|painful\w*|expensive|overpriced|hate\w*|crash\w*|freez\w*|frozen|disconnect\w*|stutter\w*|laggy|lags?|slow|ruin\w*|fail\w*)\b",
    re.I,
)
TOKENS = re.compile(r"[^\W_]+(?:['’][^\W_]+)?", re.UNICODE)
NEGATORS = {"not", "no", "never", "without", "neither", "hardly"}
BOUNDARY = re.compile(r"[.!?;,\r\n]+\s*|\b(?:but|however|yet|although|whereas|except|while)\b[\s,:]*", re.I)


def aspect_mentions(text):
    return {aspect for aspect, pattern in ASPECT_PATTERNS.items() if re.search(pattern, text, re.I)}


def cues(text, offset=0):
    found = []
    for pattern, original in [(POSITIVE, "positive"), (NEGATIVE, "negative")]:
        for match in pattern.finditer(text):
            if original == "negative" and re.match(r"\s+(?:log|report)\b", text[match.end() :], re.I):
                continue
            previous = [
                m.group().casefold().replace("’", "'") for m in TOKENS.finditer(text[: match.start()])
            ][-3:]
            # "not only fun" is not a negation of "fun".
            if "not" in previous and "only" in previous[previous.index("not") + 1 :]:
                previous = [v for v in previous if v != "not"]
            negated = sum(v in NEGATORS or v.endswith("n't") or v == "cannot" for v in previous) % 2
            following = [m.group().casefold() for m in TOKENS.finditer(text[match.end() :])][:3]
            resolution_words = {"fixed", "resolved", "eliminated", "removed"}
            resolved = (
                any(v in resolution_words for v in previous)
                or any(v in resolution_words for v in following)
                and not any(v in NEGATORS for v in following)
            )
            if original == "negative" and resolved:
                negated = not negated
            polarity = {"positive": "negative", "negative": "positive"}[original] if negated else original
            found.append(
                {
                    "start": offset + match.start(),
                    "end": offset + match.end(),
                    "passage": match.group(),
                    "polarity": polarity,
                    "negated": bool(negated),
                }
            )
    return sorted(found, key=lambda x: x["start"])


def clause_spans(text):
    """Preserve raw Unicode offsets; break contrast before assigning polarity."""
    start = 0
    initial = []
    for boundary in BOUNDARY.finditer(text):
        initial.append((start, boundary.start()))
        start = boundary.end()
    initial.append((start, len(text)))
    for left, right in initial:
        chunk = text[left:right]
        # Split coordinated, separately evaluative aspects, not "servers and missions are fun".
        cut = left
        for join in re.finditer(r"\band\b\s*", chunk, re.I):
            a, b = text[cut : left + join.start()], text[left + join.end() : right]
            if aspect_mentions(a) and aspect_mentions(b) and cues(a) and cues(b):
                yield from trimmed_span(text, cut, left + join.start())
                cut = left + join.end()
        yield from trimmed_span(text, cut, right)


def trimmed_span(text, left, right):
    while left < right and text[left].isspace():
        left += 1
    while right > left and text[right - 1].isspace():
        right -= 1
    if left < right:
        yield left, right


def combine_polarities(values):
    values = set(values)
    if "mixed" in values or {"positive", "negative"} <= values:
        return "mixed"
    if "positive" in values:
        return "positive"
    if "negative" in values:
        return "negative"
    if "neutral" in values and "uncertain" not in values:
        return "neutral"
    return "uncertain"


def analyze_feedback(text, polarity_model=None):
    grouped = defaultdict(list)
    for start, end in clause_spans(text):
        passage = text[start:end]
        aspects = aspect_mentions(passage)
        matches = cues(passage, start)
        polarities = {m["polarity"] for m in matches}
        if end < len(text) and text[end] == "?":
            polarity, reason = "uncertain", "A question is not an assertion of praise or criticism"
        elif len(aspects) > 1 and len(polarities) > 1:
            polarity, reason = (
                "uncertain",
                "Multiple aspects and conflicting cues in one clause; attribution is ambiguous",
            )
        elif polarities == {"positive", "negative"}:
            polarity, reason = "mixed", "Praise and criticism cues for the same aspect"
        elif polarities:
            polarity, reason = (
                next(iter(polarities)),
                "Clause-scoped evaluative cues with a three-token negation window",
            )
        else:
            polarity, reason = "uncertain", "Aspect mentioned without a recognized evaluative cue"
        supervised = None
        if polarity_model is not None and aspects:
            if polarity_model[:-1].transform([passage]).nnz:
                scores = polarity_model.predict_proba([passage])[0]
                index = int(scores.argmax())
                supervised = {
                    "polarity": str(polarity_model.classes_[index]),
                    "reason": "Supervised passage classifier; aspect assignment still uses keyword rules",
                    "score": float(scores[index]),
                    "calibrated": False,
                }
            else:
                supervised = {"polarity": "uncertain", "reason": "No supported supervised vocabulary"}
        for aspect in sorted(aspects):
            evidence = {
                "start": start,
                "end": end,
                "passage": passage,
                "polarity": polarity,
                "reason": reason,
                "cues": matches,
            }
            if supervised is not None:
                evidence.update(supervised)
            grouped[aspect].append(evidence)
    return {
        "task": "aspect detection and passage polarity",
        "method": "supervised-passage-v1" if polarity_model is not None else VERSION,
        "validation_status": "provisional; real-world aspect quality has not been established",
        "input_stored": False,
        "aspects": [
            {
                "aspect": name,
                "polarity": combine_polarities(e["polarity"] for e in evidence),
                "evidence": evidence,
            }
            for name, evidence in sorted(grouped.items())
        ],
        "limitations": [
            "Keyword aspect detection can miss implicit topics and Other issue.",
            "No recognized cue means uncertain, not neutral or absent.",
            "Rules do not resolve sarcasm, implied meaning, or every negation scope.",
            "Passages are exact source spans, not proof that attribution is correct.",
            "Overall recommendations are not inputs and are never assigned to every aspect.",
        ],
    }
