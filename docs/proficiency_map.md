# Course-inspired proficiency evidence

PatchPulse is an independent portfolio project, not a course submission. This maps the D803 competency names supplied by the author to inspectable work; it does not substitute for a course rubric or attest that the author independently performed every implementation step.

| Competency | Implemented evidence | What the author should explain | Remaining evidence |
|---|---|---|---|
| Implements Natural Language Processing | Versioned normalization, word/character representations, pretrained WordPiece, classical classifiers, full-parameter DistilBERT fine-tuning | Negation, slang, tokenizer differences, encoder attention versus local n-grams, truncation and pretraining exposure | More robust neural operating-point study and final evaluation |
| Applies NLP for Text Analysis and Generation | Recommendation prediction, evidence spans, training annotation workflow and deterministic brief | Overall recommendation versus aspect polarity; absent versus neutral; limitations of a template | Human-evaluated aspect detection/polarity and evidence relevance. Neural language generation is not implemented or claimed |
| Optimizes Natural Language Models | Class weighting, training-only threshold tuning, grouped folds, three-seed neural loss ablation, AdamW schedule/clipping, per-class metrics and failure diagnostics | Why high accuracy can hide complete minority failure; why a stronger classical detector stays active | Human error analysis, neural follow-up, untouched temporal/unseen-game tests and final quality/resource tradeoff |

The project intentionally studies one compelling application in depth. It does not need unrelated translation or NER features to make a credible portfolio case. A generation feature is optional; add one only with an evidence-grounding/unsupported-claim evaluation, and label extractive or template summaries accurately.

Primary artifacts: [NLP study/case study](nlp_study.md), [classical protocol](negative_detection.md), [neural implementation](../src/patchpulse/neural.py), [frozen experiment config](../configs/transformer.json), [actual results](../reports/transformer-real.json), [annotation validation](../src/patchpulse/annotations.py), [author review](author_review.md).

A polished interface and a model name do not establish mastery. Clear hypotheses, correct implementation, meaningful comparisons, honest failures, and the author's ability to defend decisions provide the evidence. Public claims must remain at the implemented level until the remaining evaluations are done.


The [working aspect prototype](aspect_sentiment.md) adds explicit clause segmentation, negation scope, mixed-feedback aggregation, source evidence offsets, grouped passage-level supervised learning and an API/UI comparison. These are inspectable implementations. Synthetic training/evaluation and software tests do not substitute for real human-reviewed aspect quality or final-test results.
