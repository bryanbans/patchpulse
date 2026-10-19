# PatchPulse: a release-feedback workspace

## Users and jobs

PatchPulse is aimed at game developers and people researching player feedback. Design from the decision they are trying to make, then use visual identity to make that workflow clear and engaging. Similar workflows across products are fine; decorative differences are not a reason to add steps.

| User's job | Workspace behavior |
|---|---|
| Check the response around an update | Overview compares recorded recommendation rates/counts, with the exact after-minus-before difference and a visible non-causation qualification. |
| Decide which topic to investigate | Aligned topic rows rank absolute changes in mention share or combined mention volume. Counts/share are selectable, and one click opens the matching reviews. These are discussion changes, not complaint changes. |
| Understand a specific review | A persistent filtered list sits next to a full-text reader. Selecting a review keeps the list, filters, denominator and pagination available. The reader exposes source versions and can hand text to analysis. |
| Inspect praise and complaints | The analysis workspace pairs text with passage notes. Exact rule cues are highlighted in context, uncertainty remains visible, and the learned-model explanation boundary is explicit. The separate recommendation experiment is collapsed by default. |
| Turn evidence into a useful brief | Save a review or suggested passage to Notebook, retain its source/label/method, add a personal interpretation, and download plain-text research notes. Statistics still have their own data-brief export. |

New topic investigations clear unrelated old filters. The not-recommended shortcut explicitly selects the after window and recommendation metadata; it does not claim to filter all complaints. Analysis inputs/results survive navigation within the app, so users can visit Notebook and return without rerunning inference.

## Visual identity

Use a dark feedback-analysis workspace with a compact hierarchy, aligned comparisons, thin borders and restrained indigo/teal highlights. The supplied visual references inform density and depth; every visualization must still answer a real research question.

| Token | Value |
|---|---|
| Working canvas | `#10131b` |
| Study rail | `#131720` |
| Primary ink | `#e6eaf3` |
| Muted text | `#aeb8cc` |
| Primary action | `#5665c4` |
| Surfaces | `#181c26` |
| Borders | `#343b4c` |
| Before series | `#8793bb` |
| After series | `#70d3c7` |

Recommendation rates use aligned bars on a fixed 0–100% scale, with counts, rates and the after-minus-before difference explicitly labeled. Topic rows share columns and comparable bar scales; sorting chooses what to investigate, not what to believe. The shorter release introduction brings the evidence list closer to the top. Avoid decorative network diagrams that imply unsupported relationships or outcomes.

Use local system sans-serif type with monospace numeric chart labels and mostly 4–6-pixel radii. Series colors encode time; praise, complaints and uncertainty retain explicit labels. Charts show recorded data, never simulated activity.

## Truth, privacy and accessibility

Notebook is an ephemeral research aid, not an annotation import or human ground truth. It retains data only in browser memory until refresh or leaving the app. Saving a machine suggestion does not verify it. Exports may contain private source text and identify themselves as unvalidated research notes. No automatic upload, browser-storage persistence or public publishing is added.

Keep source-version provenance, coverage, UTC window boundaries, sample sizes, uncertainty, synthetic mode and model limits inspectable. Real complaint-change statistics remain gated by actual evaluation. The redesign changes no detector, dataset, split, frozen final-test state or reported accuracy.

Native disclosures, visible focus, a skip link, accessible review descriptions and labeled controls support keyboard/screen-reader use. Selecting a review moves focus to its reader. Mobile stacks the release context and comparison in reading order; workspaces stack without hiding the source text or actions. Form text is at least 16 pixels on compact screens. Reduced-motion preferences remain supported. Focused text-contrast checks are useful but are not a comprehensive accessibility certification.

Browser checks cover topic scope, reader selection, session-note provenance, editing/export/removal, refresh clearing, analysis-state continuity, uncertainty retention and narrow layouts, alongside the existing analysis/annotation flows. Public screenshots use synthetic data only.
