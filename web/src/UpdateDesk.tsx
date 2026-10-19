import React, { useState } from "react";

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
  onAnalyze,
  onNotebook,
  onBrief,
}: {
  study: Study;
  notesCount: number;
  onInspect: (topic: string) => void;
  onBrowse: (negative?: boolean) => void;
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
  return (
    <div className="update-desk">
      <section className="release-story">
        <div className="release-narrative">
          <div className="story-kicker">
            <span className="tiny-orbit" />
            RELEASE WORKSPACE <span>01 / DEEP ROCK GALACTIC</span>
          </div>
          <h1>
            After the patch.
            <br />
            <em>Before the next one.</em>
          </h1>
          <p>
            Find what changed in the review sample. Follow a topic into the
            actual comments. Keep the evidence worth coming back to.
          </p>
          <div className="story-actions">
            <button className="primary" onClick={() => onBrowse()}>
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
            <span>RECORDED RECOMMENDATIONS</span>
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
              One review.
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
