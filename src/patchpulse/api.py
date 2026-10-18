"""Read-only curated analytics and bounded, local text inference."""

import hashlib
import json
import os
import time
import uuid
from collections import defaultdict, deque
from functools import lru_cache

import joblib
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from . import __version__
from .core import ASPECTS, PRIVATE, ROOT, normalize

app = FastAPI(title="PatchPulse", version=__version__)
MODE = os.environ.get("PATCHPULSE_MODE", "synthetic")
if MODE not in {"synthetic", "real"}:
    raise RuntimeError("Unsupported PATCHPULSE_MODE")
FOLDER = PRIVATE / MODE
requests_by_ip = defaultdict(deque)


class Coverage(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: str


class Period(BaseModel):
    count: int
    positive: int
    negative: int
    rate: float | None
    wilson_95: list[float] | None
    start: int
    end: int
    coverage: Coverage


class CaseResponse(BaseModel):
    id: str
    mode: str
    game: dict
    snapshot_date: str
    periods: dict[str, Period]
    change_pp: float | None
    exclusions: dict[str, int]
    mentions: list[dict]
    limitations: list[str]


class EvidenceResponse(BaseModel):
    total: int
    denominator: int
    offset: int
    records: list[dict]


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=8000)
    model_id: str = "selected"


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=8000)
    method: str = "rules"


class PredictResponse(BaseModel):
    task: str
    model_id: str
    model_revision: str | None = None
    mode: str
    prediction: str | None
    score_recommended: float | None
    score_not_recommended: float | None = None
    negative_threshold: float = 0.5
    calibrated: bool = False
    abstention_reason: str | None = None
    input_stored: bool = False


class BriefResponse(BaseModel):
    mode: str
    text: str
    evidence_ids: list[str]


@app.middleware("http")
async def request_controls(request: Request, call_next):
    # The app runs on loopback. Before public deployment, enforce a body limit in
    # the reverse proxy too. Bound streaming bodies even without Content-Length.
    if request.method == "POST":
        size = 0
        chunks = []
        async for chunk in request.stream():
            size += len(chunk)
            if size > 40000:
                return Response("Request too large", status_code=413)
            chunks.append(chunk)
        # Starlette's cached request replays _body to the downstream route.
        request._body = b"".join(chunks)
    response = await call_next(request)
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


@lru_cache(maxsize=1)
def case():
    path = FOLDER / "case.json"
    if not path.exists():
        raise HTTPException(503, "Dataset unavailable. Run python -m patchpulse build-demo first.")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/health")
def health():
    return {
        "status": "ready" if (FOLDER / "case.json").exists() else "not_ready",
        "version": __version__,
        "mode": MODE,
    }


@app.get("/api/games")
def games():
    return [case()["game"]]


@app.get("/api/updates")
def updates(app_id: int):
    if app_id != case()["game"]["app_id"]:
        raise HTTPException(404, "Game unavailable")
    return [{"id": case()["id"], **case()["game"]}]


@app.get("/api/case-studies/{case_id}", response_model=CaseResponse)
def study(case_id: str):
    if case_id != case()["id"]:
        raise HTTPException(404, "Case study unavailable")
    return {k: v for k, v in case().items() if k != "evidence"}


@app.get("/api/evidence", response_model=EvidenceResponse)
def evidence(
    request: Request,
    period: str = "all",
    aspect: str = "all",
    recommendation: str = "all",
    keyword: str = Query("", max_length=200),
    quality: str = "all",
    polarity: str = "all",
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    allowed = {"period", "aspect", "recommendation", "keyword", "quality", "polarity", "offset", "limit"}
    if set(request.query_params) - allowed:
        raise HTTPException(422, "Unknown evidence filter")
    if period not in {"all", "before", "after"} or aspect not in {"all", *ASPECTS}:
        raise HTTPException(422, "Unknown period or aspect")
    if recommendation not in {"all", "positive", "negative"} or quality not in {"all", "short"}:
        raise HTTPException(422, "Unknown recommendation or quality filter")
    if polarity not in {"all", "unreviewed"}:
        raise HTTPException(422, "Aspect polarity is not yet human evaluated; use unreviewed")
    rows = case()["evidence"]
    denominator = sum(period == "all" or r["period"] == period for r in rows)
    filtered = [
        r
        for r in rows
        if (period == "all" or r["period"] == period)
        and (aspect == "all" or any(m["aspect"] == aspect for m in r["mentions"]))
        and (recommendation == "all" or r["voted_up"] == (recommendation == "positive"))
        and keyword.casefold() in r["text"].casefold()
        and (quality == "all" or "short" in r["quality_flags"])
    ]
    safe = [
        {k: v for k, v in r.items() if k not in {"author_group", "text_hash"}}
        for r in filtered[offset : offset + limit]
    ]
    return {"total": len(filtered), "denominator": denominator, "offset": offset, "records": safe}


@app.get("/api/evaluation")
def evaluation():
    path = FOLDER / "evaluation.json"
    baseline = (
        json.loads(path.read_text()) if path.exists() else {"status": "model unavailable", "mode": MODE}
    )
    active = active_manifest()
    if not active:
        return {**baseline, "model_description": "Word unigram/bigram TF-IDF + logistic regression"}
    report = json.loads(private_artifact(active["report"]).read_text(encoding="utf-8"))
    return {
        **baseline,
        **report["selected"],
        "model_id": report["selected_id"],
        "model_description": model_info("selected")["description"],
        "comparison": report,
        "original_baseline": baseline,
    }


def private_artifact(relative):
    path = (FOLDER / relative).resolve()
    if not path.is_relative_to(FOLDER.resolve()):
        raise HTTPException(503, "Model artifact configuration is invalid")
    return path


@lru_cache(maxsize=1)
def active_manifest():
    path = FOLDER / "active-model.json"
    return json.loads(path.read_text()) if path.exists() else None


def model_info(requested="selected"):
    active = active_manifest()
    if requested == "selected":
        requested = active["model_id"] if active else "tfidf-logreg-v1"
    if requested == "tfidf-logreg-v1":
        return {
            "id": requested,
            "artifact": "baseline.joblib",
            "negative_threshold": 0.5,
            "description": "Original word TF-IDF baseline",
            "configuration": {"features": "word"},
        }
    if active and requested in active.get("models", {}):
        info = active["models"][requested]
        names = {"word": "Word TF-IDF", "char": "Character TF-IDF", "hybrid": "Word + character TF-IDF"}
        description = names[info["configuration"]["features"]]
        if info["configuration"]["class_weight"]:
            description += " · balanced training weights"
        return {**info, "id": requested, "description": description}
    raise HTTPException(422, "Unsupported model")


@app.get("/api/models")
def available_models():
    active = active_manifest()
    ids = ["selected", "tfidf-logreg-v1"]
    if active:
        ids += [name for name in active.get("models", {}) if name != active["model_id"]]
    return [
        {
            "id": name,
            "resolved_id": model_info(name)["id"],
            "description": ("Selected: " if name == "selected" else "") + model_info(name)["description"],
            "negative_threshold": model_info(name)["negative_threshold"],
            "mode": MODE,
        }
        for name in ids
        if private_artifact(model_info(name)["artifact"]).exists()
    ]


@app.get("/api/evidence/{version_id}")
def evidence_version(version_id: str):
    for record in case()["evidence"]:
        if record["version_id"] == version_id:
            return {k: v for k, v in record.items() if k not in {"author_group", "text_hash"}}
    raise HTTPException(404, "Evidence version unavailable")


@app.get("/api/research-evaluation")
def research_evaluation():
    path = ROOT / "reports/negative-detection-real.json"
    if not path.exists():
        raise HTTPException(404, "Real-data comparison report is unavailable")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/neural-evaluation")
def neural_evaluation():
    path = ROOT / "reports/transformer-real.json"
    if not path.exists():
        raise HTTPException(404, "Neural development study is not available")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/annotation-pilot")
def annotation_pilot():
    import random

    split_path = FOLDER / "split.json"
    if not split_path.exists():
        raise HTTPException(503, "Training split unavailable")
    split = json.loads(split_path.read_text())
    lookup = {r["version_id"]: r for r in case()["evidence"]}
    from .experiments import frozen_development

    training, _ = frozen_development(list(lookup.values()), split)
    sampled = random.Random(42).sample(training, min(60, len(training)))
    return {
        "mode": MODE,
        "split_hash": split["split_hash"],
        "guide_version": "0.1",
        "aspects": list(ASPECTS),
        "polarities": ["positive", "negative", "mixed", "neutral"],
        "records": [
            {"version_id": r["version_id"], "text": r["text"], "annotations": [], "human_reviewed": False}
            for r in sampled
        ],
    }


@lru_cache(maxsize=10)
def model(model_id="selected"):
    info = model_info(model_id)
    path = private_artifact(info["artifact"])
    if not path.exists():
        raise HTTPException(503, "Model unavailable")
    if info.get("sha256") and hashlib.sha256(path.read_bytes()).hexdigest() != info["sha256"]:
        raise HTTPException(503, "Model integrity check failed")
    # Only trusted artifacts created locally by our CLI; never load user-uploaded pickle/joblib.
    return joblib.load(path)


@lru_cache(maxsize=10)
def model_revision(model_id="selected"):
    return hashlib.sha256(private_artifact(model_info(model_id)["artifact"]).read_bytes()).hexdigest()


def enforce_inference_limit(request):
    key = request.client.host if request.client else "local"
    queue = requests_by_ip[key]
    now = time.monotonic()
    while queue and now - queue[0] > 60:
        queue.popleft()
    if len(queue) >= 30:
        raise HTTPException(429, "Prediction limit reached; retry in a minute", headers={"Retry-After": "60"})
    queue.append(now)


@app.post("/api/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, request: Request):
    info = model_info(payload.model_id)
    enforce_inference_limit(request)
    pipeline = model(payload.model_id)
    text = normalize(payload.text)
    base = {
        "task": "recommendation prediction",
        "model_id": info["id"],
        "mode": MODE,
        "model_revision": model_revision(payload.model_id),
        "negative_threshold": info["negative_threshold"],
    }
    if not text or pipeline[:-1].transform([text]).nnz == 0:
        return {
            **base,
            "prediction": None,
            "score_recommended": None,
            "abstention_reason": "No supported vocabulary",
        }
    scores = pipeline.predict_proba([text])[0]
    score = float(scores[list(pipeline.classes_).index(True)])
    negative = float(scores[list(pipeline.classes_).index(False)])
    return {
        **base,
        "prediction": "not recommended" if negative >= info["negative_threshold"] else "recommended",
        "score_recommended": score,
        "score_not_recommended": negative,
    }


@lru_cache(maxsize=1)
def aspect_manifest():
    path = FOLDER / "aspect-model.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


@lru_cache(maxsize=1)
def aspect_polarity_model():
    info = aspect_manifest()
    if not info or info["mode"] != MODE:
        raise HTTPException(
            503, "No supervised polarity model for this data mode. Human labels are required for real mode."
        )
    path = private_artifact(info["artifact"])
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != info["sha256"]:
        raise HTTPException(503, "Aspect model is missing or failed integrity checks")
    return joblib.load(path)


@app.get("/api/feedback-status")
def feedback_status():
    info = aspect_manifest()
    return {
        "mode": MODE,
        "methods": ["rules"] + (["supervised"] if info else []),
        "real_world_quality_established": False,
        "supervised_label_source": (
            "original synthetic fixtures" if MODE == "synthetic" else "human review attestations"
        )
        if info
        else None,
        "message": "Provisional clause-scoped rules are available. Human-reviewed aspect evaluation is pending.",
    }


@app.get("/api/feedback-evaluation")
def feedback_evaluation():
    from .aspect_evaluation import fingerprint

    path = ROOT / "reports/aspect-challenge.json"
    if not path.exists():
        raise HTTPException(404, "Synthetic development checks have not been generated")
    report = json.loads(path.read_text(encoding="utf-8"))
    source_hash = fingerprint(ROOT / "src/patchpulse/aspects.py")
    if report.get("detector_sha256") != source_hash:
        raise HTTPException(503, "Detector changed; regenerate the development checks")
    if report.get("suite_sha256") != fingerprint(ROOT / "data/fixtures/aspect-challenge.json"):
        raise HTTPException(503, "Development cases changed; regenerate the development checks")
    return report


@app.post("/api/analyze-feedback")
def analyze_feedback_request(payload: FeedbackRequest, request: Request):
    from .aspects import analyze_feedback

    if payload.method not in {"rules", "supervised"}:
        raise HTTPException(422, "Unsupported aspect method")
    if not payload.text.strip():
        raise HTTPException(422, "Enter review text")
    enforce_inference_limit(request)
    model = aspect_polarity_model() if payload.method == "supervised" else None
    result = analyze_feedback(payload.text, model)
    info = aspect_manifest() if model is not None else None
    return {
        **result,
        "mode": MODE,
        "label_source": (
            "synthetic authored examples; not real-world quality evidence"
            if MODE == "synthetic"
            else "human review attestations; development only"
        )
        if model
        else "handwritten lexical rules; not human-reviewed ground truth",
        "model_revision": info["sha256"] if info else None,
    }


@app.get("/api/briefs/{case_id}", response_model=BriefResponse)
def brief(case_id: str):
    study(case_id)
    c = case()
    lines = [
        f"PatchPulse | {c['game']['name']} | {c['game']['title']}",
        f"Mode: {MODE.upper()}. Snapshot: {c['snapshot_date']}. Retrospective snapshot study.",
        "Synthetic mode contains invented illustrative data, not Steam findings."
        if MODE == "synthetic"
        else "Local private research; source content is not cleared for redistribution.",
    ]
    for name, p in c["periods"].items():
        from datetime import UTC, datetime

        start, end = (datetime.fromtimestamp(p[k], UTC).isoformat() for k in ["start", "end"])
        lines.append(
            f"{name}: [{start}, {end}); {p['positive']}/{p['count']} recorded recommendations; coverage {p['coverage']['status']}. [finding:recorded-{name}]"
        )
    if c["change_pp"] is not None:
        lines.append(
            f"Within collected eligible reviews: {c['change_pp']:+.2f} percentage points after minus before. [finding:recorded-change]"
        )
    ids = [r["version_id"] for r in c["evidence"]]
    lines += [
        "Evidence versions for recorded statistics: " + ", ".join(ids),
        f"Exclusions: {json.dumps(c['exclusions'])}.",
        *c["limitations"],
        "Aspect complaint changes and positive themes are withheld pending human-reviewed polarity evaluation.",
    ]
    return {"mode": MODE, "text": "\n".join(lines), "evidence_ids": ids}


DIST = ROOT / "web/dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/")
    @app.get("/annotate")
    @app.get("/feedback")
    def index():
        return FileResponse(DIST / "index.html")
