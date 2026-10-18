# Latest development checkpoint — October 18, 2026

**New:** the [complaint/praise prototype](aspect_sentiment.md) works at http://127.0.0.1:8000/feedback. It defaults to transparent rules; a supervised passage classifier is trained on 48 authored synthetic examples (not human reviewed) for workflow demonstration. The user requested synthetic examples to continue development. Human labeling remains pending. Annotation exports can now be resumed in the browser.


PatchPulse is now framed around the NLP question: can we separate overall recommendations from specific complaints and preserve evidence? Read [the NLP study](nlp_study.md), [proficiency map](proficiency_map.md) and [author review guide](author_review.md). This is a personal portfolio research preview, not v1.0.0. No LinkedIn post has been sent.

## Newly completed

- DistilBERT full-parameter fine-tuning, pinned model revision, three seeds, ordinary/balanced loss, two epochs, fixed .5 threshold. All twelve epoch evaluations predict recommended; macro F1 .4925, negative recall zero. Classical character detector remains active at .7575 validation macro F1.
- Aggregate diagnostics, per-seed results, truncation/resource evidence, optional locked neural dependencies. Private weights/errors/scores stay ignored. Standard demo CI does not train/download a model.
- Annotation import rejects held-out records, changed source text, duplicate records/spans and invalid offsets, preserving the frozen training boundary.
- Updated methodology view, research case study, course-inspired competency mapping, author ownership prompts and an explicitly unfinished LinkedIn narrative draft.

## Resume priorities

1. Human annotation pilot is still pending. Private workspace: http://127.0.0.1:8001/annotate; restart with `uv run python -m patchpulse serve --mode real --port 8001` if needed. Review the 60 training examples, export before leaving (no persistence), and keep the file private. Do not reload an in-progress annotation tab.
2. Validate/import with `uv run python -m patchpulse annotate-import --mode real --file PATH`. Record independent versus AI-assisted annotations and taxonomy decisions. Freeze guide after the pilot; no claim of held-out aspect quality from training labels.
3. Write the next neural hypothesis before running it: training-only grouped threshold selection and minibatch/loss-normalization ablations are motivated by the ranking-versus-decision failure. Do not tune on the twelve negative outer-validation records. Human error review remains pending.
4. Resolve source-use/retention gates before broader collection; obtain sufficient independently reviewed aspect labels and a frozen supervised/evaluation plan. Keep third-game and temporal tests locked until final selection is complete.
5. Continue evaluated aspect detection/polarity/evidence, locked tests, remaining container/deployment checks, author explanation/replication and final portfolio release. Revise the LinkedIn draft with actual completed results; obtain exact-post approval before publishing.

Do not rerun real build-demo/train-baseline to run experiments: preserve the original split. Neural reproduction uses `uv sync --extra neural --frozen`, then `uv run --extra neural python -m patchpulse train-transformer --mode real`. This downloads the pinned base model on first use, runs locally and never opens final tests or replaces the active classical serving model. Backend model/data caches require restart after artifact changes.
