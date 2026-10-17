# Security and privacy

The development service binds to loopback. Do not expose real mode publicly: its evidence endpoint intentionally serves private source text for local inspection. Public artifacts and Docker default to synthetic mode.

Input text is not persisted or sent to external inference. Prediction accepts at most 8,000 characters, caps request bodies at 40,000 bytes, and limits each client address to 30 predictions per minute per process. This limiter is for the local single-worker build; a public deployment needs a shared edge limiter, proxy body limits, HTTPS, and an approved data/privacy policy. CORS is not enabled: the app uses same-origin requests.

Review text is rendered through React text nodes. Embedded markup and instructions are data. Never load uploaded joblib/pickle artifacts. Only locally generated trusted artifacts are loaded by the service. Author groups are HMAC pseudonyms, not guaranteed anonymous data. The private key stays in the ignored private directory.

Report a vulnerability through a private GitHub security advisory once a repository exists. Do not post secrets or source review records in issues.
