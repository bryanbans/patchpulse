# PatchPulse feedback research studio

## Product identity

A calm workspace for understanding player feedback around a game update. The design puts language, topics and the reviewer's next action ahead of a promotional hero. A warm light canvas, indigo controls, speech-note identity and readable review cards distinguish this product from a dark log-investigation console.

## Visual tokens

| Role | Value |
|---|---|
| Canvas | `#f6f5f1` |
| Surface | `#ffffff` |
| Primary ink | `#25283c` |
| Secondary text | `#626779` |
| Primary action / focus family | `#5146b7` |
| Soft indigo surface | `#eeebfa` |
| Before-period series | `#929ab9` |
| After-period series | `#6758cb` |
| Praise ink | `#176a56` |
| Complaint ink | `#a53354` |

Use the system sans-serif stack, without external font requests. Heading sizes stay compact; numeric results use tabular figures. Surface radii are 10–14 pixels, with subtle borders and restrained shadows. Reserve monospaced type for technical identifiers. Before/after series colors encode time, never sentiment. Sentiment labels always include words, not color alone.

## Workspace behavior

- Top navigation provides Overview, Reviews, Analyze feedback and How it works. Search retains its `/` keyboard shortcut; skip navigation and visible focus remain available.
- The one-study context control opens actual study information. It does not invent additional game choices. Full titles wrap on narrow screens. Comparison-window boundaries and collection qualifications remain available in native disclosures.
- Overview keeps recorded recommendations separate from topic mention counts. A guided example opens the analysis workspace without claiming to have computed results in advance.
- Reviews retain filtering, denominators, pagination, exact source-version details and the analysis handoff. The overview shows a small card-based sample; the Reviews view exposes the full collected sample.
- Analyze feedback pairs review entry with a passage-notes pane. Empty, pending, result, no-topic and error states use explicit text. On smaller screens, the panes stack in input-to-result order.
- Highlights mark exact rule-cue substrings using Unicode code-point offsets. They are contextual cues, not causal explanations or evidence that the learned classifier used those words. Learned-model results state this distinction explicitly.
- Real-world validation limits, synthetic provenance, abstention explanations, artifact diagnostics and the separate recommendation experiment remain accessible. The redesign changes no classifier, dataset, split or evaluation metric.
- Annotation retains the blind labeling workflow, explicit review attestation, keyboard selection and local export/resume. No browser persistence or automatic uploads are introduced.

## Responsive and accessibility checks

Browser checks cover desktop and mobile, plus 320-, 768- and 1024-pixel viewports, keyboard study disclosures, guided handoff, exact emoji-containing passages, pending/error feedback and navigation bounds. Mobile form text is 16 pixels to avoid unintended input zoom. Reduced-motion preferences are respected; native details/summary controls remain keyboard operable. A local computed foreground/background contrast scan covered the Overview, Analyze feedback and How it works views. This is a focused check, not a comprehensive accessibility certification.

Synthetic-only screenshots in `assets/` document the implementation. Source styles live in `web/src/style.css` and the main composition in `web/src/main.tsx` and `web/src/AspectLab.tsx`.
