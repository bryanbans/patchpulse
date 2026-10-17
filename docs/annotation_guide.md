# Development annotation pilot — guide v0.1

Purpose: label which aspects are discussed and their passage-level polarity without assuming a review's overall recommendation applies to every aspect. Rule/AI suggestions are provisional. Only actual human review supports human-ground-truth claims.

Export: `uv run python -m patchpulse annotate-export --mode real`. This creates a private, deterministic sample of up to 60 training-partition reviews. It hides the recorded recommendation and rule suggestions. Do not annotate the locked test during taxonomy refinement. The initial export exists locally in `private/real/annotation-pilot.json`.

For each record, add `reviewer_id`, set `human_reviewed` only after review, and add zero or more annotations with `aspect`, `polarity`, `start`, `end`, and `passage`. Offsets are zero-based, end-exclusive Python Unicode character indices in the exact displayed raw text; passage must equal `text[start:end]`. Browser UTF-16 offsets for emoji require conversion; this initial JSON workflow does not calculate them automatically. Preserve version_id. Import with `annotate-import --mode real --file PATH`. Validation checks identity, categories, human-review flag, reviewer ID, and exact spans. It cannot prove a person actually reviewed a record; provenance must be checked.

| Aspect | Include | Exclude |
|---|---|---|
| Performance | fps, frame drops, stutter | network disconnects |
| Stability | crash, freeze, failure to launch | difficulty frustration |
| Multiplayer | connection, lobby, server, cooperative session | combat balance |
| Gameplay | difficulty, weapons, mission mechanics | menu layout |
| Interface | controls, menus, keybind behavior | visual disability needs unless explicitly stated |
| Accessibility | subtitles, colorblind options, disability-related remapping/readability | any disliked design without an access barrier |
| Value | price, monetization, DLC value | general progression pace |
| Progression | unlocks, grind, content variety | raw technical performance |
| Other issue | explicit concern outside the taxonomy | unmentioned or purely unclear topics |

Polarity is positive, negative, mixed, or neutral/descriptive. Absent aspects receive no annotation; absent is not neutral. Mixed requires both positive and negative statements about the **same** aspect. For “I love exploration but the server disconnects,” mark progression/content positive if supported and multiplayer negative; do not automatically mark either mixed. Allow overlapping aspects and spans where the text supports them. Preserve uncertainty in a separate `notes` field for adjudication.

The UI currently shows keyword mentions and unreviewed polarity; it makes no validated complaint-change claims. Freeze the taxonomy after the training-only pilot. Plan 800 reviewed records across two development games and an unseen game, subject to feasible support. If only one person annotates, disclose single-annotator limitations and perform a consistency recheck. A second AI pass is not a second human reviewer. Assess evidence relevance separately from exact-span validity.
