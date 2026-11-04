import React, { useState } from "react";
import { NlpSnapshot } from "./NlpSnapshot";

type Study = {
  mode: string;
  game: { name: string; title: string; date: string; source_url: string };
  snapshot_date: string;
  change_pp: number | null;
  periods: Record<
    string,
    {
      count: number;
      positive: number;
      negative: number;
      rate: number | null;
      start: number;
      end: number;
      coverage: { status: string };
    }
  >;
  mentions: { aspect: string; before: number; after: number }[];
};
const percent = (n: number | null) =>
  n === null ? "—" : `${(n * 100).toFixed(1)}%`;
const icons: Record<string, string> = {
  Performance: "↯",
  Stability: "◈",
  Multiplayer: "◎",
  Gameplay: "✦",
  Interface: "⊞",
  Accessibility: "◉",
  Value: "◇",
  Progression: "↗",
};
export function UpdateDesk({
  study,
  notesCount,
  onInspect,
  onBrowse,
  onComplaints,
  onImport,
  onMethods,
  onAnalyze,
  onNotebook,
  onBrief,
}: {
  study: Study;
  notesCount: number;
  onInspect: (topic: string, period?: "after") => void;
  onBrowse: (negative?: boolean) => void;
  onComplaints: () => void;
  onImport: () => void;
  onMethods: () => void;
  onAnalyze: () => void;
  onNotebook: () => void;
  onBrief: () => void;
}) {
  const [scale, setScale] = useState("share");
  const [sort, setSort] = useState("change");
  const before = study.periods.before,
    after = study.periods.after;
  const share = (n: number, total: number) => (total ? (n / total) * 100 : 0);
  const topics = study.mentions
    .filter((t) => t.before + t.after > 0)
    .map((t) => ({
      ...t,
      delta:
        before.count && after.count
          ? share(t.after, after.count) - share(t.before, before.count)
          : null,
    }))
    .sort((a, b) =>
      sort === "change"
        ? Math.abs(b.delta ?? 0) - Math.abs(a.delta ?? 0) ||
          a.aspect.localeCompare(b.aspect)
        : b.before + b.after - a.before - a.after ||
          a.aspect.localeCompare(b.aspect),
    );
  const countMax = Math.max(1, ...topics.flatMap((t) => [t.before, t.after]));
  const mostDiscussed = [...topics].filter((t) => t.after > 0).sort((a, b) => b.after - a.after || a.aspect.localeCompare(b.aspect))[0];
  const biggestShift = [...topics].filter((t) => t.delta !== null).sort((a, b) => Math.abs(b.delta ?? 0) - Math.abs(a.delta ?? 0) || a.aspect.localeCompare(b.aspect))[0];
  const tiedMost = mostDiscussed && topics.filter((t) => t.after === mostDiscussed.after).length > 1;
  const tiedShift = biggestShift && topics.filter((t) => t.delta !== null && Math.abs(Math.abs(t.delta) - Math.abs(biggestShift.delta!)) < 1e-9).length > 1;
  return (
    <div className="update-desk">
      <section className="release-story">
        <div className="release-narrative">
          <div className="story-kicker">
            <span className="tiny-orbit" />
            FEEDBACK WORKSPACE <span>{study.mode === "synthetic" ? "EXAMPLE COLLECTION" : "LOCAL STUDY"}</span>
          </div>
          <h1>
            Player feedback. {" "}
            <em>Investigation desk.</em>
          </h1>
          <p>
            Bring your own player reviews to find potential complaints, or explore
            the example below to see how feedback changed around an update.
          </p>
          <div className="story-actions">
            <button className="primary" onClick={onImport}>Import your reviews →</button>
            <button className="secondary" onClick={onComplaints}>Find potential complaints</button>
            <button className="text-button" onClick={() => onBrowse()}>
              Browse reviews ↗
            </button>
            <button className="text-button" onClick={onAnalyze}>
              Analyze a review →
            </button>
          </div>
          <div className="release-caption">
            <strong>{study.game.title}</strong>
            <span>
              Released {study.game.date} · snapshot {study.snapshot_date}
            </span>
          </div>
        </div>
        <div className="release-pulse">
          <div className="pulse-heading">
            <span>{study.mode === "synthetic" ? "EXAMPLE · " : "STUDY · "}RECORDED RECOMMENDATIONS</span>
            <span className="small-tag">Observed labels</span>
          </div>
          <div className="comparison-readout">
            <strong>{study.change_pp === null ? "—" : `${study.change_pp >= 0 ? "+" : ""}${study.change_pp.toFixed(1)}`}<small> pp</small></strong>
            <span>Recommendation rate change · after minus before</span>
          </div>
          <div className="rate-comparison" role="img" aria-label={`Before ${percent(before.rate)} recommended; after ${percent(after.rate)} recommended. Both bars use a zero to 100 percent scale.`}>
            {[before, after].map((period, index) => <div className="rate-row" key={index}><span>{index ? "After" : "Before"}</span><div className="rate-track"><i style={{width: `${(period.rate ?? 0) * 100}%`}} /></div><b>{percent(period.rate)}</b></div>)}
            <div className="rate-axis"><span>0%</span><span>100%</span></div>
          </div>
          <div className="pulse-periods">
            <div>
              <span>Before update</span>
              <strong>{percent(before.rate)}</strong>
              <small>
                {before.positive} / {before.count} reviews
              </small>
            </div>
            <div>
              <span>After update</span>
              <strong>{percent(after.rate)}</strong>
              <small>
                {after.positive} / {after.count} reviews
              </small>
            </div>
          </div>
          <p className="pulse-caution">
            A sample comparison, not proof that the update caused a change.
          </p>
        </div>
      </section>
      <section className="signal-strip" aria-labelledby="signal-title">
        <div className="signal-intro"><span className="eyebrow">{study.mode === "synthetic" ? "EXAMPLE COLLECTION" : "LOCAL STUDY"} / QUICK SIGNALS</span><h2 id="signal-title">Where to look next.</h2><p>Topic mentions are not confirmed complaints.</p></div>
        <div className="signal-stat"><span>REVIEWS IN BOTH WINDOWS</span><strong>{(before.count + after.count).toLocaleString()}</strong><small>{before.count.toLocaleString()} before · {after.count.toLocaleString()} after</small></div>
        {mostDiscussed && after.count > 0 && <button className="signal-stat signal-link" onClick={() => onInspect(mostDiscussed.aspect, "after")}><span>{tiedMost ? "TIED MOST MENTIONED AFTER" : "MOST MENTIONED AFTER"}</span><strong>{mostDiscussed.aspect} <i>↗</i></strong><small>{mostDiscussed.after.toLocaleString()} of {after.count.toLocaleString()} reviews · {share(mostDiscussed.after, after.count).toFixed(1)}%</small></button>}
        {biggestShift && <button className="signal-stat signal-link" onClick={() => onInspect(biggestShift.aspect)}><span>{biggestShift.delta === 0 ? "TOPIC SHARE CHANGE" : tiedShift ? "TIED BIGGEST SHARE CHANGE" : "BIGGEST SHARE CHANGE"}</span><strong>{biggestShift.delta! >= 0 ? "+" : ""}{biggestShift.delta!.toFixed(1)} <i>pp</i></strong><small>{biggestShift.aspect}: {biggestShift.before}/{before.count} before · {biggestShift.after}/{after.count} after ↗</small></button>}
      </section>
      <NlpSnapshot onMethods={onMethods} onAnalyze={onAnalyze} />
      <section className="desk-breadcrumbs" aria-label="Comparison windows">
        <details className="study-picker">
          <summary>
            <strong>Study boundaries</strong>
            <span>14 days on each side · release day omitted · UTC</span>
          </summary>
          <div className="study-picker-note">
            <p>
              This workspace currently contains one game update. Before:{" "}
              {new Date(before.start * 1000).toISOString().slice(0, 10)} to{" "}
              {new Date(before.end * 1000).toISOString().slice(0, 10)}{" "}
              exclusive. After:{" "}
              {new Date(after.start * 1000).toISOString().slice(0, 10)} to{" "}
              {new Date(after.end * 1000).toISOString().slice(0, 10)} exclusive.
            </p>
            <p>
              Coverage: before {before.coverage.status.replaceAll("_", " ")};
              after {after.coverage.status.replaceAll("_", " ")}. Source
              versions and eligibility exclusions remain in the data brief.
            </p>
            <a href={study.game.source_url} target="_blank" rel="noreferrer">
              Official update ↗
            </a>
          </div>
        </details>
        <button className="text-button" onClick={onBrief}>
          Export release brief ↓
        </button>
      </section>
      <div className="desk-investigation">
        <section className="topic-board" aria-labelledby="topic-title">
          <div className="topic-board-heading">
            <div>
              <span className="eyebrow">CHOOSE A THREAD TO FOLLOW</span>
              <h2 id="topic-title">What moved in player feedback?</h2>
            </div>
            <label className="sort-topics">
              Sort topics
              <select value={sort} onChange={(e) => setSort(e.target.value)}>
                <option value="change">Biggest share change</option>
                <option value="volume">Most mentions</option>
              </select>
            </label>
          </div>
          <p>
            Topic mentions show what gets discussed. They do not tell us whether
            it is praised or criticized.
          </p>
          <div className="board-controls">
            <div className="segmented" role="group" aria-label="Aspect display">
              <button
                aria-pressed={scale === "counts"}
                onClick={() => setScale("counts")}
              >
                Counts
              </button>
              <button
                aria-pressed={scale === "share"}
                onClick={() => setScale("share")}
              >
                Share
              </button>
            </div>
            <span>
              {scale === "share"
                ? "Share of eligible reviews · 0–100% scale"
                : "Review mentions · common count scale"}
            </span>
          </div>
          <div className="conversation-grid">
            {topics.map((t) => (
              <button
                className="conversation-tile"
                key={t.aspect}
                aria-label={`Inspect ${t.aspect} evidence`}
                onClick={() => onInspect(t.aspect)}
              >
                <div className="tile-title">
                  <span className="topic-symbol" aria-hidden="true">
                    {icons[t.aspect] ?? "◌"}
                  </span>
                  <strong>{t.aspect}</strong>
                  <span aria-hidden="true">↗</span>
                </div>
                <div className="tile-change">
                  {t.delta === null
                    ? "Insufficient data"
                    : `${t.delta >= 0 ? "+" : ""}${t.delta.toFixed(1)} pp`}
                  <small>change in mention share</small>
                </div>
                <div className="tile-period">
                  <span>Before</span>
                  <i
                    style={{
                      width: `${scale === "share" ? share(t.before, before.count) : (t.before / countMax) * 100}%`,
                    }}
                  />
                  <b>
                    {scale === "share"
                      ? `${share(t.before, before.count).toFixed(1)}%`
                      : t.before}
                  </b>
                </div>
                <div className="tile-period after">
                  <span>After</span>
                  <i
                    style={{
                      width: `${scale === "share" ? share(t.after, after.count) : (t.after / countMax) * 100}%`,
                    }}
                  />
                  <b>
                    {scale === "share"
                      ? `${share(t.after, after.count).toFixed(1)}%`
                      : t.after}
                  </b>
                </div>
                <span className="tile-footer">
                  Open matching reviews <span>→</span>
                </span>
              </button>
            ))}
          </div>
        </section>
        <aside className="research-next">
          <div className="next-card coral-card">
            <span className="eyebrow">LOOK BEYOND THE THUMBS-UP</span>
            <h2>
              One review. {" "}
              <br />
              More than one opinion.
            </h2>
            <blockquote>
              “Great missions, but our co-op sessions keep disconnecting.”
            </blockquote>
            <span className="example-caption">Invented example</span>
            <button className="primary" onClick={onAnalyze}>
              Explore praise & complaints →
            </button>
          </div>
          <div className="next-card trail-card">
            <span className="eyebrow">YOUR EVIDENCE STACK</span>
            <h2>
              {notesCount
                ? `${notesCount} saved ${notesCount === 1 ? "passage" : "passages"}`
                : "Build the next-patch brief."}
            </h2>
            <p>
              Save reviews and passages to your session notebook. Add your
              interpretation and export the evidence together.
            </p>
            <button className="text-button" onClick={onNotebook}>
              Open notebook →
            </button>
          </div>
          <button className="concern-shortcut" onClick={() => onBrowse(true)}>
            <span>Read the other side</span>
            <strong>
              {after.negative} not-recommended{" "}
              {after.negative === 1 ? "review" : "reviews"} after the update ↗
            </strong>
            <small>Recommendation labels, not confirmed complaints.</small>
          </button>
        </aside>
      </div>
    </div>
  );
}
