import React, { useEffect, useState } from "react";
type Span = {
  aspect: string;
  polarity: string;
  start: number;
  end: number;
  passage: string;
};
type Row = {
  version_id: string;
  text: string;
  annotations: Span[];
  human_reviewed: boolean;
  reviewer_id?: string;
};
type Pilot = {
  mode: string;
  split_hash: string;
  aspects: string[];
  polarities: string[];
  records: Row[];
};
export function AnnotationApp() {
  const [pilot, setPilot] = useState<Pilot | null>(null),
    [error, setError] = useState(""),
    [index, setIndex] = useState(0),
    [reviewer, setReviewer] = useState(""),
    [aspect, setAspect] = useState(""),
    [polarity, setPolarity] = useState(""),
    [notice, setNotice] = useState("");
  const [selection, setSelection] = useState<{
    start: number;
    end: number;
    passage: string;
  } | null>(null);
  useEffect(() => {
    fetch("/api/annotation-pilot")
      .then((r) => {
        if (!r.ok)
          throw Error("Training sample unavailable. Build the dataset first.");
        return r.json();
      })
      .then(setPilot)
      .catch((e) => setError(e.message));
  }, []);
  const row = pilot?.records[index];
  const reviewed = pilot?.records.filter((r) => r.human_reviewed) ?? [];
  function update(value: Row) {
    setPilot(
      (p) =>
        p && {
          ...p,
          records: p.records.map((r, i) => (i === index ? value : r)),
        },
    );
  }
  function move(delta: number) {
    setIndex(index + delta);
    setSelection(null);
    setAspect("");
    setPolarity("");
    setNotice("");
  }
  function captureSelection(e: React.SyntheticEvent<HTMLTextAreaElement>) {
    const el = e.currentTarget;
    const start = el.selectionStart,
      end = el.selectionEnd;
    setSelection(
      end > start
        ? {
            start: Array.from(el.value.slice(0, start)).length,
            end: Array.from(el.value.slice(0, end)).length,
            passage: el.value.slice(start, end),
          }
        : null,
    );
  }
  function navigateSource(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (
      !["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key) ||
      e.altKey ||
      e.metaKey
    )
      return;
    const el = e.currentTarget,
      value = el.value;
    const start = el.selectionStart,
      end = el.selectionEnd;
    const backward = el.selectionDirection === "backward";
    const anchor = backward ? end : start,
      focus = backward ? start : end;
    let target = focus;
    if (e.key === "ArrowRight")
      target =
        !e.shiftKey && start !== end
          ? end
          : Math.min(
              value.length,
              focus + (value.codePointAt(focus)! > 0xffff ? 2 : 1),
            );
    if (e.key === "ArrowLeft") {
      const previous = Array.from(value.slice(0, focus)).at(-1);
      target =
        !e.shiftKey && start !== end
          ? start
          : Math.max(0, focus - (previous?.length ?? 0));
    }
    if (e.key === "Home")
      target = e.ctrlKey ? 0 : value.lastIndexOf("\n", focus - 1) + 1;
    if (e.key === "End") {
      const next = value.indexOf("\n", focus);
      target = e.ctrlKey || next < 0 ? value.length : next;
    }
    e.preventDefault();
    el.setSelectionRange(
      e.shiftKey ? Math.min(anchor, target) : target,
      e.shiftKey ? Math.max(anchor, target) : target,
      e.shiftKey && target < anchor ? "backward" : "forward",
    );
    captureSelection(e);
  }
  function download() {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(reviewed, null, 2)], {
        type: "application/json",
      }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `patchpulse-${pilot!.mode}-human-annotations.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <main className="annotation-workspace" id="main">
      <a href="/" className="annotation-back">
        ← Back to PatchPulse
      </a>
      <div className="hero">
        <div>
          <span className="eyebrow">
            HUMAN GROUND TRUTH · TRAINING DATA ONLY
          </span>
          <h1>
            Read closely.
            <br />
            <span className="hero-accent">Label deliberately.</span>
          </h1>
          <p>
            Mark exact aspect passages and their polarity. Source
            recommendations and model suggestions are hidden to reduce
            anchoring.
          </p>
        </div>
      </div>
      {error && (
        <div className="error" role="alert">
          {error}
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      )}
      {!pilot && !error && <p role="status">Loading training examples…</p>}
      {pilot && row && (
        <>
          <div className="mode-banner">
            <strong>
              {pilot.mode === "synthetic"
                ? "SYNTHETIC PRACTICE"
                : "PRIVATE TRAINING SAMPLE"}
            </strong>
            <span>
              {reviewed.length} / {pilot.records.length} reviewed. Exports
              contain source text; keep real-data files private.
            </span>
          </div>
          <section className="panel lab">
            <div className="panel-heading">
              <h2>
                Example {index + 1} of {pilot.records.length}
              </h2>
              <span className="small-tag">
                {row.human_reviewed ? "Reviewed" : "Needs human review"}
              </span>
            </div>
            <label htmlFor="reviewer">Reviewer pseudonym</label>
            <input
              id="reviewer"
              value={reviewer}
              maxLength={80}
              onChange={(e) => setReviewer(e.target.value)}
              placeholder="Use a consistent non-identifying label"
            />
            <details className="annotation-guide">
              <summary>Annotation guide</summary>
              <p>
                Select the shortest passage supporting an aspect and its
                polarity. Positive praises; negative criticizes; mixed contains
                both; neutral states without evaluation. Use Other issue for
                concrete issues outside the listed aspects. Zero annotations is
                valid when no aspect is supported. Read the entire example
                before marking it reviewed.
              </p>
              <p>
                Keyboard: focus source text, use Shift + arrow keys to select,
                then choose an aspect and polarity.
              </p>
            </details>
            <label htmlFor="source-text">Source text — select a passage</label>
            <textarea
              id="source-text"
              readOnly
              value={row.text}
              rows={8}
              onKeyDown={navigateSource}
              onSelect={captureSelection}
              onKeyUp={captureSelection}
              onPointerUp={captureSelection}
            />
            <p className="selected-passage">
              {selection
                ? `Selected: “${selection.passage}”`
                : "Select source text to add an evidence span."}
            </p>
            <div className="annotation-fields">
              <label htmlFor="span-aspect">
                Aspect
                <select
                  id="span-aspect"
                  value={aspect}
                  onChange={(e) => setAspect(e.target.value)}
                >
                  <option value="">Choose an aspect</option>
                  {pilot.aspects.map((a) => (
                    <option key={a}>{a}</option>
                  ))}
                </select>
              </label>
              <label htmlFor="span-polarity">
                Polarity
                <select
                  id="span-polarity"
                  value={polarity}
                  onChange={(e) => setPolarity(e.target.value)}
                >
                  <option value="">Choose polarity</option>
                  {pilot.polarities.map((p) => (
                    <option key={p}>{p}</option>
                  ))}
                </select>
              </label>
              <button
                disabled={!selection || !aspect || !polarity}
                onClick={() => {
                  update({
                    ...row,
                    annotations: [
                      ...row.annotations,
                      { ...selection!, aspect, polarity },
                    ],
                    human_reviewed: false,
                  });
                  setNotice(
                    "Evidence span added. Review the example before marking it reviewed.",
                  );
                }}
              >
                Add evidence span
              </button>
            </div>
            <ul className="annotation-spans">
              {row.annotations.map((a, i) => (
                <li key={i}>
                  <div>
                    <strong>
                      {a.aspect} · {a.polarity}
                    </strong>
                    <p>“{a.passage}”</p>
                    <small>
                      Unicode offsets [{a.start}, {a.end})
                    </small>
                  </div>
                  <button
                    aria-label={`Remove span ${i + 1}`}
                    onClick={() =>
                      update({
                        ...row,
                        annotations: row.annotations.filter((_, j) => j !== i),
                        human_reviewed: false,
                      })
                    }
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
            <div className="lab-actions">
              <span>
                {row.annotations.length} evidence spans · zero is valid after
                review
              </span>
              <button
                className="primary"
                disabled={!reviewer.trim()}
                onClick={() => {
                  update({
                    ...row,
                    human_reviewed: true,
                    reviewer_id: reviewer.trim(),
                  });
                  setNotice("Marked as human reviewed.");
                }}
              >
                Mark reviewed
              </button>
            </div>
            <p role="status">{notice}</p>
            <div className="pagination">
              <button disabled={index === 0} onClick={() => move(-1)}>
                ← Previous
              </button>
              <span>
                {index + 1} / {pilot.records.length}
              </span>
              <button
                disabled={index === pilot.records.length - 1}
                onClick={() => move(1)}
              >
                Next →
              </button>
            </div>
          </section>
          <section className="panel">
            <h2>Export reviewed labels</h2>
            <p>
              Only examples you explicitly mark reviewed are exported. Nothing
              is uploaded or saved by this page. Export before leaving;
              unexported work is lost on refresh. Keep the file for local import
              and quality checks.
            </p>
            <button
              className="secondary"
              disabled={!reviewed.length}
              onClick={download}
            >
              Export {reviewed.length} reviewed examples ↓
            </button>
            <p className="muted">
              Split fingerprint: <code>{pilot.split_hash.slice(0, 16)}…</code>
            </p>
          </section>
        </>
      )}
    </main>
  );
}
