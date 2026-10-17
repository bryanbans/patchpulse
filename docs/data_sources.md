# Source feasibility and use audit

Reviewed October 17, 2026. This is a documented engineering assessment, not a determination that every proposed reuse is permitted.

## Official review source

[Valve IUserReviewsService documentation](https://partner.steamgames.com/doc/webapi/IUserReviewsService) describes anonymous GET requests to `https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/` with `input_json`. The old store `/appreviews` endpoint is deprecated. The live spike verified the `response` envelope, integer enums, cursor paging, timestamp fields, boolean recommendations, and HTTP status handling. Page size is at most 100. Anonymous responses may be cached; HTTP 429 signals rate limiting.

Recent=1, all recommendation types=0, all purchase types=1. English only, Steam off-topic filtering enabled. Both inclusive source date endpoints are passed, with application end-exclusive boundary translated to `end - 1`. No helpfulness-based selection or recommendation balancing is used.

Observed terminal-page behavior: `response.query_summary.num_reviews` is zero and `reviews` is absent. The parser recognizes this specific empty protobuf-array encoding; missing arrays without explicit zero metadata are errors. Source totals and returned counts are checked separately. After-window total_matching was 2,953; 2,952 distinct records were returned before a verified empty page. We do not know whether this is source-count drift, deletion, filtering behavior, or another API inconsistency. It is not silently imputed.

## Terms and unresolved permissions

[Steam Web API Terms of Use](https://steamcommunity.com/dev/apiterms) provide conditional API/data use and application display terms, reserve intellectual-property rights, impose privacy and attribution conditions, and permit service changes or termination. They do not establish a blanket open-data license. Application display is not the same permission as bulk dataset publication. Model training and redistribution of fitted artifacts are not expressly resolved by this audit. The terms' end-user-request/privacy wording also needs review for this particular research application before public deployment.

Decisions: perform a bounded local feasibility/research spike; do not assert unrestricted training rights; keep source text and all fitted models private; publish original synthetic fixtures and code with aggregate research reports only. Obtain appropriate clarification or choose a licensed alternative before a real-text public demo, bulk dataset release, model-artifact release, or broader research collection. Never infer permission from accessibility. No source reviews are quoted in public project prose or screenshots.

Collection does not crawl profiles. Only needed review fields enter the minimized private page cache. Raw author SteamIDs are replaced with locally keyed HMAC groups before persistence. Those groups are pseudonymous. The key and private artifacts are Git-ignored. Source listing URLs intentionally do not contain author IDs; exact local version endpoints provide the provenance path. Review IDs are retained privately for idempotence. Local files remain on this user's machine; no public retention or hosting jurisdiction has been selected. Delete private research data when no longer needed or if required by the applicable conditions. Future public operation needs an approved privacy/retention policy and source attribution.

## Update sources

Valve's `ISteamNews/GetNewsForApp/v2/` supplied developer-announcement titles, timestamps, and externalpost links. Follow those links to canonical announcement pages: the API news `gid` is **not** necessarily the announcement-detail ID. The first draft constructed a store link from the news ID; verification showed that returned a generic hub. The config now stores the verified canonical announcement URL.

The primary announcement was posted June 13, 2024 at 11:02:07 UTC. This is not a verified software deployment instant. The study therefore uses day precision: `[2024-05-30, 2024-06-13)` and `[2024-06-14, 2024-06-28)` UTC, omitting June 13.

See [candidate audit](candidates.md) and [retrieved source metadata](../reports/candidate-source-metadata.json). Game art, logos, course material, raw reviews, author identifiers, and pretrained weights are absent from public artifacts.
