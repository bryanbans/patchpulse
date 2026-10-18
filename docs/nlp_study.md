# PatchPulse: NLP study and portfolio case study

## The question

A player can recommend a game while criticizing a broken co-op session. Can we preserve that distinction and help a developer find specific complaints, with evidence, around an update?

PatchPulse is an independent personal portfolio project inspired by studying natural language processing during a computer science master's program focused on AI/ML. It is not a course submission or an institution-endorsed product. The point is to demonstrate model-building and evaluation judgment on a real problem. A dashboard is the presentation layer; the NLP study is the technical centerpiece.

## What is implemented

- A retrospective, versioned Deep Rock Galactic review study with explicit timestamp eligibility, duplicate controls, source coverage, and source-use limits.
- Text-only recommendation prediction: word/character/hybrid TF-IDF and logistic regression, followed by an experimentally fine-tuned DistilBERT comparison.
- Three-seed neural loss ablation, fixed-budget optimization, validation-only selection, error diagnostics, and documented deployment choice.
- Exact evidence navigation and a blinded human annotation pilot for the next task: aspect detection and polarity. Keyword mentions are still rules, not validated complaints.

The central aspect-sentiment feature is **not yet evaluated or release-ready**. The deterministic release brief is **not neural language generation**. No unseen-game or final temporal result has been produced.

## Model-specific preprocessing

Classical models learn word 1–2-grams or character-within-word 3–5-grams from training text only. Character features can encode fragments of misspellings and gaming slang, but this experiment does not establish that this caused their improvement. No lemmatization or stopword removal is assumed beneficial. Negation and contrast are retained by the shared whitespace/simple-BBCode normalization.

DistilBERT uses that same light normalization followed by its fixed pretrained uncased WordPiece tokenizer. Its vocabulary is not fitted on the project data. Unlike local n-grams, contextual self-attention combines information across the retained input. All 66,955,010 parameters, including a new randomly initialized recommendation head, are fine-tuned. The model is a pretrained encoder, not an out-of-the-box gaming sentiment model or text generator.

The neural token budget is 256 tokens with dynamic padding and right truncation. This truncates 40 of 1,896 training examples and 7 of 406 validation examples. Median lengths are 14 and 13 tokens respectively. A complaint at the end of a long review could be removed. The classical model and transformer therefore do not have identical text exposure. A head-tail/chunking ablation is a future experiment, not an implemented result.

## Controlled neural experiment

The protocol in `configs/transformer.json` was written before neural validation results were examined:

- Base: `distilbert/distilbert-base-uncased`, revision `12040accade4e8a0f71eabdb258fecc2e7e948be`, base card declares Apache-2.0.
- Same frozen 1,896 train / 406 validation / 407 locked temporal test membership as the classical study. Class 0 is not recommended; class 1 is recommended.
- Ordinary versus inverse-frequency class-weighted cross-entropy, weights calculated from training labels only: 14.8125 and 0.517467.
- Seeds 17, 42, 73; two epochs each; batch size 16; AdamW learning rate 2e-5, weight decay .01, linear schedule with 10% warmup, gradient clipping norm 1; float32.
- Fixed negative threshold .5, deliberately avoiding another threshold search on the small outer validation set. This differs from the classical models' training-only threshold tuning.
- Choose candidate and common epoch by mean macro F1 across seeds, then mean negative F1; ties keep declaration order. Representative seed is fixed at 42, never selected for its score.
- Local RTX 5070 Ti; 1,800-second training budget. No paid compute, external inference, account upload, or additional review collection.

There are six neural training runs and twelve epoch evaluations. Four candidate/common-epoch summaries are considered. The same development validation set previously selected among six classical candidates, so these are not independent confirmatory tests. Source fingerprints, split/config/lock hashes, checkpoint checksums, package versions and environment are in the generated report.

## Actual outcome

| Model/setup | Validation macro F1 | Negative precision | Negative recall | False alarms |
|---|---:|---:|---:|---:|
| First word TF-IDF baseline | .4925 | .0000 | .0000 | 0 |
| Selected balanced character TF-IDF | .7575 | .7143 | .4167 | 2 |
| DistilBERT, ordinary loss | .4925 at both epochs, all three seeds | .0000 | .0000 | 0 |
| DistilBERT, balanced loss | .4925 at both epochs, all three seeds | .0000 | .0000 | 0 |

There are only 12 negative and 394 recommended validation examples. The character model detects five negatives and misses seven. Every neural checkpoint predicts recommended at .5, so each misses all twelve negatives. The declared tie policy picks ordinary loss, epoch 1, fixed seed 42 as the representative neural checkpoint. This is a tie outcome, not evidence that ordinary loss is superior.

Retain the classical character model as the active local detector. More parameters and pretraining did not improve the tested operating point. This does not establish that transformers are inherently worse at the task. It establishes a failure of this particular data/optimization/token-budget/decision-threshold setup.

## Failure analysis: ranking is not the decision rule

The fixed-threshold collapse is measurable across all twelve checkpoints. Negative-class average precision nevertheless ranges from .257 to .725, while all predicted class labels remain identical. Class-balanced training changes ranking scores in this sample; that is not a measured recall improvement at .5. We do not choose an operating threshold, seed or checkpoint using these post-run diagnostic rankings.

Potential explanations include sparse minority supervision (64 negative training examples), minibatch composition, the optimization budget, threshold behavior and truncation. These are hypotheses; the experiment does not isolate their causal contributions. A disciplined follow-up would predeclare training-only grouped out-of-fold threshold selection and a minibatch/loss-normalization ablation. Do not quietly retune on the twelve negative outer-validation cases to produce a more appealing headline.

The paired label-stratified bootstrap for the representative neural checkpoint versus the original word baseline produces zero difference in every resample because their class decisions are identical. Its degenerate interval is a property of this conditional resampling calculation, not certainty about real-world quality. Seed SD of zero also describes decisions here, not seed-independent probability estimates or generalization.

[Full neural report](../reports/transformer-real.json) · [Aggregate failure diagnostics](../reports/transformer-diagnostics.json) · [Classical comparison](negative_detection.md).

## Resources and reproducibility

The recorded experiment elapsed time is approximately 83.9 seconds after tokenization. It includes six training runs, validation, model initialization/loading, checkpoint saves, bootstrap calculation and report preparation up to the timer sample. Peak allocated CUDA tensor memory was 2.92 GB (decimal). Neither number is deployment latency or total GPU memory. Dependency installation, initial tokenizer setup/tokenization and final report-file writing are outside that timer. Base-weight downloads inside model loading count if not already cached. Other local processes were running.

```shell
uv sync --extra neural --frozen
uv run --extra neural python -m patchpulse train-transformer --mode real
uv run --extra neural python scripts/analyze_neural_run.py
```

Requires the existing private case, original frozen split and baseline. Do not rebuild the real split. First use downloads the pinned base weights/tokenizer; model inputs are processed locally. Windows uses the locked official PyTorch CUDA 13.0 index; other platforms resolve the standard PyPI torch build. The core synthetic application and standard CI do not install the neural extra or download weights. Seeded deterministic algorithms are warn-only; bitwise cross-platform reproducibility is not claimed.

Keep all source text, per-review scores, error text and fitted weights private. The base model license does not resolve training-data or fitted-artifact redistribution rights. Pretraining corpus exposure also cannot be ruled out, so pretrained model independence is not claimed. [Source audit](data_sources.md).

## What completes the story

1. Actually review the training-only annotation pilot; record independent versus AI-assisted decisions and taxonomy ambiguities. Freeze the guide after the pilot. Do not treat this training pilot as held-out aspect quality evidence.
2. Obtain enough independent, human-reviewed aspect/polarity labels for a frozen development/evaluation plan. Compare rules with supervised aspect detection and review-aspect polarity classification. Evaluate detection, polarity and evidence relevance separately, including mixed feedback and absent aspects.
3. Resolve broader source-use decisions before expanding development collection. Keep the unseen-game holdout untouched during model/taxonomy selection.
4. Complete the bounded neural follow-up and human error review, then run locked temporal and unseen-game tests once selection is finished. Report any missed targets.
5. Update this case study with final results and demonstrate the complete complaint/evidence workflow before describing PatchPulse as a finished NLP application.

The portfolio should show the author's ability to explain and reproduce these choices. Development used AI-assisted implementation and experiment orchestration. [Author review prompts](author_review.md) separate existing artifacts from the author's still-to-be-recorded independent explanations. No inter-annotator agreement, production adoption, causal patch effect or completed mastery certification is claimed.

References: [DistilBERT model card](https://huggingface.co/distilbert/distilbert-base-uncased/tree/12040accade4e8a0f71eabdb258fecc2e7e948be), [Hugging Face sequence classification](https://huggingface.co/docs/transformers/v5.20.1/en/tasks/sequence_classification), [weighted cross-entropy](https://docs.pytorch.org/docs/2.14/generated/torch.nn.CrossEntropyLoss.html).
