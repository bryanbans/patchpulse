import React, { useEffect, useState } from "react";
type Neural = {
  model_id: string;
  validation_class_support: { not_recommended: number };
  revision: string;
  counts: { train: number; validation: number };
  across_seed_summary: {
    id: string;
    epoch: number;
    mean_macro_f1: number;
    sd_macro_f1: number;
    mean_negative_f1: number;
  }[];
  config: { seeds: number[]; epochs: number; max_length: number };
  selected: {
    macro_f1: number;
    negative_recall: number;
    negative_precision: number;
    confusion_matrix: number[][];
  };
  selection: { id: string; epoch: number };
  parameter_count: number;
  token_lengths: { validation: { truncated_records: number } };
};
export function NeuralPanel() {
  const [report, setReport] = useState<Neural | null>(null);
  useEffect(() => {
    fetch("/api/neural-evaluation")
      .then((r) => (r.ok ? r.json() : null))
      .then(setReport)
      .catch(() => {});
  }, []);
  if (!report) return null;
  return (
    <section className="panel research-panel" aria-labelledby="neural-title">
      <span className="eyebrow">NEURAL NLP STUDY · THREE-SEED ABLATION</span>
      <h2 id="neural-title">Does context beat character patterns?</h2>
      <p>
        A pretrained DistilBERT encoder with a new recommendation head,
        fine-tuned on the same {report.counts.train.toLocaleString()} training
        records. Compare ordinary and class-balanced cross-entropy across seeds{" "}
        {report.config.seeds.join(", ")}. All{" "}
        {report.parameter_count.toLocaleString()} parameters train; the negative
        threshold stays fixed at 0.5.
      </p>
      <div className="evaluation-grid">
        <div>
          <strong>{report.selected.macro_f1.toFixed(3)}</strong>
          <span>Representative neural validation macro F1</span>
        </div>
        <div>
          <strong>
            {report.selected.confusion_matrix[0][0]} /{" "}
            {report.validation_class_support.not_recommended}
          </strong>
          <span>Negative validation reviews detected</span>
        </div>
        <div>
          <strong>
            {report.config.seeds.length} × {report.config.epochs}
          </strong>
          <span>Seeds × epochs for each loss variant</span>
        </div>
      </div>
      <div
        className="table-scroll"
        tabIndex={0}
        role="region"
        aria-label="Neural ablation comparison"
      >
        <table>
          <thead>
            <tr>
              <th>Loss variant</th>
              <th>Epoch</th>
              <th>Mean macro F1</th>
              <th>Seed SD</th>
              <th>Mean negative F1</th>
            </tr>
          </thead>
          <tbody>
            {report.across_seed_summary.map((r) => (
              <tr key={`${r.id}-${r.epoch}`}>
                <th>{r.id}</th>
                <td>{r.epoch}</td>
                <td>{r.mean_macro_f1.toFixed(3)}</td>
                <td>{r.sd_macro_f1.toFixed(3)}</td>
                <td>{r.mean_negative_f1.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="detail">
        <strong>Measured outcome: retain the classical detector.</strong>
        <p>
          Every neural checkpoint predicts the majority class at this threshold.
          The character model's 0.757 validation macro F1 remains stronger than
          this bounded neural experiment. This is a failure of the tested setup,
          not evidence that transformers cannot solve the task. Zero variation
          in macro F1 reflects identical class decisions; ranking scores still
          vary.
        </p>
      </div>
      <p>
        Token limit {report.config.max_length}:{" "}
        {report.token_lengths.validation.truncated_records} validation reviews
        were truncated. Candidate and common epoch are selected by mean
        validation scores; the representative model always uses seed 42. This
        validation set has been reused for development. Final temporal and
        unseen-game tests remain unopened. Neither model establishes aspect
        sentiment.
      </p>
      <a
        href="https://github.com/bryanbans/patchpulse/blob/main/docs/nlp_study.md"
        target="_blank"
        rel="noreferrer"
      >
        Read the NLP study and failure analysis ↗
      </a>
    </section>
  );
}
