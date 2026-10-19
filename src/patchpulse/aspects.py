"""Transparent clause-scoped aspect sentiment. Provisional, never human ground truth."""

import re
from collections import defaultdict

from .core import ASPECTS

VERSION = "aspect-rules-v3"
ASPECT_PATTERNS = {
    **ASPECTS,
    "Stability": ASPECTS["Stability"] + r"|\b(unstable|stable|startup)\b",
    "Gameplay": ASPECTS["Gameplay"] + r"|\b(gameplay)\b",
    "Multiplayer": ASPECTS["Multiplayer"]
    + r"|\b(coop|cooperative|co-operative|matchmak\w*|desync\w*|rubberband\w*|timeout|ping)\b",
    "Interface": ASPECTS["Interface"] + r"|\b(inventory|hud)\b",
    "Value": ASPECTS["Value"] + r"|\b(cost|bargain|worth|affordable|overpriced)\b",
    "Progression": ASPECTS["Progression"] + r"|\b(exploration)\b",
}

# Evaluative cues are explicit so a reviewer can inspect the rule's decision.
POSITIVE = re.compile(
    r"\b(great|good|excellent|amazing|awesome|fantastic|fun|smooth|stable|responsive|polished|fair|affordable|love\w*|enjoy\w*|favorite|favourite|fix\w*|resolved|improv\w*|reliable|works?|working|worth|seamless|bargain)\b",
    re.I,
)
NEGATIVE = re.compile(
    r"\b(bad|awful|terrible|broken|unplayable|unreliable|unresponsive|boring|repetitive|frustrat\w*|exhaust\w*|painful\w*|expensive|overpriced|hate\w*|crash\w*|freez\w*|frozen|disconnect\w*|stutter\w*|laggy|lags?|slow|ruin\w*|fail\w*|kick\w*|desync\w*|rubberband\w*|timeout|ridiculous)\b",
    re.I,
)
TOKENS = re.compile(r"[^\W_]+(?:['’][^\W_]+)?", re.UNICODE)
NEGATORS = {"not", "no", "never", "without", "neither", "hardly"}
BOUNDARY = re.compile(r"[.!?;,\r\n]+\s*|\b(?:but|however|yet|although|whereas|except|while)\b[\s,:]*", re.I)
NONASSERTION = re.compile(r"\b(?:if|unless|wish|wishes|wished|hope|hopes|hopefully)\b", re.I)
RESOLUTION = {"fix", "fixed", "resolved", "eliminated", "removed"}
MULTIPLAYER_COMPLAINT = re.compile(
    r"\b(?:(?:get|gets|got|getting)\s+kicked|can(?:not|'t)\s+(?:join|connect)|"
    r"unable\s+to\s+(?:join|connect)|(?:voice\s+chat\s+)?never\s+connects?|"
    r"stuck\s+(?:in|on)\s+(?:a\s+)?(?:queue|loading)|"
    r"(?:queue\s+times?|queue)\s+(?:is|are|takes?)\s+(?:forever|ridiculous)|"
    r"(?:matchmaking|matchmaker)\s+(?:fails?|failed|is\s+broken)|"
    r"takes\s+forever\s+to\s+find\s+(?:a\s+)?lobb(?:y|ies))\b",
    re.I,
)
PHRASE_CUES = [
    (re.compile(r"\b(?:do|does)\s+not\s+respond\b|\b(?:do|does)n't\s+respond\b", re.I), "negative"),
    (re.compile(r"\beasy\s+to\s+read\b", re.I), "positive"),
    (re.compile(r"\bgrind(?:ing)?\s+never\s+ends?\b", re.I), "negative"),
]


def is_negator(token):
    token = token.casefold().replace("’", "'")
    return token in NEGATORS or token.endswith("n't") or token == "cannot"


def negated_before(text, position):
    previous = [m.group().casefold() for m in TOKENS.finditer(text[:position])][-3:]
    if "not" in previous and "only" in previous[previous.index("not") + 1 :]:
        previous = [v for v in previous if v != "not"]
    return bool(sum(is_negator(v) for v in previous) % 2)


def aspect_mentions(text):
    found = {aspect for aspect, pattern in ASPECT_PATTERNS.items() if re.search(pattern, text, re.I)}
    if MULTIPLAYER_COMPLAINT.search(text):
        found.add("Multiplayer")
    return found


def cues(text, offset=0):
    found = []
    for pattern, original in [(POSITIVE, "positive"), (NEGATIVE, "negative")]:
        for match in pattern.finditer(text):
            if original == "negative" and re.match(r"\s+(?:logs?|reports?)\b", text[match.end() :], re.I):
                continue
            negated = negated_before(text, match.start())
            if original == "negative":
                # A nearby repair verb scopes over the failure cue. Check negation at
                # that verb, including contractions; do not invert the failure twice.
                previous = list(TOKENS.finditer(text[: match.start()]))[-3:]
                following = list(TOKENS.finditer(text[match.end() :]))[:3]
                repairs = [(m.start(), m.group()) for m in previous if m.group().casefold() in RESOLUTION] + [
                    (match.end() + m.start(), m.group())
                    for m in following
                    if m.group().casefold() in RESOLUTION
                ]
                if repairs:
                    repair_position, _ = min(repairs, key=lambda item: abs(item[0] - match.start()))
                    negated = not negated_before(text, repair_position)
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
    for match in MULTIPLAYER_COMPLAINT.finditer(text):
        found.append(
            {
                "start": offset + match.start(),
                "end": offset + match.end(),
                "passage": match.group(),
                "polarity": "negative",
                "negated": False,
            }
        )
    for pattern, polarity in PHRASE_CUES:
        for match in pattern.finditer(text):
            found.append(
                {
                    "start": offset + match.start(),
                    "end": offset + match.end(),
                    "passage": match.group(),
                    "polarity": polarity,
                    "negated": False,
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
        sentence_start = max((m.end() for m in re.finditer(r"[.!?\r\n]", text[:start])), default=0)
        nonassertion = NONASSERTION.search(text[sentence_start:end])
        guarded = False
        if re.match(r"\s*[.!?]*\?", text[end:]):
            polarity, reason = "uncertain", "A question is not an assertion of praise or criticism"
            guarded = True
        elif nonassertion:
            polarity, reason = "uncertain", "Conditional or wish wording does not establish a current outcome"
            guarded = True
        elif len(aspects) > 1 and len(polarities) > 1:
            polarity, reason = (
                "uncertain",
                "Multiple aspects and conflicting cues in one clause; attribution is ambiguous",
            )
            guarded = True
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
        if polarity_model is not None and aspects and not guarded:
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
        "method": "supervised-passage-v2" if polarity_model is not None else VERSION,
        "rules_version": VERSION,
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
            "Questions, explicit conditionals/wishes, and ambiguous multi-topic attribution abstain even with a learned classifier.",
            "Passages are exact source spans, not proof that attribution is correct.",
            "Overall recommendations are not inputs and are never assigned to every aspect.",
        ],
    }
