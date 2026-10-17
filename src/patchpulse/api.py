"""Read-only curated analytics and bounded, local text inference."""

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
    model_id: str = "tfidf-logreg-v1"


class PredictResponse(BaseModel):
    task: str
    model_id: str
    model_revision: str | None = None
    mode: str
    prediction: str | None
    score_recommended: float | None
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
    return json.loads(path.read_text()) if path.exists() else {"status": "model unavailable", "mode": MODE}


@app.get("/api/evidence/{version_id}")
def evidence_version(version_id: str):
    for record in case()["evidence"]:
        if record["version_id"] == version_id:
            return {k: v for k, v in record.items() if k not in {"author_group", "text_hash"}}
    raise HTTPException(404, "Evidence version unavailable")


@lru_cache(maxsize=1)
def model():
    path = FOLDER / "baseline.joblib"
    if not path.exists():
        raise HTTPException(503, "Baseline model unavailable")
    # Only trusted artifacts created locally by our CLI; never load user-uploaded pickle/joblib.
    return joblib.load(path)


@app.post("/api/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, request: Request):
    if payload.model_id != "tfidf-logreg-v1":
        raise HTTPException(422, "Unsupported model")
    key = request.client.host if request.client else "local"
    queue = requests_by_ip[key]
    now = time.monotonic()
    while queue and now - queue[0] > 60:
        queue.popleft()
    if len(queue) >= 30:
        raise HTTPException(429, "Prediction limit reached; retry in a minute", headers={"Retry-After": "60"})
    queue.append(now)
    pipeline = model()
    text = normalize(payload.text)
    base = {
        "task": "recommendation prediction",
        "model_id": payload.model_id,
        "mode": MODE,
        "model_revision": evaluation().get("split_hash"),
    }
    if not text or pipeline["tfidf"].transform([text]).nnz == 0:
        return {
            **base,
            "prediction": None,
            "score_recommended": None,
            "abstention_reason": "No supported vocabulary",
        }
    score = float(pipeline.predict_proba([text])[0][list(pipeline.classes_).index(True)])
    return {
        **base,
        "prediction": "recommended" if score >= 0.5 else "not recommended",
        "score_recommended": score,
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
    def index():
        return FileResponse(DIST / "index.html")
