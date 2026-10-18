# Model cards — recommendation detection

The active private detector is `char-balanced-v2`: character-within-word 3–5-gram TF-IDF, min_df 2, maximum 60,000 features (21,368 learned), balanced logistic regression C=4, max_iter=500, seed 42. Its negative threshold is 0.5, chosen from training-only grouped out-of-fold scores. Validation macro F1 is 0.7575; negative precision 0.7143, recall 0.4167, F1 0.5263; confusion matrix `[[5,7],[2,392]]`. It still misses 7 of 12 negatives. Scores are uncalibrated and deployment quality is unproven.

See [comparison protocol and limits](negative_detection.md). Private candidate artifacts are integrity-checked and selected through an atomic manifest. Original baseline remains available. Final-test, unseen-game and human aspect results remain pending. A bounded transformer comparison is documented below.

## Historical first baseline — tfidf-logreg-v1

**Task:** predict a recorded Steam recommendation from review text. Not emotion detection, aspect sentiment, bug detection, or causal update analysis.

**State:** local exploratory baseline; uncalibrated, unsuitable for release-quality negative-review detection. Separate artifacts are trained from synthetic and real data. Both remain local and Git-ignored; the synthetic artifact is reproducible from original fixture text. The API reports mode and split revision; the real aggregate report records the artifact SHA-256.

**Inputs:** normalized review text only, at most 8,000 characters at inference. Versioned preprocessing preserves negation and contrast, collapses whitespace, removes simple BBCode tags. Word TF-IDF unigram/bigram vocabulary and IDF fit only training text. Logistic regression, max_iter 500, seed 42. No game, author, date, recommendation label, helpfulness, or post-review metadata features.

**Training:** primary eligible development records, chronological partitions and greedy duplicate exclusions. Exact counts and environment are in the aggregate evaluation. One initial seed/configuration; no final-test predictions produced. Unknown vocabulary causes abstention. Other scores are not validated probabilities and do not supply calibrated uncertainty.

**Validation:** 406 real records, 12 negative and 394 positive; macro F1 0.4925, negative recall 0, accuracy 0.9704. Every validation prediction is positive. Majority baseline is equal. This establishes a class-imbalance failure, not useful negative-class quality. The new comparison adds exploratory validation intervals; unseen-game, human aspect, and reviewed evidence relevance results remain pending; the neural comparison now appears below.

**Use:** inspect the development workflow, investigate baseline failure, and test local inference behavior. Do not use for individual-player judgments, automated moderation, severity claims, or production recommendations. Synthetic metrics are workflow tests only. Training permissions and artifact distribution are unresolved; no fitted model is publicly redistributed.

**Next:** assess the new detector’s errors with a human; expand development data under a frozen evaluation plan. Preserve locked tests until selection is complete. A stronger model is a future measured result, not an assumed outcome.


## DistilBERT development comparison — 2026-10-18

Base `distilbert/distilbert-base-uncased` at revision `12040accade4e8a0f71eabdb258fecc2e7e948be`, base card Apache-2.0. All 66,955,010 parameters fine-tuned; ordinary versus train-weighted cross-entropy, seeds 17/42/73, two epochs, 256-token right truncation, fixed .5 negative threshold. All twelve epoch evaluations predict only recommended; macro F1 .4925 and negative recall zero. Retain the character classifier; neural weights are private research artifacts and are not active in the serving model registry. Pretraining bias/exposure, truncation, minority scarcity and reused validation restrict claims. These results do not establish aspect polarity or final generalization. See [study](nlp_study.md) and [generated report](../reports/transformer-real.json).
