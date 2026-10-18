import React, { useEffect, useRef, useState } from "react";
type Evidence = {
  start: number;
  end: number;
  passage: string;
  polarity: string;
  reason: string;
  cues: { passage: string; negated: boolean }[];
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
const EXAMPLES = [
  {
    name: "Praise + complaint",
    text: "I recommend the game. Great missions, but our co-op sessions keep disconnecting.",
  },
  {
    name: "Negation",
    text: "No crashes this week. The performance is not great, though.",
  },
  {
    name: "Same topic, mixed feedback",
    text: "The combat is fun but the weapons feel terrible.",
  },
  {
    name: "No clear sentiment",
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
            : `Analysis unavailable (${response.status}). Try the rule baseline or restart the local model server.`,
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
      <span className="eyebrow">ASPECT SENTIMENT · WORKING PROTOTYPE</span>
      <h2 id="feedback-title">One review. Different kinds of feedback.</h2>
      <p>
        Find praise and complaints about specific parts of a game. The overall
        recommendation is never used as an aspect label.
      </p>
      <div className="feedback-note">
        <strong>Provisional analysis</strong>
        <span>
          Rule results and synthetic-trained predictions have not established
          real-world quality. Check the passages; sarcasm, implicit topics and
          ambiguous scope can be missed.
        </span>
      </div>
      <div
        className="example-picks"
        aria-label="Original illustrative examples"
      >
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
      <label htmlFor="feedback-method">Aspect analysis method</label>
      <select
        id="feedback-method"
        value={method}
        disabled={busy}
        onChange={(e) => {
          setMethod(e.target.value);
          setResult(null);
        }}
      >
        <option value="rules">Transparent clause and negation rules</option>
        {methods.includes("supervised") && (
          <option value="supervised">
            Supervised passage classifier ·{" "}
            {syntheticModel
              ? "synthetic training"
              : "human-labeled development"}
          </option>
        )}
      </select>
      <label htmlFor="feedback-text">Feedback to analyze</label>
      <textarea
        id="feedback-text"
        rows={4}
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
      {result && (
        <div className="feedback-results" aria-live="polite">
          <p className="muted">
            {result.method} · {result.label_source}
          </p>
          {result.aspects.length === 0 ? (
            <div className="empty">
              No supported aspect was detected. This does not mean the review
              contains no complaint.
            </div>
          ) : (
            result.aspects.map((a) => (
              <article className={`feedback-card ${a.polarity}`} key={a.aspect}>
                <div className="panel-heading">
                  <h3>{a.aspect}</h3>
                  <span
                    className={`pill ${a.polarity === "positive" ? "positive" : a.polarity === "negative" ? "negative" : ""}`}
                  >
                    {labels[a.polarity]} · provisional
                  </span>
                </div>
                {a.evidence.map((e, i) => (
                  <div className="feedback-evidence" key={i}>
                    <blockquote>{e.passage}</blockquote>
                    <p>
                      {labels[e.polarity]} · raw-text Unicode offsets [{e.start}
                      , {e.end})
                    </p>
                    <details>
                      <summary>Why this label?</summary>
                      <p>{e.reason}</p>
                      {e.cues.length > 0 && (
                        <p>
                          Rule cues:{" "}
                          {e.cues
                            .map(
                              (c) =>
                                `${c.passage}${c.negated ? " (negated/resolved)" : ""}`,
                            )
                            .join(", ")}
                        </p>
                      )}
                      {e.score !== undefined && (
                        <p>
                          Classifier score: {e.score.toFixed(3)} · uncalibrated
                        </p>
                      )}
                    </details>
                  </div>
                ))}
              </article>
            ))
          )}
          <p className="muted">
            These are candidate interpretations, not confirmed issues or
            before/after complaint statistics.
          </p>
        </div>
      )}
    </section>
  );
}
