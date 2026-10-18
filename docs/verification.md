# Local verification — October 17, 2026

- 24 Python tests passed, including explicit HTTP-date retry handling and a duplicate-page progress bound.
- Eight Playwright cases passed across desktop Chromium and mobile Chromium emulating iPhone 13: navigation, filters/denominators, empty results, expansion, brief download, model inference, methodology, browser errors, keyboard focus, layout overflow, inert embedded markup/instructions, counts/share scale arithmetic, and keyboard search without intercepting text entry.
- Desktop and mobile case/evidence/model/methodology screenshots were inspected. All public screenshots use synthetic mode. Private real-mode smoke also passed observed rates, negative-label filters, evidence expansion, model inference, and browser-error checks. The real screenshot stays private.
- A clean Git archive successfully installed locked Python and Node dependencies, built the synthetic demo and frontend, and served the page/health/prediction through TestClient. It used no private data or Steam access.
- Python lint/format, TypeScript production build, npm dependency audit, and pip-audit passed locally. No known dependency vulnerabilities were reported; the local project itself is not a PyPI package and is skipped by pip-audit. Starlette emitted a TestClient/httpx deprecation warning, with no failing behavior; monitor dependency compatibility.
- The publication guard passed over tracked files after staging. Manual review confirmed synthetic-only screenshots and fixtures, aggregate-only research reports, and no private directory or handoff/course files. The guard is pattern-based and does not replace a full security audit.
- Local model and cached API timings are in `reports/local-benchmark.json`. No deployed/network/browser-load performance claim is made.
- Docker build is unverified because the local Linux Docker engine was not running. GitHub CI status cannot be claimed until the workflow is published and a run completes.
- Final temporal and unseen-game tests are unopened. No transformer, human aspect-label, evidence relevance, or launch-quality model result is claimed.

## Negative-detection pause checkpoint — 2026-10-17

Local checks: 33 Python tests and 12 Playwright tests passed across desktop Chromium and the mobile viewport. Ruff lint/format, TypeScript/Vite production build, staged publication guard (75 files), pip-audit and npm audit passed; dependency audits reported no known vulnerabilities. The local package itself is not on PyPI and is skipped by pip-audit. Python tests retain the upstream Starlette/httpx TestClient deprecation warning.

Visual review covered the detector comparison and annotation workspace on desktop/mobile; checked keyboard selection, emoji offset conversion, explicit human-review gating, exported spans, detector request selection, and visible thresholds. Screenshots use synthetic examples only. Actual human review remains pending, and no locked-test evaluation was run. This adds no Docker or deployed performance verification.


## NLP-focused increment — 2026-10-18

Local checks: 45 Python tests passed with the optional neural dependencies installed, including a network-free random tiny DistilBERT smoke verifying gradients reach both encoder and classification head. Standard CI without the neural extra skips that optional smoke. Fourteen desktop/mobile browser tests passed, including the aggregate neural study and explicit failure outcome. Ruff lint/format, production TypeScript/Vite build and npm audit passed. pip-audit found no known vulnerabilities in auditable packages; the local project and CUDA-specific `torch 2.14.1+cu130` build were skipped because those exact versions are not on PyPI. Do not describe that as a comprehensive audit of the CUDA runtime.

The actual local neural experiment fine-tuned the pinned DistilBERT on the frozen training partition and evaluated only development validation: six runs, twelve epoch evaluations, all majority-class decisions at .5. Source/lock/config/manifest/checkpoint fingerprints are recorded. No source text or fitted weights are public. Final-test flag and original manifest remain unchanged. Visual review covered the desktop/mobile methodology view; synthetic evidence screenshots remain distinct from aggregate real-data reports. Human aspect labels, final quality, Docker and deployment remain unverified/pending.


## Aspect sentiment and synthetic continuation

69 local Python tests passed with neural extras installed; 22 desktop/mobile browser tests passed. Covered clause/contrast scope, negation, resolved failures, questions, mixed-aspect aggregation, uncertain versus neutral, exact emoji offsets, grouped passage splits, duplicate/conflicting labels, insufficient support, model round trips and integrity, bounded API input, Evidence-to-lab handoff, HTML escaping, synthetic-model provenance and annotation export/resume validation. TypeScript/Vite build and Ruff checks passed. The standard demo now trains its synthetic passage classifier automatically, without pretrained weights or paid services.

The 48 authored synthetic passages remain `human_reviewed: false`. Their fixed 36/12 supervised demonstration split produced approximately .211 macro F1; this weak workflow-only result is disclosed, not advertised as real-world accuracy. Real aspect training remains gated by actual reviewed labels, a frozen guide and class support. Real recommendation data/splits/weights and final tests were preserved. Desktop/mobile captures show only synthetic examples. No real complaint-change statistics, human agreement or final aspect quality is claimed.


## First-time reader copy review — 2026-10-18

Reworked the README and application around player-feedback questions, with plain-language navigation and definitions for sentiment, model thresholds, TF-IDF, precision, recall, macro F1 and neural experiment terms. Removed unexplained academic framing from the main presentation while preserving the detailed study and its limitations. No model, labels, data splits or reported measurements changed. TypeScript/Vite build and all 22 desktop/mobile browser checks passed. Visually reviewed the refreshed synthetic overview, feedback workspace and methodology captures; public screenshots contain invented examples only.


## Complaint/praise reliability increment — 2026-10-18

83 local Python tests passed (including the optional neural smoke); 24 desktop/mobile browser checks passed. Production TypeScript/Vite build and Ruff lint/format checks passed. Added 48 authored synthetic development scenarios with recorded v1 baseline, phenomenon slices, end-to-end praise/complaint counts, recommendation-prefix invariance and exact substring checks. Regression scoring itself is tested against known false-topic and abstention errors; published rule metrics and canonical cross-platform fingerprints are verified. The app rejects stale diagnostics. Browser checks cover unresolved-crash wording, learned-model abstention guards, diagnostic provenance and disclosure, in addition to the existing workflows.

Rules improved from 39 to 46 exact topic/polarity maps on these development cases; the small synthetic-trained classifier matches 23 after the same safety guards. Both comparisons are explicitly authored development evidence, with possible language overlap and no independent human review. Implicit-topic and descriptive-versus-uncertain failures remain reported. The fixed rule version is v2; fitted passage weights were not retrained or promoted. Real source data, recommendation models/splits and final-test locks remain unchanged. Synthetic desktop/mobile feedback and expanded validation screenshots were visually inspected. No real-player accuracy, human agreement, before/after complaint rate or deployment claim is added.
