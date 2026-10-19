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


## Feedback research studio redesign — 2026-10-18

Replaced the dark console styling with a warm light studio, indigo navigation/actions, teal/rose sentiment labels and a speech-note brand mark. Reorganized the overview into a compact study context, recorded recommendation summary, topic comparison, guided analysis handoff and review cards. Comparison boundaries and collection qualifications remain in keyboard-operable disclosures. The analysis workspace pairs input with passage notes and exact rule-cue highlights; Unicode code-point slicing preserves the quoted text, and learned predictions explicitly distinguish those highlights from model attribution. All review filters, pagination, exports, model selection, uncertainty explanations, provenance, methodology and blind annotation remain available.

Production TypeScript/Vite build passed. All 32 desktop/mobile browser checks passed, including 320/768/1024-pixel layouts, keyboard study context, guided handoff, emoji-preserving highlighted passages, learned-model explanation boundaries, pending requests and recoverable errors. The existing analysis, annotation, export, browser-error and inert HTML checks also passed. Refreshed synthetic-only desktop/mobile captures were visually inspected across overview, feedback analysis, review library, methodology and annotation. A focused computed text-contrast scan found no remaining low-contrast text in the inspected Overview, Analyze feedback and How it works views after corrections; this is not a comprehensive accessibility audit. Mobile inputs use 16-pixel text, visible focus and reduced-motion support remain intact. No backend, classifier, dataset, split, final-test state or reported model quality changed.


## Release-feedback workflow and game-development identity — 2026-10-18

Rebuilt the overview around a release comparison and sortable topic-mention movements, with Counts/Share scales and direct topic-to-review investigation. Added a master/detail review explorer that retains filters, denominators, pagination and source-version detail while switching the selected review. New topic investigations clear unrelated old filters; the not-recommended shortcut explicitly selects after-window recommendation metadata. Added a session-only Notebook for source-linked reviews and suggested passages, personal interpretations, removal and plain-text export. Saving a suggestion never makes it human ground truth. Pasted/edited text is marked as unverified source; source-version references are retained for collected reviews. Export content remains local and may contain private text. Analysis inputs/results survive internal navigation, but refresh/leaving clears session state. The separate recommendation model remains accessible in a disclosure.

The visual identity uses a graphite project rail, cool reading canvas, blue release panel and crisp cyan accents, replacing the warm paper treatment. Mobile prioritizes the actual comparison before introductory copy. All 40 desktop/mobile browser checks passed, including reader focus/selection, scoped shortcuts, note provenance/editing/export/removal/refresh clearing, uncertain-label retention, analysis-state continuity and 320-pixel task layouts. Production TypeScript/Vite build passed. Final synthetic-only desktop/mobile captures were inspected for overview, reader, analysis and notebook; a focused computed text-contrast scan covered all five workspaces without flagged text contrast failures. This is not a comprehensive accessibility audit. No backend, model weights, evaluation measurements, source dataset, split or final-test state changed.

## Dark feedback workspace refinement — 2026-10-18

Replaced circular recommendation graphics with aligned zero-to-100-percent bars and converted topic cards into comparable investigation rows. Added a consistent dark canvas, restrained series colors and compact layout across the existing review, analysis and notebook workflows. No detector or evaluation results changed.

## Local import and complaint-rule update — 2026-10-18

Added a browser-parsed CSV/JSON import workspace. A user maps a text column, optionally carries a review ID, and submits at most 200 reviews to the loopback API for transient rule-based candidate retrieval. The API never writes imported text to disk, returns exact source spans, limits candidates to 100 returned records, and exports a clearly provisional review queue. The batch request is bounded to 2 MB; the browser limits selected files to 1.5 MB.

Aspect rules are now v3. Explicit failed-matchmaking, failed-join, kick-event, queue, desync, rubberband and failed-repair language is handled conservatively, while questions and conditions still abstain. The authored development suite now has 47/48 exact review maps and 23/23 expected complaint decisions; this is a regression result from cases used during development, not an accuracy estimate for player reviews. The remaining descriptive server-browser mismatch stays visible. Actual human-reviewed evaluation is still required before reporting complaint detection as reliable or calculating real complaint rates.

Validation: 89 Python tests, lint and formatting checks passed; 48 desktop/mobile browser checks passed, including CSV import, malformed JSON feedback, candidate export, exact offsets and review scopes. The public-file guard passed for 118 tracked files.

## Public import presentation refresh — 2026-10-19

Added synthetic desktop and mobile captures of the local import flow after a CSV is mapped and the provisional candidate queue is returned. The README now shows that concrete workflow next to the input contract, privacy boundary, batching limit, and interpretation limits. Corrected documentation references to the current aspect-rules v3 detector; this does not change detector behavior or its evaluation status.

Validation: production build passed; all 40 Playwright checks passed across desktop/mobile. Visually inspected desktop overview and analysis plus mobile overview; refreshed synthetic screenshots. Focused computed text-contrast scan across five workspaces returned no failures after button/skip-link fixes (not a comprehensive accessibility audit).

## Game-developer investigation review — 2026-10-18

Added provisional rule-suggestion retrieval across recommendation labels, scoped to the selected topic and applied before pagination. The overview opens after-update potential complaints; exact matched passages remain next to the complete review. Added return-to-review navigation, isolated evidence errors with retry, stale-row hiding and user-authored next-investigation fields in notebook exports. Human-evaluated polarity remains gated; no model, training data, detector version or quality claim changed.

Validation: 84 Python tests passed; lint/format and production build passed; all 44 desktop/mobile browser tests passed, followed by focused passing notebook/export and triage checks after final refinements. Visually inspected desktop/mobile triage and refreshed synthetic captures. Five-workspace text-contrast scan found no failures. Local private-data timing for the after-window complaint filter was 0.760s cold and 0.005s warm; this is an implementation smoke check, not accuracy evidence. Source data remains private.
