# Author review and interview preparation

Status: independent author explanations and human labels still need to be recorded. These prompts are not completed assessments or fabricated answers in the author's voice. Implementation and experiment execution have been AI-assisted using Codex.

Use a private working note or a clearly attributed public learning log to record your own reasoning, the experiment/code you checked, and any decisions you changed. Ask for explanations or make a small reproducible change when something is unclear; being able to defend a decision matters more than reciting it.

1. **Problem framing:** Why can a recommended review contain a complaint? What target do Steam recommendation labels actually supervise, and what additional labels does aspect sentiment require?
2. **Representations:** Explain word bigrams, character n-grams, WordPiece and contextual self-attention using an original mixed-feedback example. What could each miss?
3. **Data integrity:** Explain creation versus last-update time, retrospective snapshot bias, the duplicate rule, author groups and the frozen temporal split. What still could leak through pretrained weights?
4. **Optimization:** Derive the inverse-frequency class weights from 64 negative and 1,832 recommended training cases. Explain how weighted cross-entropy, batch composition, AdamW, warmup and gradient clipping differ from changing a decision threshold.
5. **Results:** Explain why .970 accuracy with zero negative recall is a failure for the task. Read both confusion matrices. Why did we keep the .757 macro-F1 character model after training a transformer?
6. **Uncertainty:** Why are twelve negative validation examples fragile? Why does identical fixed-threshold behavior produce zero seed SD and a degenerate paired-bootstrap interval without proving certainty?
7. **Next experiment:** Write a hypothesis and train-only selection protocol before running another model. What result would change the hypothesis? Why should the locked test remain closed?
8. **Demonstration:** Run the synthetic demo, reproduce an aggregate calculation, inspect an exact evidence span, and explain the source-rights boundary. Separate your design/review work from AI-assisted implementation accurately.

Suggested hands-on ownership exercise: independently predict the consequences of changing a negative threshold on a small invented score/label table, calculate precision and recall, then verify with `recommendation_labels` and `metrics`. Keep that exercise synthetic; do not use final-test scores for practice tuning.
