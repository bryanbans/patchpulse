import React, { useEffect, useState } from "react";
type Candidate = {
  id: string;
  macro_f1: number;
  negative_precision: number;
  negative_recall: number;
  negative_threshold: number;
  confusion_matrix: number[][];
};
type Report = {
  selected_id: string;
  counts: { validation: number };
  validation_class_support: { recommended: number; not_recommended: number };
  candidates: Candidate[];
  uncertainty: { macro_f1_interval_95: number[] };
};
export function ResearchPanel() {
  const [report, setReport] = useState<Report | null>(null);
  useEffect(() => {
    fetch("/api/research-evaluation")
      .then((r) => (r.ok ? r.json() : null))
      .then(setReport)
      .catch(() => {});
  }, []);
  if (!report) return null;
  const chosen = report.candidates.find((c) => c.id === report.selected_id)!;
  const sensitive = report.candidates.find((c) => c.id === "word-threshold-v2");
  const support = report.validation_class_support;
  return (
    <section className="panel research-panel" aria-labelledby="research-title">
      <span className="eyebrow">
        REAL-DATA DEVELOPMENT STUDY · AGGREGATE RESULTS
      </span>
      <h2 id="research-title">Catch the negatives. Count the false alarms.</h2>
      <p>
        Six fixed CPU baselines on the same frozen Deep Rock Galactic split.
        Thresholds use training-only grouped cross-validation. Selection uses
        406 chronological validation records: 394 recommended, just 12 not
        recommended.
      </p>
      <div className="evaluation-grid">
        <div>
          <strong>{chosen.macro_f1.toFixed(3)}</strong>
          <span>Selected validation macro F1</span>
        </div>
        <div>
          <strong>
            {chosen.confusion_matrix[0][0]} / {support.not_recommended}
          </strong>
          <span>
            Negative reviews detected · {chosen.confusion_matrix[1][0]} false
            alarms
          </span>
        </div>
        <div>
          <strong>{(chosen.negative_precision * 100).toFixed(1)}%</strong>
          <span>Negative prediction precision</span>
        </div>
      </div>
      <div
        className="table-scroll"
        tabIndex={0}
        role="region"
        aria-label="Detector comparison"
      >
        <table>
          <thead>
            <tr>
              <th>Detector</th>
              <th>Macro F1</th>
              <th>Negative precision</th>
              <th>Negative recall</th>
              <th>Negative threshold</th>
            </tr>
          </thead>
          <tbody>
            {report.candidates.map((c) => (
              <tr
                key={c.id}
                className={c.id === report.selected_id ? "selected-model" : ""}
              >
                <th>
                  {c.id}
                  {c.id === report.selected_id ? " · selected" : ""}
                </th>
                <td>{c.macro_f1.toFixed(3)}</td>
                <td>{(c.negative_precision * 100).toFixed(1)}%</td>
                <td>{(c.negative_recall * 100).toFixed(1)}%</td>
                <td>{c.negative_threshold}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>
        The sensitive word model catches {sensitive?.confusion_matrix[0][0]} of{" "}
        {support.not_recommended} negatives but flags{" "}
        {sensitive?.confusion_matrix[1][0]} recommended reviews. The selected
        character model catches fewer negatives with fewer false alarms. Neither
        detector measures aspect sentiment.
      </p>
      <div className="detail">
        <strong>Development evidence, with wide uncertainty.</strong>
        <p>
          Selected macro F1 bootstrap interval:{" "}
          {report.uncertainty.macro_f1_interval_95
            .map((x) => x.toFixed(3))
            .join("–")}{" "}
          (95%, 1,000 label-stratified resamples). This interval does not
          correct for selecting on the same validation set, source bias, or
          unseen-game performance. Final tests remain unopened. Public demo
          predictions still use synthetic training data.
        </p>
      </div>
    </section>
  );
}
