import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";
import { ResearchPanel } from "./ResearchPanel";
import { NeuralPanel } from "./NeuralPanel";
import { AspectLab } from "./AspectLab";
import { AnnotationApp } from "./AnnotationApp";

type Period = {
  count: number;
  positive: number;
  negative: number;
  rate: number | null;
  start: number;
  end: number;
  coverage: { status: string; cap?: number };
};
type Case = {
  id: string;
  mode: string;
  snapshot_date: string;
  game: { name: string; title: string; date: string; source_url: string };
  periods: Record<string, Period>;
  change_pp: number | null;
  exclusions: Record<string, number>;
  mentions: { aspect: string; before: number; after: number }[];
  limitations: string[];
};
type Evidence = {
  version_id: string;
  text: string;
  voted_up: boolean;
  period: string;
  created_at: number;
  mentions: { aspect: string; passage: string; start: number; end: number }[];
  source_url: string | null;
};
type Evaluation = {
  status: string;
  mode: string;
  model_description?: string;
  macro_f1?: number;
  majority_macro_f1?: number;
  counts?: Record<string, number>;
  confusion_matrix?: number[][];
  train_seconds?: number;
  split_hash?: string;
};
async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, init);
  if (!r.ok)
    throw new Error(
      `Request unavailable (${r.status}). ${r.status === 503 ? "Build the local dataset and model first." : "Please retry or adjust the input."}`,
    );
  return r.json();
}
const date = (t: number) => new Date(t * 1000).toISOString().slice(0, 10);
const pct = (rate: number | null) =>
  rate === null ? "Insufficient data" : `${(rate * 100).toFixed(1)}%`;

function App() {
  const [feedbackInput, setFeedbackInput] = useState<{
    text: string;
    revision: number;
  }>();
  const searchRef = useRef<HTMLInputElement>(null);
  const [focusSearch, setFocusSearch] = useState(false);
  const [aspectView, setAspectView] = useState<"counts" | "share">("counts");
  const [data, setData] = useState<Case | null>(null),
    [error, setError] = useState(""),
    [tab, setTab] = useState(
      window.location.pathname === "/feedback"
        ? "Analyze feedback"
        : "Overview",
    );
  const [period, setPeriod] = useState("all"),
    [aspect, setAspect] = useState("all"),
    [recommendation, setRecommendation] = useState("all"),
    [keyword, setKeyword] = useState("");
  const [rows, setRows] = useState<Evidence[]>([]),
    [total, setTotal] = useState(0),
    [denominator, setDenominator] = useState(0),
    [offset, setOffset] = useState(0),
    [busy, setBusy] = useState(false),
    [expanded, setExpanded] = useState("");
  const [models, setModels] = useState<
    { id: string; description: string; negative_threshold: number }[]
  >([]);
  const [modelId, setModelId] = useState("selected");
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null),
    [text, setText] = useState(
      "I love the exploration, but multiplayer disconnects still interrupt our runs.",
    ),
    [prediction, setPrediction] = useState<{
      model_id: string;
      negative_threshold: number;
      score_not_recommended: number | null;
      prediction: string | null;
      score_recommended: number | null;
      abstention_reason: string | null;
    } | null>(null),
    [predicting, setPredicting] = useState(false),
    [predictError, setPredictError] = useState("");
  useEffect(() => {
    if (tab === "Reviews" && focusSearch) {
      searchRef.current?.focus();
      setFocusSearch(false);
    }
  }, [tab, focusSearch]);
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      const target = event.target as HTMLElement;
      if (
        event.key === "/" &&
        !event.ctrlKey &&
        !event.metaKey &&
        !target.isContentEditable &&
        !["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)
      ) {
        event.preventDefault();
        setTab("Reviews");
        setFocusSearch(true);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  useEffect(() => {
    api<Case>("/api/case-studies/drg-season-05")
      .then(setData)
      .catch((e) => setError(e.message));
    api<typeof models>("/api/models")
      .then(setModels)
      .catch(() => {});
    api<Evaluation>("/api/evaluation")
      .then(setEvaluation)
      .catch(() => {});
  }, []);
  useEffect(() => {
    let cancelled = false;
    setBusy(true);
    const q = new URLSearchParams({
      period,
      aspect,
      recommendation,
      keyword,
      offset: String(offset),
      limit: "12",
    });
    api<{ records: Evidence[]; total: number; denominator: number }>(
      "/api/evidence?" + q,
    )
      .then((x) => {
        if (!cancelled) {
          setRows(x.records);
          setTotal(x.total);
          setDenominator(x.denominator);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setBusy(false);
      });
    return () => {
      cancelled = true;
    };
  }, [period, aspect, recommendation, keyword, offset]);
  async function exportBrief() {
    try {
      const b = await api<{ text: string }>("/api/briefs/drg-season-05");
      const url = URL.createObjectURL(
        new Blob([b.text], { type: "text/plain;charset=utf-8" }),
      );
      const a = document.createElement("a");
      a.href = url;
      a.download = "patchpulse-release-brief.txt";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function predict() {
    setPredicting(true);
    setPredictError("");
    try {
      setPrediction(
        await api("/api/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, model_id: modelId }),
        }),
      );
    } catch (e) {
      setPredictError((e as Error).message);
    } finally {
      setPredicting(false);
    }
  }
  function selectAspect(value: string) {
    setAspect(value);
    setOffset(0);
    setTab("Reviews");
  }
  const hasFilters =
    period !== "all" ||
    aspect !== "all" ||
    recommendation !== "all" ||
    keyword !== "";
  function clearFilters() {
    setPeriod("all");
    setAspect("all");
    setRecommendation("all");
    setKeyword("");
    setOffset(0);
    setExpanded("");
  }
  const evidencePanel = (
    <section
      className="panel evidence"
      aria-labelledby="evidence-title"
      aria-busy={busy}
    >
      <div className="panel-heading">
        <div>
          <span className="eyebrow">TRACE EVERY OBSERVATION</span>
          <h2 id="evidence-title">The words behind the numbers</h2>
        </div>
        <span className="small-tag">
          {data?.mode === "synthetic"
            ? "Invented example reviews"
            : "Private source versions"}
        </span>
      </div>
      {tab !== "Overview" && (
        <div className="filters">
          <label>
            Window
            <select
              value={period}
              onChange={(e) => {
                setPeriod(e.target.value);
                setOffset(0);
              }}
            >
              <option value="all">Both windows</option>
              <option value="before">Before update</option>
              <option value="after">After update</option>
            </select>
          </label>
          <label>
            Topic mention
            <select
              value={aspect}
              onChange={(e) => {
                setAspect(e.target.value);
                setOffset(0);
              }}
            >
              <option value="all">All topics</option>
              {data?.mentions.map((m) => (
                <option key={m.aspect}>{m.aspect}</option>
              ))}
            </select>
          </label>
          <label>
            Recorded recommendation
            <select
              value={recommendation}
              onChange={(e) => {
                setRecommendation(e.target.value);
                setOffset(0);
              }}
            >
              <option value="all">All recommendations</option>
              <option value="positive">Recommended</option>
              <option value="negative">Not recommended</option>
            </select>
          </label>
          <label>
            Search text
            <input
              ref={searchRef}
              value={keyword}
              maxLength={200}
              placeholder="e.g. connection"
              onChange={(e) => {
                setKeyword(e.target.value);
                setOffset(0);
              }}
            />
          </label>
        </div>
      )}
      {hasFilters && (
        <div className="filter-summary">
          <span>
            Filtered to{" "}
            {period === "all" ? "both windows" : `the ${period} window`}
            {aspect !== "all" ? ` · ${aspect}` : ""}
            {recommendation !== "all"
              ? ` · ${recommendation === "positive" ? "recommended" : "not recommended"}`
              : ""}
            {keyword ? ` · “${keyword}”` : ""}
          </span>
          <button className="text-button" onClick={clearFilters}>
            Clear filters
          </button>
        </div>
      )}
      <p className="muted" role="status">
        {busy
          ? "Loading evidence…"
          : `${total} matching reviews / ${denominator} eligible reviews in selected window. Topic mentions may overlap.`}
      </p>
      {!busy && rows.length === 0 && (
        <div className="empty">
          No evidence matches these filters. Try another topic or search term.
        </div>
      )}
      {rows.slice(0, tab === "Overview" ? 3 : rows.length).map((r) => (
        <article key={r.version_id} className="review">
          <div className="review-meta">
            <span className={r.voted_up ? "pill positive" : "pill negative"}>
              {r.voted_up ? "↗ Recommended" : "↘ Not recommended"}
            </span>
            <span>
              {r.period === "before" ? "Before" : "After"} ·{" "}
              {date(r.created_at)} UTC
            </span>
          </div>
          <p>{r.text}</p>
          <div className="review-bottom">
            <div className="tags">
              {r.mentions.map((m) => (
                <button key={m.aspect} onClick={() => selectAspect(m.aspect)}>
                  {m.aspect}
                </button>
              ))}
            </div>
            <button
              className="text-button"
              onClick={() => {
                setFeedbackInput({ text: r.text, revision: Date.now() });
                setTab("Analyze feedback");
              }}
            >
              Analyze this review ↗
            </button>
            <button
              className="text-button"
              aria-expanded={expanded === r.version_id}
              onClick={() =>
                setExpanded(expanded === r.version_id ? "" : r.version_id)
              }
            >
              {" "}
              {expanded === r.version_id
                ? "Hide evidence −"
                : "Inspect evidence +"}{" "}
            </button>
          </div>
          {expanded === r.version_id && (
            <div className="detail">
              <p>
                <strong>Version</strong> <code>{r.version_id}</code>
              </p>
              <p>
                The recommendation comes from the review record. Topic words
                show what is mentioned, but do not establish whether the player
                praises or criticizes it.
              </p>
              {r.mentions.map((m) => (
                <blockquote key={m.aspect}>
                  <strong>{m.aspect}</strong> · raw-text offsets [{m.start},{" "}
                  {m.end})<br />
                  {m.passage}
                </blockquote>
              ))}
              {r.source_url ? (
                <a href={r.source_url} target="_blank" rel="noreferrer">
                  Steam source listing ↗
                </a>
              ) : (
                <p>
                  This is an invented example, not a published Steam review.
                </p>
              )}
            </div>
          )}
        </article>
      ))}
      {tab === "Overview" ? (
        <div className="evidence-preview-footer">
          <p>
            Start with a few examples, then explore the complete collected
            sample.
          </p>
          <button className="secondary" onClick={() => setTab("Reviews")}>
            Browse all {total.toLocaleString()} reviews →
          </button>
        </div>
      ) : (
        <div className="pagination">
          <button
            disabled={offset === 0 || busy}
            onClick={() => setOffset(Math.max(0, offset - 12))}
          >
            ← Previous
          </button>
          <span>
            {total === 0 ? "0" : offset + 1}–{Math.min(offset + 12, total)} of{" "}
            {total}
          </span>
          <button
            disabled={offset + 12 >= total || busy}
            onClick={() => setOffset(offset + 12)}
          >
            Next →
          </button>
        </div>
      )}
    </section>
  );
  return (
    <div className="shell">
      <a className="skip-link" href="#main">
        Skip to main content
      </a>
      <aside>
        <a className="brand" href="#main" aria-label="PatchPulse home">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 28 28" fill="none">
              <path
                d="M3 15h6l3-8 5 15 3-7h5"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          PatchPulse
          <span className="brand-dot">.</span>
        </a>
        <div className="sidebar-label">RELEASE INTELLIGENCE</div>
        <nav aria-label="Main navigation">
          {["Overview", "Reviews", "Analyze feedback", "How it works"].map(
            (item, i) => (
              <button
                key={item}
                className={tab === item ? "active" : ""}
                aria-current={tab === item ? "page" : undefined}
                onClick={() => setTab(item)}
              >
                <svg
                  className="nav-icon"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path
                    d={
                      [
                        "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
                        "M21 21l-5-5 M18 10a8 8 0 1 1-16 0a8 8 0 0 1 16 0",
                        "M9 3h6 M10 3v7L4 20a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1l-6-10V3 M7 15h10",
                        "M3 4h7a2 2 0 0 1 2 2v15a3 3 0 0 0-3-2H3z M21 4h-7a2 2 0 0 0-2 2v15a3 3 0 0 1 3-2h6z",
                      ][i]
                    }
                  />
                </svg>
                {item}
                <span className="nav-index" aria-hidden="true">
                  0{i + 1}
                </span>
              </button>
            ),
          )}
        </nav>
        <div className="sidebar-note">
          <span className="status-dot" /> Local preview
          <p>Evidence before conclusions.</p>
          <small>
            Player feedback analysis.
            <br />
            Not affiliated with Valve or game developers.
          </small>
        </div>
      </aside>
      <main id="main">
        <header>
          <div className="breadcrumbs">
            WORKSPACE <span>/</span> {tab.toUpperCase()}
          </div>
          <div className="header-actions">
            <button
              className="quick-search"
              onClick={() => {
                setTab("Reviews");
                setFocusSearch(true);
              }}
            >
              Search evidence <kbd>/</kbd>
            </button>
            <span className="build-tag">
              PROTOTYPE <span>01</span>
            </span>
          </div>
        </header>
        {error && (
          <div className="error" role="alert">
            {error}
            <button onClick={() => window.location.reload()}>Retry</button>
          </div>
        )}
        {!data && !error && <p role="status">Loading the case study…</p>}
        {data && (
          <>
            <div className="mode-banner">
              <span className="status-dot" />
              <strong>
                {data.mode === "synthetic"
                  ? "SYNTHETIC DEMO"
                  : "PRIVATE REAL-DATA STUDY"}
              </strong>
              <span>
                {data.mode === "synthetic"
                  ? "These invented reviews show how the app works. They are not findings about the game."
                  : "Reviews were collected after the update for a local study. Source text and trained models stay private."}
              </span>
            </div>
            <div className="hero">
              <div>
                <span className="eyebrow">PLAYER FEEDBACK, IN CONTEXT</span>
                <h1>
                  {tab === "Overview" ? (
                    <>
                      Find the signal.
                      <br />
                      <span className="hero-accent">Follow the evidence.</span>
                    </>
                  ) : tab === "Reviews" ? (
                    "Follow the evidence."
                  ) : tab === "Analyze feedback" ? (
                    "Test the text, not your assumptions."
                  ) : (
                    "Make the method inspectable."
                  )}
                </h1>
                <p>
                  {tab === "Overview"
                    ? "Compare recommendations before and after an update, explore review topics, and read the comments behind the numbers."
                    : tab === "Reviews"
                      ? "Filter the collected reviews by time, topic, or recommendation. Open a review to inspect its supporting passages."
                      : tab === "Analyze feedback"
                        ? "Paste a review to explore what it praises or criticizes. You can also try a separate model that predicts the overall recommendation."
                        : "See where the data comes from, how the models were tested, and what the results can—and cannot—tell you."}
                </p>
              </div>
              <button
                className="primary"
                onClick={
                  tab === "Overview"
                    ? () => {
                        setTab("Reviews");
                      }
                    : exportBrief
                }
              >
                {tab === "Overview"
                  ? "Browse reviews ↗"
                  : "Export release brief ↓"}
              </button>
            </div>
            <div className="case-bar">
              <div className="game-glyph" aria-hidden="true">
                DRG
              </div>
              <div>
                <h2>{data.game.name}</h2>
                <p>
                  {data.game.title} <span>· {data.game.date}</span>
                </p>
                <p className="case-context">
                  {(
                    data.periods.before.count + data.periods.after.count
                  ).toLocaleString()}{" "}
                  eligible{" "}
                  {data.mode === "synthetic"
                    ? "synthetic examples"
                    : "collected reviews"}{" "}
                  · snapshot {data.snapshot_date}
                </p>
              </div>
              <a href={data.game.source_url} target="_blank" rel="noreferrer">
                Official update ↗
              </a>
            </div>
            {tab === "Overview" && (
              <>
                <div className="section-label">
                  <h2>Recorded recommendations</h2>
                  <span>
                    Observed labels ·{" "}
                    {data.mode === "synthetic"
                      ? "invented demo data"
                      : "eligible collected sample"}
                  </span>
                </div>
                <div className="stats-grid">
                  {["before", "after"].map((p) => (
                    <section className="stat-card" key={p}>
                      <span className="eyebrow">
                        {p === "before"
                          ? "01 / BEFORE UPDATE"
                          : "02 / AFTER UPDATE"}
                      </span>
                      <strong>{pct(data.periods[p].rate)}</strong>
                      <p>
                        {data.periods[p].positive} recommended /{" "}
                        {data.periods[p].count} eligible reviews
                      </p>
                      <div
                        className="rate-track"
                        role="img"
                        aria-label={`${p}: ${pct(data.periods[p].rate)} recommended`}
                      >
                        <span
                          style={{
                            width: `${(data.periods[p].rate || 0) * 100}%`,
                          }}
                        />
                      </div>
                      <small>
                        {date(data.periods[p].start)} →{" "}
                        {date(data.periods[p].end)} exclusive · UTC
                      </small>
                      <span className="coverage">
                        {data.periods[p].coverage.status.replaceAll("_", " ")}
                      </span>
                    </section>
                  ))}
                  <section className="stat-card change">
                    <span className="eyebrow">03 / OBSERVED DIFFERENCE</span>
                    <strong>
                      {data.change_pp === null
                        ? "—"
                        : `${data.change_pp >= 0 ? "+" : ""}${data.change_pp.toFixed(1)}`}
                      <em> pp</em>
                    </strong>
                    <p>Percentage points, after minus before</p>
                    <div className="change-note">
                      A change in the collected reviews.
                      <br />
                      No claim of patch causation.
                    </div>
                    <small>Snapshot · {data.snapshot_date}</small>
                  </section>
                </div>
                <section className="window-map" aria-label="Comparison windows">
                  <div className="window-map-title">
                    <span className="eyebrow">THE COMPARISON FRAME</span>
                    <span className="map-qualification">
                      Equal windows · release day omitted · UTC
                    </span>
                  </div>
                  <div className="window-map-track">
                    <div className="window-segment before-segment">
                      <span>BEFORE</span>
                      <div className="calendar-cells" aria-hidden="true">
                        {Array.from({ length: 14 }, (_, i) => (
                          <i key={i} />
                        ))}
                      </div>
                      <small>
                        {date(data.periods.before.start)} —{" "}
                        {date(data.periods.before.end)} exclusive
                      </small>
                    </div>
                    <div className="release-marker">
                      <span className="release-diamond" aria-hidden="true" />
                      <strong>UPDATE</strong>
                      <span>{data.game.date}</span>
                    </div>
                    <div className="window-segment after-segment">
                      <span>AFTER</span>
                      <div className="calendar-cells" aria-hidden="true">
                        {Array.from({ length: 14 }, (_, i) => (
                          <i key={i} />
                        ))}
                      </div>
                      <small>
                        {date(data.periods.after.start)} —{" "}
                        {date(data.periods.after.end)} exclusive
                      </small>
                    </div>
                  </div>
                </section>
                <div className="analysis-grid">
                  <section className="panel">
                    <div className="panel-heading">
                      <div>
                        <span className="eyebrow">EXPLORATORY SIGNALS</span>
                        <h2>What gets mentioned?</h2>
                      </div>
                      <div
                        className="segmented"
                        role="group"
                        aria-label="Aspect display"
                      >
                        <button
                          aria-pressed={aspectView === "counts"}
                          onClick={() => setAspectView("counts")}
                        >
                          Counts
                        </button>
                        <button
                          aria-pressed={aspectView === "share"}
                          onClick={() => setAspectView("share")}
                        >
                          Share
                        </button>
                      </div>
                    </div>
                    <p className="muted">
                      Counts of reviews mentioning each topic. These are not
                      complaint counts. A mention alone does not tell us whether
                      the player is praising or criticizing the topic.
                    </p>
                    <div className="legend">
                      <span className="before-key" /> Before{" "}
                      <span className="after-key" /> After
                    </div>
                    <div className="plot-axis">
                      {aspectView === "counts"
                        ? "Review mentions · common count scale"
                        : "Share of eligible reviews · 0–100% scale"}
                      <span>BEFORE / AFTER</span>
                    </div>
                    {data.mentions
                      .filter((m) => m.before + m.after > 0)
                      .map((m) => (
                        <button
                          className="aspect-row"
                          key={m.aspect}
                          onClick={() => selectAspect(m.aspect)}
                          aria-label={`Inspect ${m.aspect} evidence`}
                        >
                          <span>{m.aspect}</span>
                          <div className="aspect-tracks">
                            <span
                              style={{
                                width: `${(100 * m.before) / (aspectView === "share" ? Math.max(data.periods.before.count, 1) : Math.max(...data.mentions.flatMap((v) => [v.before, v.after]), 1))}%`,
                              }}
                            />
                            <span
                              style={{
                                width: `${(100 * m.after) / (aspectView === "share" ? Math.max(data.periods.after.count, 1) : Math.max(...data.mentions.flatMap((v) => [v.before, v.after]), 1))}%`,
                              }}
                            />
                          </div>
                          <span className="aspect-count">
                            {aspectView === "counts"
                              ? `${m.before} / ${m.after}`
                              : `${((100 * m.before) / Math.max(data.periods.before.count, 1)).toFixed(1)}% / ${((100 * m.after) / Math.max(data.periods.after.count, 1)).toFixed(1)}%`}{" "}
                            <span aria-hidden="true">↗</span>
                          </span>
                        </button>
                      ))}
                  </section>
                  <section className="panel field-notes">
                    <span className="eyebrow">READ THIS WITH THE CHARTS</span>
                    <h2>Context is part of the result.</h2>
                    <div className="note">
                      <span>01</span>
                      <div>
                        <h3>A retrospective snapshot</h3>
                        <p>
                          Current text is eligible only when created in its
                          window and last edited before the cutoff.
                        </p>
                      </div>
                    </div>
                    <div className="note">
                      <span>02</span>
                      <div>
                        <h3>Coverage stays visible</h3>
                        <p>
                          {Object.values(data.periods).some(
                            (p) => p.coverage.status === "capped_incomplete",
                          )
                            ? "At least one collection cap was reached. Windows are incomplete and may overrepresent later dates."
                            : data.mode === "real"
                              ? "Pagination exhausted both windows. A one-record mismatch with the after-window source total remains unresolved."
                              : "These invented examples demonstrate collection states; they do not represent the player population."}
                        </p>
                      </div>
                    </div>
                    <div className="note">
                      <span>03</span>
                      <div>
                        <h3>Mentions are not sentiment</h3>
                        <p>
                          A player can recommend a game while criticizing
                          multiplayer. A topic word alone does not tell us
                          whether the feedback is positive or negative.
                        </p>
                      </div>
                    </div>
                    <div className="excluded">
                      <strong>
                        {Object.values(data.exclusions).reduce(
                          (a, b) => a + b,
                          0,
                        )}
                      </strong>
                      <span>reviews excluded by eligibility rules</span>
                    </div>
                    <button className="text-button" onClick={exportBrief}>
                      Export evidence-linked brief ↓
                    </button>
                  </section>
                </div>
                {evidencePanel}
              </>
            )}
            {tab === "Reviews" && evidencePanel}
            {tab === "Analyze feedback" && (
              <>
                <AspectLab input={feedbackInput} />
                <section className="panel lab">
                  <span className="eyebrow">
                    TEXT-ONLY RECOMMENDATION PREDICTION
                  </span>
                  <h2>Would this player recommend the game?</h2>
                  <p>
                    This separate experiment estimates the overall
                    recommendation from the review text. It does not replace a
                    known recommendation or the topic-level analysis above.
                  </p>
                  <p>
                    {models.find((m) => m.id === modelId)?.description ??
                      evaluation?.model_description ??
                      "TF-IDF + logistic regression"}
                    .{" "}
                    {data.mode === "synthetic"
                      ? "Trained on invented examples for this demo; accuracy on real reviews has not been established."
                      : "An experimental model tested on development data, not the final test set."}{" "}
                    User input stays local and is not stored.
                  </p>
                  <details className="annotation-guide">
                    <summary>What do the model names mean?</summary>
                    <p>
                      TF-IDF measures how distinctive words or character
                      fragments are in the training reviews. Logistic regression
                      learns how those features relate to a recommendation.
                      Balanced training gives the less common recommendation
                      class more weight. The exact model configuration and
                      evaluation are available in How it works.
                    </p>
                  </details>
                  <label htmlFor="model-choice">Detector</label>
                  <select
                    id="model-choice"
                    value={modelId}
                    onChange={(e) => {
                      setModelId(e.target.value);
                      setPrediction(null);
                    }}
                  >
                    {models.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.description} · negative threshold{" "}
                        {m.negative_threshold}
                      </option>
                    ))}
                  </select>
                  <p className="muted">
                    The threshold is the score at which a model labels a review
                    not recommended. A lower threshold can catch more negative
                    reviews and produce more false alarms. The scores are not
                    verified probabilities of correctness; they are
                    uncalibrated.
                  </p>
                  <label htmlFor="example">Review text</label>
                  <textarea
                    id="example"
                    value={text}
                    maxLength={8000}
                    onChange={(e) => {
                      setText(e.target.value);
                      setPrediction(null);
                    }}
                    rows={5}
                  />
                  <div className="lab-actions">
                    <span>{text.length} / 8,000 characters</span>
                    <button
                      className="primary"
                      disabled={!text.trim() || predicting}
                      onClick={predict}
                    >
                      {predicting ? "Predicting…" : "Predict recommendation ↗"}
                    </button>
                  </div>
                  {predictError && <p role="alert">{predictError}</p>}
                  {prediction && (
                    <div className="prediction" role="status">
                      <span className="eyebrow">
                        {prediction.abstention_reason
                          ? "ABSTAINED"
                          : "MODEL OUTPUT"}
                      </span>
                      <h3>
                        {prediction.prediction ?? prediction.abstention_reason}
                      </h3>
                      {prediction.score_recommended !== null && (
                        <p>
                          Recommended-class score:{" "}
                          {prediction.score_recommended.toFixed(3)} ·
                          uncalibrated. This score describes the overall
                          recommendation, not praise or complaints about
                          individual topics.
                          <br />
                          Not-recommended score:{" "}
                          {prediction.score_not_recommended?.toFixed(3)} ·
                          decision threshold: {prediction.negative_threshold}.
                          <br />
                          Model: {prediction.model_id}
                        </p>
                      )}
                    </div>
                  )}
                </section>
              </>
            )}
            {tab === "How it works" && (
              <>
                <section className="panel methodology">
                  <span className="eyebrow">READING THE RESULTS</span>
                  <h2>What is counted, and what is predicted?</h2>
                  <p>
                    <strong>Recorded recommendations</strong> are the
                    recommendation labels already attached to the collected
                    reviews. The overview counts those labels directly.
                  </p>
                  <p>
                    <strong>Suggested topic sentiment</strong> means praise or
                    criticism about one part of a game, such as multiplayer.
                    These suggestions are experimental and need checking against
                    the quoted text.
                  </p>
                  <p>
                    <strong>Development results</strong> come from reviews used
                    to compare models. They help guide the next experiment; they
                    do not establish final accuracy on future reviews or another
                    game.
                  </p>
                  <p>
                    In the tables below, <strong>precision</strong> measures how
                    often a negative prediction is correct;{" "}
                    <strong>recall</strong> measures how many negative reviews
                    are found. <strong>Macro F1</strong> balances precision and
                    recall and gives each recommendation class equal weight.
                    Higher is better, up to 1.
                  </p>
                </section>
                <NeuralPanel />
                <ResearchPanel />
                <section className="panel methodology">
                  <span className="eyebrow">DEVELOPMENT EVALUATION</span>
                  <h2>Show the work. Keep the limits.</h2>
                  <p>
                    {evaluation?.status ?? "Evaluation not available"}.{" "}
                    {data.mode === "synthetic"
                      ? "Metrics in this panel measure synthetic workflow behavior only."
                      : ""}
                  </p>
                  {evaluation?.macro_f1 !== undefined && (
                    <>
                      <div className="evaluation-grid">
                        <div>
                          <strong>{evaluation.macro_f1.toFixed(3)}</strong>
                          <span>Validation macro F1</span>
                        </div>
                        <div>
                          <strong>
                            {evaluation.majority_macro_f1?.toFixed(3)}
                          </strong>
                          <span>Majority baseline macro F1</span>
                        </div>
                        <div>
                          <strong>{evaluation.counts?.validation}</strong>
                          <span>Validation records</span>
                        </div>
                      </div>
                      <h3>Validation confusion matrix</h3>
                      <p>
                        Rows: actual; columns: predicted. Order: not
                        recommended, recommended.
                      </p>
                      <table>
                        <thead>
                          <tr>
                            <th>Actual / predicted</th>
                            <th>Not recommended</th>
                            <th>Recommended</th>
                          </tr>
                        </thead>
                        <tbody>
                          {evaluation.confusion_matrix?.map((r, i) => (
                            <tr key={i}>
                              <th>
                                {i === 0 ? "Not recommended" : "Recommended"}
                              </th>
                              {r.map((v, j) => (
                                <td key={j}>{v}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </>
                  )}
                  <h3>Evaluation status</h3>
                  <p>
                    Chronological train/validation/temporal-test partitions are
                    frozen before fitting. Exact and near duplicates are removed
                    before splitting. Final temporal tests remain unopened. The
                    unseen-game test and human aspect evaluation are pending.
                    Real-data development uncertainty appears in the comparison
                    above.
                  </p>
                  <h3>Help review the training labels</h3>
                  <p>
                    Review training examples without seeing source
                    recommendations or model suggestions. Select topic passages
                    and label their sentiment, then export your reviewed
                    examples for validation.
                  </p>
                  <a className="secondary annotation-link" href="/annotate">
                    Open{" "}
                    {data.mode === "synthetic"
                      ? "synthetic practice"
                      : "private training"}{" "}
                    annotation workspace →
                  </a>
                  <h3>Collection and provenance</h3>
                  <p>
                    Equal 14-day UTC windows omit the release date because
                    deployment time is not verified. Source requests use Recent
                    ordering, both recommendation classes, all purchase types,
                    and Steam's off-topic filter. Each period receives its own
                    cap. Immutable text versions and private HMAC author groups
                    support provenance audits.
                  </p>
                  <h3>Known limitations</h3>
                  {data.limitations.map((x) => (
                    <p key={x}>{x}</p>
                  ))}
                  <p>
                    Wilson intervals describe sampling variability under
                    binomial assumptions; they cannot establish
                    representativeness. Public release excludes source review
                    text, identifiers, and trained artifacts until the
                    applicable permissions are established.
                  </p>
                  <p>
                    <a
                      href="https://partner.steamgames.com/doc/webapi/IUserReviewsService"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Official review API
                    </a>{" "}
                    ·{" "}
                    <a
                      href="https://steamcommunity.com/dev/apiterms"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Source terms
                    </a>
                  </p>
                </section>
              </>
            )}
            <footer>
              <span>PATCHPULSE · EVIDENCE BEFORE CONCLUSIONS</span>
              <span>
                Local prototype ·{" "}
                {data.mode === "synthetic"
                  ? "invented demo data"
                  : "private source data"}
              </span>
            </footer>
          </>
        )}
      </main>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {window.location.pathname === "/annotate" ? <AnnotationApp /> : <App />}
  </React.StrictMode>,
);
