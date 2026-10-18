# First baseline: what it demonstrates and where it fails

This report is development validation, not a final benchmark. It concerns an October 17, 2026 retrospective snapshot around Deep Rock Galactic's Season 05 update.

## Cohort and split

3,883 returned distinct reviews; 3,575 eligible after excluding 291 post-cutoff edits and 17 empty texts. Raw recommendation analysis retains naturally occurring duplicate text; model evaluation separately removes 866 exact/near-duplicate records using a frozen greedy token-trigram Jaccard threshold of 0.85. Keep the earliest-created record in each match; latest observed version per review precedes that operation. The greedy policy is order-dependent and is not a complete semantic-duplicate detector. Conflicting duplicate labels are not independently adjudicated yet.

The remaining 2,709 modeling records split chronologically: 1,896 training, 406 validation, 407 locked temporal test. Boundary timestamps are June 20, 2024 05:32:56 UTC and June 23, 2024 16:32:06 UTC. Tied timestamps remain together. Train/validation HMAC author overlap was zero in this collection. This does not establish anonymity or pretraining independence. The final test's predictions and labels have not been examined for model selection.

## Baseline

Text-only word unigram/bigram TF-IDF, at most 30,000 features, sublinear TF, logistic regression with defaults other than max_iter=500 and random_state=42. Vocabulary and IDF fit only training text. No labels, metadata, author IDs, game IDs, votes, or future proxies are features. Unicode text, negation, punctuation, contrast, and gaming vocabulary are retained apart from versioned whitespace/BBCode cleanup. The vectorizer's standard word tokenization still affects punctuation and one-character tokens. Only one seed was run for this initial deterministic classical configuration.

| Metric | TF-IDF/logistic regression | Majority baseline |
|---|---:|---:|
| Validation macro F1 | 0.4925 | 0.4925 |
| Validation accuracy | 0.9704 | 0.9704 |
| Negative-class recall | 0 | 0 |

Validation supports: 12 not recommended, 394 recommended. Confusion matrix, rows actual and columns predicted, order `[not recommended, recommended]`: `[[0, 12], [0, 394]]`.

The classifier predicts every validation record as recommended. Accuracy makes that look successful, but it fails to detect negative recommendations. It is a functioning engineering baseline, unsuitable for a quality claim. Initial fit time was approximately 0.10 seconds on the documented CPU, excluding preparation, duplicate detection, and collection. Scores are uncalibrated. Unknown vocabulary triggers abstention; there is no validated uncertainty threshold.

## Follow-up development experiment

The [negative-detection comparison](negative_detection.md) now compares class balancing, character n-grams, and thresholds on this same frozen partition. Add the second development game only under a newly documented, frozen multi-game split plan. The [bounded transformer study](nlp_study.md) is now complete with a pinned revision, license, compatible locked runtime and fixed training budget. Do not open either release test to choose settings. Existing small single-game partitions are developmental, not a completed two-game study.

Exploratory bootstrap uncertainty is now reported for the selected development detector. A 30-error human review, calibrated inference, unseen-game score, and human aspect/evidence relevance results remain pending. The bounded transformer comparison is documented in the NLP study. Do not interpret synthetic demo metrics as real data evaluation. The [aggregate artifact](../reports/milestone1-real-aggregates.json) contains actual values, split hash, environment, model checksum, and limitations. Private text and weights are excluded.
