# Candidate selection

Metadata and tiny source-schema spikes performed October 17, 2026. Source totals below are matching after-window records before edit/quality eligibility—not guaranteed usable training counts. Scores are transparent subjective feasibility judgments, 1–5, not measured product quality. No candidate was selected using prediction accuracy.

| Candidate / official update | Date | Matching after | Volume | Category breadth | Genre diversity | Confound manageability | Decision |
|---|---|---:|---:|---:|---:|---:|---|
| [Deep Rock Galactic / Season 05](https://steamcommunity.com/games/DeepRockGalactic/announcements/detail/4174354336751077143) | 2024-06-13 | 2,953 | 4 | 5 | 4 | 3 | Primary development case |
| [Satisfactory / 1.0](https://steamcommunity.com/games/526870/announcements/detail/4567301015235883040) | 2024-09-10 | 7,366 | 5 | 4 | 5 | 2 | Second development candidate |
| [No Man's Sky / Worlds Part I, 5.0](https://steamcommunity.com/games/275850/announcements/detail/6401387156599058162) | 2024-07-17 | 4,956 | 4 | 5 | 5 | 2 | Frozen unseen-game candidate |
| [HELLDIVERS 2 / 1.001.100](https://steamcommunity.com/games/553850/announcements/detail/7147864422081646860) | 2024-09-17 | 3,229 | 4 | 5 | 3 | 1 | Alternate; many overlapping announcements |

Deep Rock Galactic makes the mixed-feedback problem concrete: a player may recommend a cooperative mining game while reporting connection problems. Its dated seasonal update offers technical, mission, progression, and interface topics without requiring invented business impact. Full collection subsequently revealed strong positive-label imbalance; the first classifier's failure is documented rather than hidden.

Satisfactory adds factory-building and progression vocabulary. Its 1.0 release also changes the audience, so before/after changes cannot be assigned to individual patch features. No Man's Sky offers a distinct exploration genre and is reserved before tuning. Its tiny schema response was not inspected for prediction or annotation decisions. No holdout model results exist.

All four have official developer notes. The metadata showed preview/announcement activity near the primary update and a nearby Chemical Agents Warbond announcement for HELLDIVERS 2. A full audit of subsequent patches, discounts, promotions, and player composition is pending. Confound scores express that uncertainty; they do not certify a clean comparison. Recorded API positive/negative summary fields establish both labels exist, but eligible minority support still needs measurement for additional games. Development/holdout roles are frozen in `configs/game_roles.json`.
