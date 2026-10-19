# PatchPulse: a release-feedback workspace

## Users and jobs

PatchPulse is aimed at game developers and people researching player feedback. Design from the decision they are trying to make, then use visual identity to make that workflow clear and engaging. Similar workflows across products are fine; decorative differences are not a reason to add steps.

| User's job | Workspace behavior |
|---|---|
| Check the response around an update | Overview compares recorded recommendation rates/counts, with the exact after-minus-before difference and a visible non-causation qualification. |
| Decide which topic to investigate | Topic tiles rank absolute changes in mention share or combined mention volume. Counts/share are selectable, and one click opens the matching reviews. These are discussion changes, not complaint changes. |
| Understand a specific review | A persistent filtered list sits next to a full-text reader. Selecting a review keeps the list, filters, denominator and pagination available. The reader exposes source versions and can hand text to analysis. |
| Inspect praise and complaints | The analysis workspace pairs text with passage notes. Exact rule cues are highlighted in context, uncertainty remains visible, and the learned-model explanation boundary is explicit. The separate recommendation experiment is collapsed by default. |
| Turn evidence into a useful brief | Save a review or suggested passage to Notebook, retain its source/label/method, add a personal interpretation, and download plain-text research notes. Statistics still have their own data-brief export. |

New topic investigations clear unrelated old filters. The not-recommended shortcut explicitly selects the after window and recommendation metadata; it does not claim to filter all complaints. Analysis inputs/results survive navigation within the app, so users can visit Notebook and return without rerunning inference.

## Visual identity

Use a professional game-development workspace, a task-focused tool for inspecting feedback. A graphite study rail anchors the project and keeps game context visible. The main canvas stays cool and light for reading review text. Release-focused blue artwork, crisp surfaces and restrained cyan accents give the product energy; topic movement, the reader and the evidence stack provide its structure.

| Token | Value |
|---|---|
| Working canvas | `#f1f4f8` |
| Study rail | `#182238` |
| Primary ink | `#1d2538` |
| Primary action | `#4353ce` |
| Release panel | `#173565` |
| Release accent | `#86e0ff` |
| Surfaces | `#ffffff` |
| Borders | `#dce2ed` |
| Before series | `#7389bd` |
| After series | `#168193` |

Use the local system sans-serif stack, a compact typographic hierarchy and mostly 6–9-pixel component radii. Large release typography belongs beside actual comparison data and useful actions. Graphics show real sample values; they are not simulated live activity. Series colors encode time, while sentiment uses explicit praise/complaint/mixed/needs-review labels. Zero-support comparisons remain unestablished.

## Truth, privacy and accessibility

Notebook is an ephemeral research aid, not an annotation import or human ground truth. It retains data only in browser memory until refresh or leaving the app. Saving a machine suggestion does not verify it. Exports may contain private source text and identify themselves as unvalidated research notes. No automatic upload, browser-storage persistence or public publishing is added.

Keep source-version provenance, coverage, UTC window boundaries, sample sizes, uncertainty, synthetic mode and model limits inspectable. Real complaint-change statistics remain gated by actual evaluation. The redesign changes no detector, dataset, split, frozen final-test state or reported accuracy.

Native disclosures, visible focus, a skip link, accessible review descriptions and labeled controls support keyboard/screen-reader use. Selecting a review moves focus to its reader. Mobile places the actual update comparison before introductory copy; workspaces stack without hiding the source text or actions. Form text is at least 16 pixels on compact screens. Reduced-motion preferences remain supported. Focused text-contrast checks are useful but are not a comprehensive accessibility certification.

Browser checks cover topic scope, reader selection, session-note provenance, editing/export/removal, refresh clearing, analysis-state continuity, uncertainty retention and narrow layouts, alongside the existing analysis/annotation flows. Public screenshots use synthetic data only.
