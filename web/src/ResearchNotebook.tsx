import React from "react";

export type ResearchNote = {
  id: string;
  text: string;
  topic: string;
  label: string;
  source: string;
  method?: string;
  annotation: string;
  nextStep?: string;
};
export type NoteDraft = Omit<ResearchNote, "id" | "annotation">;

export function ResearchNotebook({
  notes,
  onRemove,
  onEdit,
  onNextStep,
  onBrowse,
  onBrief,
}: {
  notes: ResearchNote[];
  onRemove: (id: string) => void;
  onEdit: (id: string, text: string) => void;
  onNextStep: (id: string, text: string) => void;
  onBrowse: () => void;
  onBrief: () => void;
}) {
  function download() {
    const content = [
      "PatchPulse · Research notebook",
      "Session notes, not validated findings. May contain private source text. Review before sharing.",
      ...notes.map(
        (n, i) =>
          `\n${i + 1}. ${n.topic} · ${n.label}\nSource: ${n.source}${n.method ? `\nMethod: ${n.method}` : ""}\nPassage:\n${n.text}\nResearcher's note: ${n.annotation || "No interpretation added."}\nNext investigation: ${n.nextStep || "Not yet decided."}`,
      ),
    ].join("\n");
    const url = URL.createObjectURL(
      new Blob([content], { type: "text/plain;charset=utf-8" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "patchpulse-research-notebook.txt";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <section className="notebook-workspace" aria-labelledby="notebook-title">
      <div className="desk-title">
        <div>
          <span className="eyebrow">YOUR RESEARCH TRAIL</span>
          <h1 id="notebook-title">Evidence for the next decision.</h1>
          <p>
            Keep useful evidence together. Add your interpretation before
            drawing a conclusion. Record a concrete next check: reproduce the issue, compare earlier reviews, or gather more evidence.
          </p>
        </div>
        <button className="primary" disabled={!notes.length} onClick={download}>
          Export notebook ↓
        </button>
      </div>
      <div className="notebook-privacy">
        <strong>Session only</strong> Nothing is uploaded or saved
        automatically. Refreshing or leaving the app clears this notebook.
        Exports may contain private review text.
      </div>
      {!notes.length ? (
        <div className="notebook-empty">
          <div className="paper-stack" aria-hidden="true">
            <span>01</span>
            <i />
            <i />
          </div>
          <h2>Build a brief from the source.</h2>
          <p>
            Save a review from the explorer or a suggested passage from an
            analysis. Its source and label stay attached.
          </p>
          <button className="primary" onClick={onBrowse}>
            Find a review to investigate →
          </button>
        </div>
      ) : (
        <div className="note-grid">
          {notes.map((n, i) => (
            <article className="research-note" key={n.id}>
              <div className="note-topline">
                <span>NOTE {String(i + 1).padStart(2, "0")}</span>
                <button
                  className="text-button"
                  onClick={() => onRemove(n.id)}
                  aria-label={`Remove note ${i + 1}`}
                >
                  Remove ×
                </button>
              </div>
              <h2>{n.topic}</h2>
              <span className="small-tag">{n.label}</span>
              <blockquote>{n.text}</blockquote>
              <p className="note-source">
                {n.source}
                {n.method && (
                  <>
                    <br />
                    {n.method}
                  </>
                )}
              </p>
              <label>
                Your interpretation
                <textarea
                  rows={3}
                  value={n.annotation}
                  onChange={(e) => onEdit(n.id, e.target.value)}
                  placeholder="What does this passage support—and what is still uncertain?"
                />
              </label>
              <label className="next-investigation">Next investigation
                <input value={n.nextStep || ""} onChange={e => onNextStep(n.id, e.target.value)} placeholder="e.g. Reproduce disconnects with a four-player lobby" />
              </label>
            </article>
          ))}
        </div>
      )}
      <div className="notebook-footnote">
        <div>
          <h3>Need the sample statistics too?</h3>
          <p>
            The data brief contains recorded recommendation counts, evidence
            references and limitations. It does not turn these notes into
            verified complaint trends.
          </p>
        </div>
        <button className="secondary" onClick={onBrief}>
          Export release brief ↓
        </button>
      </div>
    </section>
  );
}
