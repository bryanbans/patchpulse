# Local verification — October 17, 2026

- 22 Python tests passed before final hardening; final count is recorded in the chat/check output.
- Six Playwright cases passed across desktop Chromium and mobile Chromium emulating iPhone 13: navigation, filters/denominators, empty results, expansion, brief download, model inference, methodology, browser errors, keyboard focus, layout overflow, and inert embedded markup/instructions.
- Desktop and mobile case/evidence/model/methodology screenshots were inspected. All public screenshots use synthetic mode. Private real-mode smoke also passed observed rates, negative-label filters, evidence expansion, model inference, and browser-error checks. The real screenshot stays private.
- A clean Git archive successfully installed locked Python and Node dependencies, built the synthetic demo and frontend, and served the page/health/prediction through TestClient. It used no private data or Steam access.
- Python lint/format, TypeScript production build, npm dependency audit, and pip-audit passed locally. No known dependency vulnerabilities were reported; the local project itself is not a PyPI package and is skipped by pip-audit. Starlette emitted a TestClient/httpx deprecation warning, with no failing behavior; monitor dependency compatibility.
- The publication guard passed over tracked files after staging. Manual review confirmed synthetic-only screenshots and fixtures, aggregate-only research reports, and no private directory or handoff/course files. The guard is pattern-based and does not replace a full security audit.
- Local model and cached API timings are in `reports/local-benchmark.json`. No deployed/network/browser-load performance claim is made.
- Docker build is unverified because the local Linux Docker engine was not running. GitHub CI status cannot be claimed until the workflow is published and a run completes.
- Final temporal and unseen-game tests are unopened. No transformer, human aspect-label, evidence relevance, or launch-quality model result is claimed.
