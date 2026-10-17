# Model card — tfidf-logreg-v1

**Task:** predict a recorded Steam recommendation from review text. Not emotion detection, aspect sentiment, bug detection, or causal update analysis.

**State:** local exploratory baseline; uncalibrated, unsuitable for release-quality negative-review detection. Separate artifacts are trained from synthetic and real data. Both remain local and Git-ignored; the synthetic artifact is reproducible from original fixture text. The API reports mode and split revision; the real aggregate report records the artifact SHA-256.

**Inputs:** normalized review text only, at most 8,000 characters at inference. Versioned preprocessing preserves negation and contrast, collapses whitespace, removes simple BBCode tags. Word TF-IDF unigram/bigram vocabulary and IDF fit only training text. Logistic regression, max_iter 500, seed 42. No game, author, date, recommendation label, helpfulness, or post-review metadata features.

**Training:** primary eligible development records, chronological partitions and greedy duplicate exclusions. Exact counts and environment are in the aggregate evaluation. One initial seed/configuration; no final-test predictions produced. Unknown vocabulary causes abstention. Other scores are not validated probabilities and do not supply calibrated uncertainty.

**Validation:** 406 real records, 12 negative and 394 positive; macro F1 0.4925, negative recall 0, accuracy 0.9704. Every validation prediction is positive. Majority baseline is equal. This establishes a class-imbalance failure, not useful negative-class quality. No unseen-game result, transformer comparison, confidence interval, human aspect metric, or reviewed evidence relevance result exists.

**Use:** inspect the development workflow, investigate baseline failure, and test local inference behavior. Do not use for individual-player judgments, automated moderation, severity claims, or production recommendations. Synthetic metrics are workflow tests only. Training permissions and artifact distribution are unresolved; no fitted model is publicly redistributed.

**Next:** compare train-fitted class weighting and character n-grams on validation; assess error types; expand development data under a frozen evaluation plan. Preserve locked tests until selection is complete. A stronger model is a future measured result, not an assumed outcome.
