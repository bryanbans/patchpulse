import React, { useEffect, useRef, useState } from "react";
type Evidence = {
  start: number;
  end: number;
  passage: string;
  polarity: string;
  reason: string;
  cues: {
    passage: string;
    negated: boolean;
    start: number;
    end: number;
    polarity: string;
  }[];
  score?: number;
};
type Analysis = {
  method: string;
  mode: string;
  label_source: string;
  validation_status: string;
  aspects: { aspect: string; polarity: string; evidence: Evidence[] }[];
  limitations: string[];
};
type DevelopmentChecks = {
  method: string;
  rules: {
    reviews: number;
    exact_review_matches: number;
    recommendation_invariance: { passed: number; total: number };
  };
  baseline?: { rules: { exact_review_matches: number } };
  synthetic_supervised?: { results: { exact_review_matches: number } };
};
const EXAMPLES = [
  {
    name: "Praise + complaint",
    text: "I recommend the game. Great missions, but our co-op sessions keep disconnecting.",
  },
  {
    name: "No crashes",
    text: "No crashes this week. The performance is not great, though.",
  },
  {
    name: "Mixed feedback",
    text: "The combat is fun but the weapons feel terrible.",
  },
  {
    name: "Topic mention only",
    text: "The server browser lists regional lobbies.",
  },
];
const labels: Record<string, string> = {
  positive: "Praise",
  negative: "Complaint",
  mixed: "Mixed feedback",
  neutral: "Descriptive",
  uncertain: "Needs review",
};
function explainReason(reason: string) {
  if (reason.includes("Multiple aspects"))
    return "This part of the review mentions several topics and contains conflicting wording. The rules cannot reliably tell which opinion belongs to which topic.";
  if (reason.includes("question"))
    return "This passage asks a question rather than clearly praising or criticizing the topic.";
  if (reason.includes("Conditional or wish"))
    return "This sentence describes a condition, hope, or wish. The detector leaves it for review rather than treating the wording as a confirmed current outcome.";
  if (reason.includes("without a recognized"))
    return "The topic was recognized, but no clear praise or criticism word was found.";
  if (reason.includes("Praise and criticism"))
    return "Both positive and negative wording refer to this topic.";
  if (reason.includes("Supervised passage"))
    return "The classifier estimated this passage's sentiment using patterns learned from labeled examples. Topic detection still uses keyword rules.";
  if (reason.includes("No supported"))
    return "The classifier did not recognize useful vocabulary in this passage.";
  return "The topic and the words below appeared in the same clause—a part of a sentence. The rules check up to three preceding words for negation, such as ‘not’, and nearby wording for resolved problems, such as ‘fixed crashes’.";
}

function PassageHighlight({ evidence }: { evidence: Evidence }) {
  const chars = Array.from(evidence.passage);
  const parts: React.ReactNode[] = [];
  let cursor = 0;
  for (const cue of evidence.cues) {
    const start = cue.start - evidence.start;
    const end = cue.end - evidence.start;
    if (start < cursor || end > chars.length || start < 0 || end <= start)
      continue;
    parts.push(chars.slice(cursor, start).join(""));
    parts.push(
      <mark key={`${start}-${end}`} data-tone={cue.polarity}>
        {chars.slice(start, end).join("")}
      </mark>,
    );
    cursor = end;
  }
  parts.push(chars.slice(cursor).join(""));
  return <>{parts}</>;
}

export function AspectLab({
  input,
}: {
  input?: { text: string; revision: number };
}) {
  const [text, setText] = useState(EXAMPLES[0].text),
    [method, setMethod] = useState("rules"),
    [methods, setMethods] = useState(["rules"]),
    [result, setResult] = useState<Analysis | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [syntheticModel, setSyntheticModel] = useState(true);
  const [checks, setChecks] = useState<DevelopmentChecks | null>(null);
  const revision = useRef(0);
  useEffect(() => {
    fetch("/api/feedback-status")
      .then((r) => (r.ok ? r.json() : null))
      .then((r) => {
        if (r) {
          setMethods(r.methods);
          setSyntheticModel(r.mode === "synthetic");
        }
      })
      .catch(() => {});
    fetch("/api/feedback-evaluation")
      .then((r) => (r.ok ? r.json() : null))
      .then(setChecks)
      .catch(() => {});
  }, []);
  useEffect(() => {
    if (input) {
      revision.current++;
      setText(input.text);
      setResult(null);
      setError("");
      setBusy(false);
    }
  }, [input]);
  async function analyze() {
    const request = ++revision.current;
    setBusy(true);
    setResult(null);
    setError("");
    try {
      const response = await fetch("/api/analyze-feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, method }),
      });
      if (!response.ok)
        throw Error(
          response.status === 429
            ? "Too many analyses. Wait a minute and retry."
            : `Analysis unavailable (${response.status}). Choose Topic and wording rules, or restart the local server and try again.`,
        );
      const data = await response.json();
      if (request === revision.current) setResult(data);
    } catch (e) {
      if (request === revision.current) setError((e as Error).message);
    } finally {
      if (request === revision.current) setBusy(false);
    }
  }
  return (
    <section
      className="panel lab feedback-lab"
      aria-labelledby="feedback-title"
    >
      <span className="eyebrow">PRAISE AND COMPLAINTS · PREVIEW</span>
      <h2 id="feedback-title">What does this review praise or criticize?</h2>
      <p>
        Paste a game review to explore feedback about topics such as gameplay,
        performance, or multiplayer. A player can recommend a game and still
        criticize one of its features.
      </p>
      <div className="feedback-note">
        <strong>Treat these as suggestions</strong>
        <span>
          This preview has not been validated on human-reviewed real player
          feedback. Check each suggestion against the quoted text. Sarcasm and
          topics that are only implied can be missed.
        </span>
      </div>
      <div className="feedback-workbench">
        <div className="feedback-compose">
          <h3>Start with a review</h3>
          <p className="compose-hint">
            Use an invented example or bring your own text.
          </p>
          <div className="example-picks" aria-label="Invented example reviews">
            {EXAMPLES.map((e) => (
              <button
                className="secondary"
                key={e.name}
                disabled={busy}
                onClick={() => {
                  revision.current++;
                  setText(e.text);
                  setResult(null);
                  setError("");
                }}
              >
                {e.name}
              </button>
            ))}
          </div>
          <label htmlFor="feedback-method">Analysis method</label>
          <select
            id="feedback-method"
            value={method}
            disabled={busy}
            onChange={(e) => {
              setMethod(e.target.value);
              setResult(null);
            }}
          >
            <option value="rules">Topic and wording rules (default)</option>
            {methods.includes("supervised") && (
              <option value="supervised">
                Learned text classifier ·{" "}
                {syntheticModel
                  ? "invented training examples"
                  : "reviewed training examples"}
              </option>
            )}
          </select>
          <label htmlFor="feedback-text">Review to analyze</label>
          <textarea
            id="feedback-text"
            rows={6}
            maxLength={8000}
            value={text}
            disabled={busy}
            onChange={(e) => {
              setText(e.target.value);
              setResult(null);
            }}
          />
          <div className="lab-actions">
            <span>{text.length} / 8,000 characters · input is not stored</span>
            <button
              className="primary"
              disabled={!text.trim() || busy}
              onClick={analyze}
            >
              {busy ? "Analyzing…" : "Analyze praise and complaints"}
            </button>
          </div>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </div>
        <section
          className="feedback-reading"
          aria-label="Passage notes"
          aria-busy={busy}
        >
          <div className="reading-heading">
            <h3>Passage notes</h3>
            <span className="small-tag">Suggested interpretations</span>
          </div>
          {!result && (
            <div className="reading-empty">
              <span className="reading-symbol" aria-hidden="true">
                “ ”
              </span>
              <h3>
                {busy
                  ? "Reading the feedback…"
                  : "A closer look at what players mean."}
              </h3>
              <p>
                {busy
                  ? "Finding topic words and checking the surrounding language."
                  : "Run an analysis to see suggested praise and complaints alongside the exact words behind them."}
              </p>
              <div className="sentiment-key">
                <span>Praise</span>
                <span>Complaint</span>
                <span>Mixed</span>
              </div>
              <p className="reading-caption">
                One review can contain different opinions about different
                topics.
              </p>
            </div>
          )}
          {result && (
            <div className="feedback-results" aria-live="polite">
              <p className="muted">
                {result.method.startsWith("aspect-rules-")
                  ? "Rule-based suggestions: topic words and nearby wording guide the labels."
                  : result.mode === "synthetic"
                    ? "Learned from invented example passages. This does not establish accuracy on real reviews."
                    : "Learned from reviewed training passages. Final accuracy has not been established."}
              </p>
              {result.aspects.length === 0 ? (
                <div className="empty">
                  No topic was recognized. The review may still contain a
                  complaint; the current topic rules may have missed it.
                </div>
              ) : (
                result.aspects.map((a) => (
                  <article
                    className={`feedback-card ${a.polarity}`}
                    key={a.aspect}
                  >
                    <div className="panel-heading">
                      <h3>{a.aspect}</h3>
                      <span
                        className={`pill ${a.polarity === "positive" ? "positive" : a.polarity === "negative" ? "negative" : ""}`}
                      >
                        {labels[a.polarity]} · suggested
                      </span>
                    </div>
                    {a.evidence.map((e, i) => (
                      <div className="feedback-evidence" key={i}>
                        <blockquote>
                          <PassageHighlight evidence={e} />
                        </blockquote>
                        {e.cues.length > 0 && (
                          <p className="highlight-caption">
                            {e.score !== undefined
                              ? "Highlights show rule cues, not the learned model’s reasoning."
                              : "Highlights show rule cues. Read them in the full passage’s context."}
                          </p>
                        )}
                        <p>{labels[e.polarity]}</p>
                        <details>
                          <summary>Why this label?</summary>
                          <p>{explainReason(e.reason)}</p>
                          <p>
                            Evidence position in the original text: [{e.start},{" "}
                            {e.end}). These are zero-based Unicode character
                            offsets; the end position is excluded.
                          </p>
                          {e.cues.length > 0 && (
                            <p>
                              {e.score !== undefined
                                ? "Rule cues for comparison (not a model explanation): "
                                : "Words used by the rules: "}
                              {e.cues
                                .map(
                                  (c) =>
                                    `${c.passage}${c.negated ? " (meaning changed by nearby wording)" : ""}`,
                                )
                                .join(", ")}
                            </p>
                          )}
                          {e.score !== undefined && (
                            <p>
                              Model score: {e.score.toFixed(3)} · uncalibrated
                              (not a verified probability of correctness)
                            </p>
                          )}
                        </details>
                      </div>
                    ))}
                  </article>
                ))
              )}
              <p className="muted">
                These labels help you inspect a review. They do not confirm a
                software defect or measure how complaints changed after an
                update.
              </p>
            </div>
          )}
        </section>
      </div>
      <details className="feedback-checks">
        <summary>How is this detector checked?</summary>
        {checks ? (
          <p>
            The current rules match the expected topic labels in{" "}
            {checks.rules.exact_review_matches} of {checks.rules.reviews}{" "}
            invented development scenarios
            {checks.baseline
              ? ` (previous rules: ${checks.baseline.rules.exact_review_matches})`
              : ""}
            . These scenarios cover negation, mixed feedback, questions, repair
            wording, and ambiguous topics. They were used to improve the rules,
            so this is a regression check—not an estimate of accuracy on new
            reviews.
          </p>
        ) : (
          <p>
            Development check results are unavailable for this detector version.
            No real-world accuracy claim is made.
          </p>
        )}
        <p>
          Changing an overall recommendation should not change which topics are
          praised or criticized.
          {checks
            ? ` This holds for both tested recommendation prefixes in all ${checks.rules.recommendation_invariance.total} development scenarios.`
            : ""}{" "}
          Implicit topics can still be missed, and a topic without evaluative
          wording remains “Needs review.” Human-reviewed real player feedback is
          still required for a release-quality evaluation.
        </p>
        {checks?.synthetic_supervised && (
          <p>
            The small classifier trained on invented passages matches{" "}
            {checks.synthetic_supervised.results.exact_review_matches} of these{" "}
            {checks.rules.reviews} scenarios. It remains an experimental
            alternative; the transparent rules are the default. These scenarios
            may share wording with its training examples and are not a held-out
            test.
          </p>
        )}
      </details>
    </section>
  );
}
