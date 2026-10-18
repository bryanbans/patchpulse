# LinkedIn narrative — development draft, not approved for posting

## Intended release story

After studying Natural Language Processing as part of my computer science master's program focused on AI/ML, I became interested in a deceptively simple question: what can a thumbs-up review hide?

A player can recommend a game and still report frustrating multiplayer problems. That led me to build PatchPulse: a project exploring how to separate overall recommendations from specific feedback, and connect observations to their evidence.

The model study has already challenged my assumptions. In a small development sample, a character-based classical model detected five of twelve negative reviews with two false alarms. A fully fine-tuned DistilBERT experiment, across three seeds and two loss variants, predicted only the majority class at the tested threshold. Adding a transformer did not automatically improve the result.

I'm using those failures to guide the next experiments. Human-reviewed aspect evaluation and untouched final tests are still ahead, so this is a research preview rather than a finished release.

Code, protocols and measured limitations: https://github.com/bryanbans/patchpulse

#NLP #MachineLearning #PortfolioProject

## Publication conditions

This draft is truthful for the present development stage; it does not announce completed aspect sentiment or final-test quality. For the intended finished-project announcement, replace the pending-work paragraph with actual final outcomes only after those gates are met. The author should review the learning narrative and accurately explain their own contributions; implementation and experiment orchestration were AI-assisted. Use synthetic demo screenshots only. No public demo hosting is implied. Present the exact final post and media for explicit approval before posting.
