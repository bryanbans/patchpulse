# PatchPulse

[![Application checks](https://github.com/bryanbans/patchpulse/actions/workflows/ci.yml/badge.svg)](https://github.com/bryanbans/patchpulse/actions/workflows/ci.yml)

**Find potential complaints in player reviews. Inspect the evidence. Decide what to investigate.**

A player can recommend a game and still report that matchmaking fails. If a team reads only the overall rating, that frustration can disappear in the aggregate.

PatchPulse is a local natural language processing (NLP) tool that helps a game team turn a review export into an investigation queue. It suggests topics and complaint passages, keeps those passages alongside the full reviews, and lets the team export the evidence for human review. The project also investigates how different NLP models predict overall recommendations—and documents what they miss.

[Get started](#install-and-run) · [See the workflow](#from-reviews-to-an-investigation) · [Explore the NLP study](docs/nlp_study.md)

## From reviews to an investigation

Imagine a developer reviewing player feedback after an update. One review says:

> “The missions are fun, but matchmaking fails every night.”

The developer wants to find comments like this without losing the praise or the surrounding context. With PatchPulse they can:

1. **Import feedback:** Open **Import data**, choose a CSV or JSON export, and map the review-text column and an optional review ID.
2. **Find leads:** Run the analysis to see the number of reviews with potential complaints and their suggested topics.
3. **Inspect the evidence:** Read each matching passage next to its full review. In the example above, the matchmaking passage is a multiplayer complaint candidate.
4. **Share the queue:** Export the candidates and use the source text to decide which leads deserve further investigation.

![Import workspace showing complaint candidates grouped by topic, matching passages, and full review text](assets/readme-desktop-import.png)

*The import workspace analyzing four invented reviews. The counts and comments illustrate the workflow; they are not findings about a game.*

Suggestions come from transparent language rules. They can miss complaints or flag passages incorrectly, so a candidate is a lead for a person to assess—not confirmation of a defect or a validated complaint rate.

## Try it with your own reviews

Install the app using the [steps below](#install-and-run), then open **Import data**.

For a quick test, save the following invented reviews as `reviews.csv` and import that file:

```csv
review_id,review
101,"The missions are fun, but matchmaking fails every night."
102,"The soundtrack is excellent."
```

Select `review` as the text column and `review_id` as the optional ID. PatchPulse will show potential complaints, their matching passages, and the complete review; use **Export candidates** to save the queue as a text file.

- CSV needs a header row. JSON may be an array of review objects or `{ "records": [...] }`.
- The text field is required; an ID field is optional, limited to 200 characters, and carried into the exported candidate queue.
- Each run accepts up to 200 nonempty reviews, each up to 8,000 characters; the selected file must be at most 1.5 MB. Split larger exports into batches.
- The browser parses the file and sends the selected text to the local server for analysis. PatchPulse does not automatically save the imported data or send it to a remote service. An exported queue is downloaded to your computer and contains review text.

The output lists exact passages that matched transparent complaint rules and a topic-level candidate count. It is a review queue, not an issue count, a defect confirmation, or a validated complaint rate. Read the full review before making a product decision; no match does not prove that a review contains no complaint.

Import analyzes reviews in the **Import data** workspace. Overview and Reviews continue to show the included example collection; imported files do not yet produce before-and-after comparisons.

## Current project status

**A working local feedback analysis tool with ongoing evaluation.**

- The included example collection contains 48 invented reviews. The app runs without Steam access, a GPU, or paid AI services after dependency installation, and accepts your own review exports.
- The overview highlights review volume, the most-mentioned topic after the update, and the largest change in topic share. Select a topic signal to inspect matching reviews in the example collection.
- A separate private study examines Deep Rock Galactic's Season 05 update. Public reports contain aggregate results; source review text, identifiers, and trained models stay out of this repository.
- Recommendation prediction is a separate model experiment. It never replaces a review's known recommendation in the before-and-after statistics.
- Complaint/praise rules now handle repair negation and preserve uncertainty for questions, wishes, and ambiguous topics. A [reproducible development suite](docs/aspect_sentiment.md#version-4-development-checks-and-measured-changes) records improvements and remaining failures; these authored checks do not establish real-world accuracy.
- Human-reviewed evaluation of complaint detection, final temporal evaluation, and evaluation on an unseen game remain unfinished. Authored example checks are development tests, not an independent benchmark.

## The NLP study

The technical challenge follows from the product question: understanding a review means more than assigning one positive or negative label. PatchPulse uses natural language processing (NLP)—methods for analyzing written language—to explore mixed feedback and compare ways of predicting overall recommendations.

In a separate private-data experiment, the study asks whether a more complex model better predicts a review's recorded recommendation, especially when not-recommended reviews are much less common. This experiment measures whole-review recommendation prediction; it does not validate the topic-level complaint detector. The app and documented protocols can be run locally. Reproducing the private study requires the separately retained source data and models.

![NLP research panel comparing the word baseline and selected model on not-recommended reviews](assets/readme-desktop-nlp.png)

*The application displays aggregate development results from the separate recommendation-prediction study.*

The first experiment exposed a common evaluation trap: **97% accuracy hid a model that detected none of the negative reviews.** Features based on short character sequences improved the result. A subsequent fine-tuning experiment with DistilBERT, a pretrained transformer language model, did not beat that classical model at its tested decision threshold.

| Recommendation model | Validation macro F1¹ | Not-recommended reviews detected | Recommended reviews incorrectly flagged |
|---|---:|---:|---:|
| Initial word-based classifier | 0.493 | 0 of 12 | 0 |
| Selected character-based classifier | **0.757** | **5 of 12** | **2** |
| DistilBERT, both tested loss variants | 0.493 | 0 of 12 | 0 |

¹ Macro F1 gives each recommendation class equal weight. These are development results on 406 reviews, including only 12 negative examples—not final performance estimates. Classical thresholds were tuned using training-only predictions; the neural threshold stayed at 0.5. DistilBERT was fully fine-tuned across three seeds, two loss variants, and two epochs per run. Every neural checkpoint made the same class decisions at that threshold.

The selected character model detected 5 of the 12 not-recommended reviews, missed 7, and incorrectly flagged 2 recommended reviews. Model selection used this same validation set, so the result is not a final performance estimate. The character classifier remains the active private detector. The study records the neural failure, uncertainty, truncation, and resource use rather than assuming a transformer must be better. Final tests remain unopened.

[Read the NLP case study](docs/nlp_study.md) · [Classical comparison](docs/negative_detection.md) · [Model cards](docs/model_card.md) · [Results and data limitations](docs/evaluation.md)

## Install and run

Install Python 3.12, [uv](https://docs.astral.sh/uv/), and Node.js 24, then run:

```shell
git clone https://github.com/bryanbans/patchpulse.git
cd patchpulse
uv sync --frozen --python 3.12
uv run python -m patchpulse build-demo
npm ci --prefix web
npm run build --prefix web
uv run python -m patchpulse serve
```

Open http://127.0.0.1:8000. Compare the two review windows, explore the evidence, try the text classifier in **Analyze feedback**, and inspect the results in **How it works**. Analysis text/results remain in browser memory while this workspace is open; the local server does not retain input. Refreshing or leaving clears that working state. Open `/feedback` to try **Praise + complaint**, **No crashes**, and **Mixed feedback**, or send a review from Reviews using **Analyze this review**.

To explore the included example collection, choose **Find potential complaints**, narrow by topic or text, and inspect the matching passage beside the full review. Use **Analyze this review** for a rule explanation, then return to your filters. Save useful reviews or passages to **Notebook**, add your interpretation, and export your notes. Labels remain suggestions; notes are session-only until exported and are cleared on refresh or when leaving the app.

The included example reviews are invented, so their statistics are not findings about a real game. The How it works page separately labels aggregate results from the private real-data study.

## Data and design

The private study retained **3,575 eligible reviews** across two 14-day windows around the update. Recommendation rates were 837/853 before and 2,643/2,722 after: a **1.03 percentage-point decrease within the collected sample**. Reviews edited beyond their window cutoff and empty texts were excluded. Collection also found a one-review discrepancy between the source's advertised count and returned records; that limitation remains visible.

PatchPulse preserves immutable review versions, records collection gaps, and removes exact/near duplicates before splitting modeling data. Training, validation, and final-test membership are frozen so model selection cannot silently change the comparison.

```mermaid
flowchart LR
  A[Official Steam review API] --> B[Private versioned reviews]
  B --> C[Eligible before/after samples]
  C --> D[Recorded statistics and evidence]
  C --> E[Frozen model-development splits]
  E --> F[Classical and transformer experiments]
  D --> G[FastAPI and React dashboard]
  F --> H[Aggregate evaluation reports]
  H --> G
  I[Invented example reviews] --> J[Local example and tests]
```

Built with Python, FastAPI, SQLite, scikit-learn, React, and TypeScript. Optional neural experiments use PyTorch and Hugging Face Transformers. Dependencies and model revisions are pinned.

## Explore the project

- [Setup, development, private-study reproduction, and checks](docs/reproduction.md)
- [NLP case study and failure analysis](docs/nlp_study.md)
- [Data source and reuse audit](docs/data_sources.md)
- [Human annotation guide](docs/annotation_guide.md)
- [Architecture decisions](docs/decisions.md)
- [Feedback studio design system](docs/design_system.md)
- [Verification record](docs/verification.md)
- [Milestones and remaining release work](docs/milestones.md)

The next steps are human-reviewed topic sentiment, a bounded follow-up to the neural experiment, and untouched final evaluations. Source-use questions must be resolved before broader collection or public display of real review text. Docker configuration is included, but its build has not been verified.

Original code is MIT licensed. Third-party data, models, assets, and trademarks are excluded from that grant. See [third-party notices](THIRD_PARTY_NOTICES.md) and [security/privacy](SECURITY.md). PatchPulse is an independent project and is not affiliated with Valve or the game developers.
