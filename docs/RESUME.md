# Development pause — October 17, 2026

The user requested a pause after the negative-detection increment. This is a research preview, not v1.0.0. No LinkedIn post has been sent.

## Completed

- Six-candidate development comparison, preserving original split and locked final tests.
- Selected private character model: validation macro F1 0.7575 versus 0.4925; 5/12 negatives found, 2 false alarms. Only 12 validation negatives; no final quality claim.
- Model lab selection, visible negative thresholds, real aggregate comparison, training-only human annotation workspace.
- Private weights/source text remain excluded from public Git.

## Resume here

1. Open the private annotation workspace at http://127.0.0.1:8001/annotate. If the local server is stopped, use `uv run python -m patchpulse serve --mode real --port 8001`. Public synthetic practice is on port 8000. Review all 60 training examples, export before leaving (no browser persistence), and keep the real-data file private.
2. Validate/import actual human labels with `uv run python -m patchpulse annotate-import --mode real --file PATH`. Do not substitute AI labels for human ground truth. Freeze/adjudicate taxonomy after the pilot; note single-annotator limits.
3. Human-review selected detector errors in the active private experiment directory; these are still marked unreviewed. The selected model has 9 validation mistakes; the planned 30-error review requires expanding the reviewed error set, not inventing more errors.
4. Resolve source reuse/retention gates before expanding to the second development game. Preserve the unseen-game holdout and final temporal test.
5. Continue bounded transformer comparison, evaluated aspects/evidence, container/deployment/accessibility checks, release case study and explicit approval of exact LinkedIn copy.

Read `docs/negative_detection.md`, `docs/milestones.md`, and `docs/data_sources.md`. Do not rerun build-demo/train-baseline on the real snapshot just to run comparisons: preserve its frozen manifest. Restart the API after changing active model artifacts, since data/models are cached.
