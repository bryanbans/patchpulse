# Negative detection: development comparison

The first detector predicted all validation records as recommended. This iteration tests whether class balancing, character features, and an explicit negative-score threshold improve minority-class detection without changing the original data split.

## Fixed protocol

`configs/negative_detection.json` declares six candidates, seed 42, three StratifiedGroupKFold training folds, a fixed negative-score threshold grid, selection tie-breakers, and 1,000 bootstrap resamples. Vocabulary, IDF and class weights are fitted inside each training fold. Author groups never cross inner folds. Inner folds shuffle within the training period; the outer validation remains chronological. Scores greater than or equal to the negative threshold predict not recommended.

The original manifest fingerprint is `74d00361fcc2a33215dfad6b2bb99075774e1b1c3ab29e8e26a144b6e84afefc`. Training contains 1,832 recommended and 64 not recommended records; validation contains 394 recommended and 12 not recommended. The 407 temporal-test records remain unopened. No extra game was collected or inspected for tuning. Final-test membership IDs are validated without reading their labels or text for experiments.

Thresholds maximize training out-of-fold macro F1, then negative F1, then proximity to 0.5. Candidate selection maximizes validation macro F1, then negative F1, negative precision, and fewer features. This is a bounded development search, not nested estimation of final generalization. A single deterministic lbfgs configuration is not multi-seed robustness evidence.

## Measured results

| Candidate | Threshold | Macro F1 | Negative precision | Negative recall |
|---|---:|---:|---:|---:|
| Original word | 0.50 | 0.4925 | 0.0000 | 0.0000 |
| Word + threshold | 0.05 | 0.6789 | 0.2759 | 0.6667 |
| Balanced word C=1 | 0.40 | 0.6747 | 0.3000 | 0.5000 |
| Balanced word C=4 | 0.30 | 0.6885 | 0.3333 | 0.5000 |
| **Balanced character C=4** | **0.50** | **0.7575** | **0.7143** | **0.4167** |
| Balanced hybrid C=4 | 0.25 | 0.7231 | 0.3889 | 0.5833 |

The selected character model detects 5 negatives, misses 7, and incorrectly flags 2 recommended reviews. The thresholded word model detects 8, misses 4, and incorrectly flags 21. Both are available privately in the model lab so this tradeoff is inspectable. The selected model has 21,368 features. The synthetic public demo retains its own synthetic model; real aggregates are labeled separately.

The selected model's label-stratified paired-bootstrap macro F1 interval is 0.609–0.878 (95%). The paired improvement over the original baseline interval is 0.117–0.385. These intervals condition on this small validation sample and do not account for selecting the winner on the same sample, source bias, author dependence, or unseen-game generalization. They are exploratory, not final-test evidence. Scores are uncalibrated. There is no new aspect sentiment claim.

## Reproduction and artifacts

With the existing private case, original `split.json`, and original `evaluation.json` preserved:

```shell
uv run python -m patchpulse compare-baselines --mode real
# Restart the real API to load the new manifest:
uv run python -m patchpulse serve --mode real --port 8001
```

Do not rebuild or retrain the original baseline to run this comparison. A new collection is a different source snapshot. Each run saves versioned private candidate weights, a full report, and unreviewed error records. An atomic active-model pointer selects the winner. Original weights and split files remain intact. The public report contains aggregate metrics, split/config/lock/artifact hashes and environment metadata only. Its `code_commit` is the prior HEAD at execution; `code_state` explicitly records the then-uncommitted experiment implementation, which is saved in this development commit.

[Aggregate report](../reports/negative-detection-real.json), [local CPU protocol](../reports/negative-detection-benchmark.json). The selected model's 100 warm forward calls had p95 0.339 ms on the documented CPU, using three repeated original synthetic sentences. This excludes HTTP and is not a production workload. Cached localhost case requests had p95 1.425 ms. No WAN/browser performance claim follows.

Next: actual human annotation and error review, source-rights decisions before broader collection, a second development game under a frozen plan, and a bounded transformer comparison. Keep final temporal and unseen-game evaluation locked until selection is finished.

Technical references: [scikit-learn logistic regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html), [decision thresholds](https://scikit-learn.org/stable/modules/classification_threshold.html), [FeatureUnion](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.FeatureUnion.html).
