# Dataset card — primary retrospective snapshot

**Scope:** local research; October 17, 2026 retrieval; Deep Rock Galactic, Steam app 548430; Season 05, June 13, 2024. This is not an openly licensed dataset distribution. Public artifacts contain aggregates and original synthetic fixtures only.

**Unit:** one latest observed review version per source review ID. Immutable private versions include raw text, SHA-256 text hash, source timestamps, observation timestamp, boolean recorded recommendation, language, and HMAC author group where supplied. No profile crawling, author biography, helpfulness features, or author IDs enter the model. Raw historical text before subsequent edits cannot be recovered from this snapshot.

**Selection:** English, all purchase types, both recommendation classes, Recent ordering, Steam off-topic filter enabled. Equal 14-day UTC windows exclude the release date. Separate 3,500-record caps were not reached. Verified empty terminal pages ended collection. Before: 931 distinct returned, 853 eligible. After: 2,952 distinct returned, 2,722 eligible; advertised matching count 2,953. The mismatch is unresolved and reported as partial/source-count discrepancy. Do not describe the sample as the player population.

**Exclusions:** 291 versions last edited at/after their period cutoff, 17 empty texts. Labels: before 837 recommended/16 not recommended; after 2,643/79. This class imbalance is preserved in analytics. Modeling independently removes 866 exact/near duplicates; see evaluation policy. Private review/version split manifests are hashed, and the aggregate report records the split hash and boundaries. No human aspect labels exist yet. Rule keyword matches are unreviewed mentions, not ground truth.

**Risks:** self-selection, source filters, deleted/unavailable records, edited-review exclusions, label imbalance, overlapping releases/promotions, retrospective snapshots, time-varying player composition, gaming memes/sarcasm, and imperfect duplicate detection. The API does not guarantee complete historical data. Text may include offensive content or embedded instructions; it is untrusted and rendered as text. HMAC groups remain pseudonymous rather than anonymous.

**Synthetic demo:** 48 original illustrative sentences with invented labels/times, visibly separate from real research. It supports reproducibility and UI tests, not external-validity claims. Do not merge its evaluation numbers with the real study.

**Retention and public use:** real text, private identifiers, collection pages, keys, and trained artifacts remain outside Git. Review local retention as the research progresses. Source training/display/redistribution questions remain open in the source audit. Public hosting and jurisdiction have not been chosen.
