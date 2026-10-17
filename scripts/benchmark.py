"""Small local benchmark. Does not read locked-test records."""

import json
import platform
import statistics
import time
from pathlib import Path

import httpx
import joblib

root = Path(__file__).resolve().parents[1]
results = {
    "hardware": "Ryzen 7 7800X3D; 16 logical processors; 63.1 GiB RAM; Windows 11; CPU inference",
    "python": platform.python_version(),
    "repetitions": 100,
    "warmups": 10,
    "protocol": "Sequential localhost HTTP; no browser or WAN; model timing excludes HTTP. Other processes were running.",
    "batch_size": 1,
    "model": "selected private model",
    "input_distribution": "Three original synthetic sentences repeated; not a representative workload.",
}
samples = [
    "The game crashes and I cannot recommend it.",
    "Great missions and wonderful co-op content.",
    "I love the game but multiplayer disconnects ruin our sessions.",
]
active = json.loads((root / "private/real/active-model.json").read_text())
results["model"] = active["model_id"]
results["negative_threshold"] = active["negative_threshold"]
results["model_artifact_sha256"] = active["sha256"]
model = joblib.load(root / "private/real" / active["artifact"])
timings = []
for i in range(110):
    started = time.perf_counter()
    model.predict_proba([samples[i % len(samples)]])
    if i >= 10:
        timings.append((time.perf_counter() - started) * 1000)
results["model_forward_ms"] = {"median": statistics.median(timings), "p95": sorted(timings)[94]}
with httpx.Client(base_url="http://127.0.0.1:8001", timeout=30) as client:
    timings = []
    for i in range(110):
        started = time.perf_counter()
        r = client.get("/api/case-studies/drg-season-05")
        r.raise_for_status()
        if i >= 10:
            timings.append((time.perf_counter() - started) * 1000)
    results["cached_case_http_ms"] = {"median": statistics.median(timings), "p95": sorted(timings)[94]}
    r = client.post("/api/predict", json={"text": samples[0]})
    r.raise_for_status()
    assert r.json()["mode"] == "real"
(root / "reports/negative-detection-benchmark.json").write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
