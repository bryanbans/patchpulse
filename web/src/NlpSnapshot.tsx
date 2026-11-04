import React, { useEffect, useState } from "react";

type RecommendationReport = {
  counts: { validation: number };
  validation_class_support: { recommended: number; not_recommended: number };
  selected_id: string;
  candidates: { id: string; confusion_matrix: number[][] }[];
};

export function NlpSnapshot({ onMethods, onAnalyze }: { onMethods: () => void; onAnalyze: () => void }) {
  const [report, setReport] = useState<RecommendationReport | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "unavailable">("loading");

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/research-evaluation", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("Report unavailable");
        return response.json();
      })
      .then((data: RecommendationReport) => { setReport(data); setStatus("ready"); })
      .catch(() => { if (!controller.signal.aborted) setStatus("unavailable"); });
    return () => controller.abort();
  }, []);

  const baseline = report?.candidates.find((candidate) => candidate.id === "word-default-v1");
  const selected = report?.candidates.find((candidate) => candidate.id === report.selected_id);
  const support = report?.validation_class_support;
  const hasResults = baseline?.confusion_matrix?.[0]?.[0] !== undefined &&
    selected?.confusion_matrix?.[0]?.[0] !== undefined && selected?.confusion_matrix?.[1]?.[0] !== undefined && support;

  return <section className="nlp-snapshot" aria-labelledby="nlp-snapshot-title">
    <div className="nlp-snapshot-intro">
      <span className="eyebrow">NATURAL LANGUAGE PROCESSING / RESEARCH</span>
      <h2 id="nlp-snapshot-title">Understand the words. Test the method.</h2>
      <p>PatchPulse examines feedback at two levels: topic-specific praise and complaints in a passage, and the prediction of an entire review's recommendation.</p>
      <div className="nlp-snapshot-actions">
        <button className="primary" onClick={onAnalyze}>Analyze a review →</button>
        <button className="secondary" onClick={onMethods}>Explore methods &amp; evaluation ↗</button>
      </div>
    </div>
    <div className="nlp-snapshot-evidence">
      <span className="eyebrow">RECOMMENDATION PREDICTION / DEVELOPMENT STUDY</span>
      <h3>How does the model handle rare negative reviews?</h3>
      {status === "loading" && <p role="status">Loading research results…</p>}
      {(status === "unavailable" || (status === "ready" && !hasResults)) && <p role="status">Research results are unavailable. Explore the methods for more context.</p>}
      {hasResults && report && baseline && selected && support && <>
        <div className="nlp-compare" aria-label="Not-recommended reviews detected in development validation">
          <div><span>Word baseline</span><strong>{baseline.confusion_matrix[0][0]}<small> / {support.not_recommended}</small></strong><span>not-recommended detected</span></div>
          <div><span>Selected model</span><strong>{selected.confusion_matrix[0][0]}<small> / {support.not_recommended}</small></strong><span>not-recommended detected</span></div>
          <div><span>False alarms</span><strong>{selected.confusion_matrix[1][0]}</strong><span>recommended reviews flagged</span></div>
        </div>
        <p className="nlp-snapshot-note">Private study, {report.counts.validation} validation reviews ({support.not_recommended} not recommended). Development selection and a small minority class limit generalization. This measures whole-review recommendations, not complaint detection; human-reviewed complaint evaluation is pending.</p>
      </>}
    </div>
  </section>;
}
