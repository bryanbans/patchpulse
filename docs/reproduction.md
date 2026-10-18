# Setup, reproduction, and verification

The [README](../README.md) explains the product questions and current scope. This page contains the engineering commands and boundaries.

## Offline demo and frontend development

Follow the README's setup commands for the synthetic demo. It uses 48 original examples; no Steam requests, paid inference, GPU, or pretrained weights are required after installation. Initial dependency installation requires internet.

For frontend development, keep the synthetic API running on port 8000 and run `npm run dev --prefix web`. Vite proxies API calls to port 8000. Restart the API after rebuilding data or models because snapshots and models are cached in-process.

The complaint/praise workspace is `/feedback`; it includes rules and a synthetic-trained classifier. `build-demo` trains both the recommendation baseline and synthetic passage classifier. Rebuild only the synthetic demo when following that setup. The browser annotation workspace is `/annotate`. The synthetic port is practice only. Private real mode uses port 8001. Export annotations before leaving or refreshing; the page does not persist work. See the [annotation guide](annotation_guide.md).

## Private source study

Review the [source-use audit](data_sources.md) before collecting or using real data. The code does not establish a data-reuse license. The initial study was a bounded private feasibility/research collection; broader collection and real-text public display remain gated by unresolved source-use decisions.

For an initial authorized snapshot, the collection/preparation workflow is:

```shell
uv run python -m patchpulse collect --cap-per-period 3500
uv run python -m patchpulse build-demo --mode real
uv run python -m patchpulse serve --mode real --port 8001
```

`build-demo --mode real` prepares the case and trains the original baseline, writing its split. **Do not rerun it on the existing frozen study just to compare models.** Keep the original case, `split.json`, and baseline evaluation intact. The existing snapshot's comparison commands are:

```shell
uv run python -m patchpulse compare-baselines --mode real
uv sync --extra neural --frozen
uv run --extra neural python -m patchpulse train-transformer --mode real
uv run --extra neural python scripts/analyze_neural_run.py
```

The optional neural extra downloads the pinned base model on first use. All review processing and training run locally. The neural experiment does not replace the active classical serving model. [Exact neural protocol and resource evidence](nlp_study.md).

Real mode is private local inspection. Do not deploy it publicly. Current API data can change, so a recollection is a new snapshot rather than an exact recreation of past text. Resume a collection with `collect --cap-per-period 3500 --resume-run RUN_ID` from its private manifest. Resume verifies saved page hashes. Each period has an independent cap; capped coverage remains incomplete.

Source text, pseudonymous author groups, keys, per-review scores, and fitted models stay in ignored `private/`. Public reports contain aggregate results only. [Dataset card](dataset_card.md) · [Source report](../reports/milestone1-real-aggregates.json).

## CLI commands

| Command | Purpose |
|---|---|
| `collect` | Retrieve a bounded private snapshot with checkpoints. |
| `prepare` | Build eligible cohorts without fitting a model. |
| `build-demo` | Prepare a case and train its initial baseline/split. |
| `train-baseline` | Train the initial baseline and write a split; preserve existing study splits when comparing models. |
| `compare-baselines` | Compare classical candidates against an existing frozen split. |
| `train-aspects` | Train passage polarity on synthetic fixtures, or on supported reviewed training labels after freezing the guide. |
| `train-transformer` | Run the optional bounded neural study against an existing frozen split. |
| `annotate-export` | Export a blinded sample from the frozen training partition. |
| `annotate-import` | Validate reviewed training labels; requires `--file PATH`. |
| `serve` | Start the local application; use `--mode real --port 8001` for private inspection. |

Default mode is synthetic. Full release evaluation and issue-grouping commands remain future work.

## Verification

```shell
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run pytest -q
npm run build --prefix web
npx --prefix web playwright install chromium
# Keep the synthetic API running on port 8000 in another terminal:
npm test --prefix web
uv run python -m pip_audit --local
npm audit --prefix web --audit-level=high
uv run python scripts/check_public_files.py
```

The optional network-free neural smoke test runs when the neural extra is installed; standard CI skips it. CI uses synthetic reviews and does not call Steam or download model weights. Dependency installation requires network access. The publication guard is a limited check, not a comprehensive secret scan. See the [verification record](verification.md) for actual checks, audit exclusions, and remaining limitations. Docker configuration is supplied; its build remains unverified.

## Local benchmarks

The initial CPU baseline and selected character detector have separate reports. Both use 100 warm forward calls over three repeated original synthetic sentences, excluding HTTP, and 100 warm localhost case requests. These are not representative production workloads, browser-load measurements, or deployed latency claims.

- [Initial baseline protocol and results](../reports/local-benchmark.json)
- [Selected character detector protocol and results](../reports/negative-detection-benchmark.json)

The neural study reports experiment elapsed time and peak allocated CUDA tensor memory. Those are different measurements from inference latency; see the [NLP study](nlp_study.md).
