import React, { useMemo, useRef, useState } from "react";

type Row = Record<string, string>;
type Candidate = {
  index: number;
  id: string | null;
  text: string;
  suggestions: { aspect: string; polarity: string; passage: string }[];
};
type Result = {
  records_received: number;
  candidate_reviews: number;
  candidate_reviews_by_aspect: Record<string, number>;
  candidates: Candidate[];
  limitations: string[];
};

function parseCsv(source: string): Row[] {
  const rows: string[][] = [];
  let row: string[] = [], value = "", quoted = false;
  for (let i = 0; i < source.length; i += 1) {
    const char = source[i];
    if (char === '"' && quoted && source[i + 1] === '"') { value += '"'; i += 1; }
    else if (char === '"') quoted = !quoted;
    else if (char === "," && !quoted) { row.push(value); value = ""; }
    else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && source[i + 1] === "\n") i += 1;
      row.push(value); value = "";
      if (row.some((cell) => cell.trim())) rows.push(row);
      row = [];
    } else value += char;
  }
  row.push(value);
  if (row.some((cell) => cell.trim())) rows.push(row);
  if (rows.length < 2) throw new Error("The CSV needs a header row and at least one review.");
  const headers = rows[0].map((h, i) => h.trim() || `column_${i + 1}`);
  return rows.slice(1).map((cells) => Object.fromEntries(headers.map((h, i) => [h, cells[i] || ""])));
}

function parseFile(source: string, name: string): Row[] {
  if (name.toLowerCase().endsWith(".json")) {
    const parsed = JSON.parse(source);
    const rows = Array.isArray(parsed) ? parsed : parsed.records;
    if (!Array.isArray(rows) || !rows.every((row) => row && typeof row === "object" && !Array.isArray(row))) {
      throw new Error("JSON must be an array of review objects or an object with a records array.");
    }
    return rows.map((row) => Object.fromEntries(Object.entries(row).map(([key, value]) => [key, value == null ? "" : String(value)])));
  }
  return parseCsv(source);
}

const textNames = ["review", "text", "content", "body", "comment"];
const idNames = ["id", "review_id", "recommendationid", "reviewid"];
function guess(headers: string[], names: string[]) {
  return headers.find((header) => names.includes(header.trim().toLowerCase())) || headers[0] || "";
}

export function ImportWorkspace() {
  const input = useRef<HTMLInputElement>(null);
  const [rows, setRows] = useState<Row[]>([]);
  const [fileName, setFileName] = useState("");
  const [textField, setTextField] = useState("");
  const [idField, setIdField] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Result | null>(null);
  const headers = useMemo(() => Array.from(new Set(rows.flatMap((row) => Object.keys(row)))), [rows]);
  const usable = rows.filter((row) => row[textField]?.trim()).slice(0, 200);

  async function importFile(file: File) {
    setError(""); setResult(null);
    try {
      if (file.size > 1_500_000) throw new Error("Choose a file under 1.5 MB. Split a larger export into smaller review batches.");
      const parsed = parseFile(await file.text(), file.name);
      if (!parsed.length) throw new Error("No review rows were found.");
      const keys = Array.from(new Set(parsed.flatMap((row) => Object.keys(row))));
      setRows(parsed); setFileName(file.name); setTextField(guess(keys, textNames)); setIdField(guess(keys, idNames));
    } catch (e) { setRows([]); setError((e as Error).message); }
  }

  async function analyze() {
    if (!usable.length) { setError("Select a text column that contains at least one review."); return; }
    setBusy(true); setError(""); setResult(null);
    try {
      const response = await fetch("/api/analyze-feedback-batch", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ records: usable.map((row) => ({ id: idField ? row[idField] || null : null, text: row[textField].trim() })) }),
      });
      if (!response.ok) throw new Error(`Analysis unavailable (${response.status}). Split the import into fewer or shorter reviews and retry.`);
      setResult(await response.json());
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }

  function download() {
    if (!result) return;
    const lines = [
      "PatchPulse complaint-candidate export",
      "Provisional rule suggestions. Review the source text before treating a candidate as a product issue.",
      `Reviewed: ${result.records_received}; candidate reviews: ${result.candidate_reviews}`,
      ...result.candidates.flatMap((candidate) => [
        "",
        `Review ${candidate.id || candidate.index + 1}`,
        `Text: ${candidate.text}`,
        ...candidate.suggestions.map((s) => `Candidate: ${s.aspect} · ${s.polarity} · ${s.passage}`),
      ]),
    ];
    const anchor = document.createElement("a");
    anchor.href = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" }));
    anchor.download = "patchpulse-complaint-candidates.txt";
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(anchor.href), 1000);
  }

  return <section className="import-workspace" aria-labelledby="import-title">
    <div className="desk-title"><div><span className="eyebrow">LOCAL REVIEW IMPORT</span><h1 id="import-title">Turn an export into an investigation queue.</h1><p>Load review text from a CSV or JSON export. PatchPulse finds provisional complaint candidates, groups them by topic, and gives you the matching source text.</p></div></div>
    <div className="import-privacy"><strong>Your file stays local.</strong> The browser parses it, PatchPulse processes the selected text in memory, and neither side writes it to disk. Review exports may contain personal or private data.</div>
    <div className="import-grid">
      <section className="import-card"><h2>1. Choose a review export</h2><p>Use a CSV with a header row, or JSON as an array of objects (or <code>{'{ "records": [...] }'}</code>). A review-text column is required; an ID column is optional.</p><input ref={input} className="sr-only" type="file" accept=".csv,.json,text/csv,application/json" onChange={(event) => event.target.files?.[0] && importFile(event.target.files[0])}/><button className="primary" onClick={() => input.current?.click()}>Choose CSV or JSON</button>{fileName && <p className="import-file"><strong>{fileName}</strong> · {rows.length} rows read in this browser</p>}</section>
      <section className="import-card"><h2>2. Confirm the columns</h2>{headers.length ? <><label>Review text<select aria-label="Review text column" value={textField} onChange={(event) => setTextField(event.target.value)}>{headers.map((header) => <option key={header}>{header}</option>)}</select></label><label>Review ID <small>(optional)</small><select aria-label="Review ID column" value={idField} onChange={(event) => setIdField(event.target.value)}><option value="">No ID column</option>{headers.map((header) => <option key={header}>{header}</option>)}</select></label><p>{usable.length} review{usable.length === 1 ? "" : "s"} ready. Each run is limited to 200 reviews.</p><button className="primary" disabled={busy || !usable.length} onClick={analyze}>{busy ? "Finding candidates…" : "Find complaint candidates →"}</button></> : <p>Choose a file to map columns and start a local run.</p>}</section>
    </div>
    {error && <div className="error" role="alert">{error}</div>}
    {result && <section className="import-results" aria-live="polite"><div className="results-heading"><div><span className="eyebrow">PROVISIONAL OUTPUT</span><h2>{result.candidate_reviews} of {result.records_received} reviews have a complaint candidate.</h2></div><button className="secondary" onClick={download}>Export candidates ↓</button></div><p>Candidate reviews by topic. These are review counts, not issue counts or validated complaint rates.</p><div className="import-topic-counts">{Object.entries(result.candidate_reviews_by_aspect).map(([aspect, count]) => <span key={aspect}><strong>{count}</strong>{aspect}</span>)}</div>{result.candidates.length ? <div className="candidate-list">{result.candidates.map((candidate) => <article key={`${candidate.index}-${candidate.id || ""}`}><div><span>REVIEW {candidate.id || candidate.index + 1}</span>{candidate.suggestions.map((suggestion, index) => <p key={index}><strong>{suggestion.aspect}</strong> · {suggestion.polarity === "mixed" ? "mixed feedback" : "potential complaint"}<br />“{suggestion.passage}”</p>)}</div><blockquote>{candidate.text}</blockquote></article>)}</div> : <div className="empty">No explicit complaint candidates were found. Read a sample before concluding that there are no complaints; implicit or unusual wording can be missed.</div>}<details><summary>What this result can and cannot say</summary><ul>{result.limitations.map((item) => <li key={item}>{item}</li>)}</ul></details></section>}
  </section>;
}
