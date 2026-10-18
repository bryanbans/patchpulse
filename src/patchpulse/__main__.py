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
            "compare-baselines",
            "train-transformer",
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
    if args.command == "train-transformer":
        from .neural import run

        run(args.mode)
        return
    if args.mode == "real":
        source = json.loads((PRIVATE / "current.json").read_text(encoding="utf-8"))
    else:
        source = json.loads((ROOT / "data/fixtures/synthetic.json").read_text(encoding="utf-8"))
    case = build_case(source["records"], config, source["coverage"], args.mode)
    folder = PRIVATE / args.mode
    folder.mkdir(exist_ok=True)
    if args.command == "compare-baselines":
        from .experiments import compare

        compare(args.mode)
        return
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

        from .experiments import frozen_development

        manifest = json.loads((folder / "split.json").read_text())
        training, _ = frozen_development(case["evidence"], manifest)
        pilot = random.Random(42).sample(training, min(60, len(training)))
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
        from .annotations import audit_annotations

        manifest = json.loads((folder / "split.json").read_text())
        audit = audit_annotations(rows, case["evidence"], manifest)
        (folder / "annotation-audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
        (folder / "human-annotations.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"Imported {len(rows)} reviewed records; provenance still requires human verification.")


if __name__ == "__main__":
    main()
