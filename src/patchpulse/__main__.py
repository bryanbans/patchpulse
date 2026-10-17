import argparse
import json

from .core import PRIVATE, ROOT, build_case


def main():
    parser = argparse.ArgumentParser(description="PatchPulse local, evidence-led workflow")
    parser.add_argument(
        "command",
        choices=[
            "collect",
            "build-demo",
            "prepare",
            "train-baseline",
            "annotate-export",
            "annotate-import",
            "serve",
        ],
    )
    parser.add_argument("--mode", choices=["synthetic", "real"], default="synthetic")
    parser.add_argument("--cap-per-period", type=int, default=500)
    parser.add_argument("--file")
    parser.add_argument("--resume-run")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    config = json.loads((ROOT / "configs/case.json").read_text(encoding="utf-8"))
    PRIVATE.mkdir(exist_ok=True)
    if args.command == "collect":
        from .collection import collect

        print(json.dumps(collect(config, args.cap_per_period, resume_run=args.resume_run), indent=2))
        return
    if args.command == "serve":
        import os

        import uvicorn

        os.environ["PATCHPULSE_MODE"] = args.mode
        if not 1024 <= args.port <= 65535:
            parser.error("--port must be between 1024 and 65535")
        uvicorn.run("patchpulse.api:app", host="127.0.0.1", port=args.port)
        return
    if args.mode == "real":
        source = json.loads((PRIVATE / "current.json").read_text(encoding="utf-8"))
    else:
        source = json.loads((ROOT / "data/fixtures/synthetic.json").read_text(encoding="utf-8"))
    case = build_case(source["records"], config, source["coverage"], args.mode)
    folder = PRIVATE / args.mode
    folder.mkdir(exist_ok=True)
    if args.command in ["build-demo", "prepare"]:
        (folder / "case.json").write_text(json.dumps(case, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {"mode": args.mode, "eligible": len(case["evidence"]), "exclusions": case["exclusions"]}
            )
        )
    if args.command in ["build-demo", "train-baseline"]:
        from .modeling import train

        print(json.dumps(train(case["evidence"], args.mode), indent=2))
    if args.command == "annotate-export":
        import random

        from .modeling import split_records

        partitions, _ = split_records(case["evidence"])
        pilot = random.Random(42).sample(partitions["train"], min(60, len(partitions["train"])))
        rows = [
            {"version_id": r["version_id"], "text": r["text"], "annotations": [], "human_reviewed": False}
            for r in pilot
        ]
        # Recommendation and rule suggestions hidden to avoid anchoring.
        (folder / "annotation-pilot.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"Exported {len(rows)} private annotation records to {folder / 'annotation-pilot.json'}")
    if args.command == "annotate-import":
        if not args.file:
            parser.error("--file is required")
        rows = json.loads(__import__("pathlib").Path(args.file).read_text(encoding="utf-8"))
        known = {r["version_id"]: r["text"] for r in case["evidence"]}
        from .core import ASPECTS

        for r in rows:
            if (
                r["version_id"] not in known
                or r.get("human_reviewed") is not True
                or not r.get("reviewer_id")
            ):
                raise ValueError("Unknown record, missing human review or reviewer ID")
            for a in r["annotations"]:
                if a["aspect"] not in ASPECTS or a["polarity"] not in [
                    "positive",
                    "negative",
                    "mixed",
                    "neutral",
                ]:
                    raise ValueError("Unknown annotation category")
                if not 0 <= a["start"] < a["end"] <= len(known[r["version_id"]]):
                    raise ValueError("Invalid evidence offsets")
                if known[r["version_id"]][a["start"] : a["end"]] != a["passage"]:
                    raise ValueError("Evidence is not an exact source substring")
        (folder / "human-annotations.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"Imported {len(rows)} reviewed records; provenance still requires human verification.")


if __name__ == "__main__":
    main()
