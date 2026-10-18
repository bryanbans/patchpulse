"""Local bounded transformer experiment. Training/validation only; optional dependencies."""

import hashlib
import json
import math
import os
import platform
import subprocess
import time
from collections import Counter
from datetime import UTC, datetime

import numpy as np

from .core import PRIVATE, ROOT, normalize
from .experiments import frozen_development, metrics, paired_bootstrap, recommendation_labels


def class_weights(labels):
    """Inverse-frequency weights calculated from training labels only; class 0 is negative."""
    counts = Counter(int(v) for v in labels)
    if set(counts) != {0, 1}:
        raise ValueError("Both training classes required")
    return [len(labels) / (2 * counts[i]) for i in [0, 1]]


def select_common_checkpoint(results, config):
    """Never select a lucky seed; require the complete predeclared experiment."""
    expected = {
        (c["id"], seed, epoch)
        for c in config["candidates"]
        for seed in config["seeds"]
        for epoch in range(1, config["epochs"] + 1)
    }
    keys = [(r["id"], r["seed"], r["epoch"]) for r in results]
    if set(keys) != expected or len(keys) != len(expected):
        raise ValueError("Incomplete or duplicate experiment results; cannot select")
    choices = []
    for candidate in config["candidates"]:
        for epoch in range(1, config["epochs"] + 1):
            rows = [r for r in results if r["id"] == candidate["id"] and r["epoch"] == epoch]
            choices.append(
                {
                    "id": candidate["id"],
                    "epoch": epoch,
                    "mean_macro_f1": float(np.mean([r["macro_f1"] for r in rows])),
                    "sd_macro_f1": float(np.std([r["macro_f1"] for r in rows], ddof=1)),
                    "mean_negative_f1": float(np.mean([r["negative_f1"] for r in rows])),
                }
            )
    return max(choices, key=lambda c: (c["mean_macro_f1"], c["mean_negative_f1"])), choices


def source_fingerprints():
    return {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in [
            "src/patchpulse/neural.py",
            "src/patchpulse/experiments.py",
            "src/patchpulse/core.py",
            "configs/transformer.json",
            "uv.lock",
        ]
    }


def run(mode="real"):
    # Set before torch import/initialization. All source text stays on this machine.
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    try:
        import torch
        import transformers
        from torch.utils.data import DataLoader
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            get_linear_schedule_with_warmup,
        )
    except ImportError as exc:
        raise RuntimeError("Install the optional neural extra: uv sync --extra neural --frozen") from exc

    folder = PRIVATE / mode
    config_path = ROOT / "configs/transformer.json"
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    manifest_bytes = (folder / "split.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    case = json.loads((folder / "case.json").read_text(encoding="utf-8"))
    train, validation = frozen_development(case["evidence"], manifest)
    baseline = json.loads((folder / "evaluation.json").read_text())
    if baseline["split_hash"] != manifest["split_hash"]:
        raise ValueError("Original baseline and frozen manifest differ")
    labels = np.asarray([int(r["voted_up"]) for r in train])
    vlabels = np.asarray([int(r["voted_up"]) for r in validation])
    weights = class_weights(labels)
    if set(vlabels) != {0, 1}:
        raise ValueError("Both validation classes required")
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = folder / "neural" / run_id
    run_dir.mkdir(parents=True)
    # Record the exact protocol before training; no account login or upload.
    (run_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    tokenizer = AutoTokenizer.from_pretrained(
        config["model_id"],
        revision=config["revision"],
        cache_dir=str(PRIVATE / "hf-cache"),
        trust_remote_code=False,
    )

    def encode(rows):
        texts = [normalize(r["text"]) for r in rows]
        lengths = [len(ids) for ids in tokenizer(texts, truncation=False)["input_ids"]]
        encoded = tokenizer(texts, truncation=True, max_length=config["max_length"])
        return [{key: value[i] for key, value in encoded.items()} for i in range(len(rows))], {
            "records": len(rows),
            "truncated_records": sum(n > config["max_length"] for n in lengths),
            "max_tokens_before_truncation": max(lengths),
            "median_tokens_before_truncation": float(np.median(lengths)),
        }

    train_inputs, train_lengths = encode(train)
    valid_inputs, valid_lengths = encode(validation)
    torch.set_num_threads(config["cpu_threads"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.use_deterministic_algorithms(True, warn_only=True)
    if device.type == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.cuda.reset_peak_memory_stats()
    results, score_arrays = [], {}
    training_started = time.perf_counter()
    deadline = training_started + config["maximum_training_seconds"]
    for candidate in config["candidates"]:
        for seed in config["seeds"]:
            transformers.set_seed(seed)
            model = AutoModelForSequenceClassification.from_pretrained(
                config["model_id"],
                revision=config["revision"],
                num_labels=2,
                id2label={0: "not_recommended", 1: "recommended"},
                label2id={"not_recommended": 0, "recommended": 1},
                cache_dir=str(PRIVATE / "hf-cache"),
                trust_remote_code=False,
                use_safetensors=True,
                attn_implementation="eager",
            ).to(device)
            parameter_count = sum(p.numel() for p in model.parameters())
            optimizer = torch.optim.AdamW(
                model.parameters(), lr=config["learning_rate"], weight_decay=config["weight_decay"]
            )
            total_steps = math.ceil(len(train) / config["batch_size"]) * config["epochs"]
            scheduler = get_linear_schedule_with_warmup(
                optimizer,
                num_warmup_steps=int(total_steps * config["warmup_fraction"]),
                num_training_steps=total_steps,
            )
            loss_weights = (
                torch.tensor(weights, dtype=torch.float32, device=device)
                if candidate["class_weight"]
                else None
            )
            generator = torch.Generator().manual_seed(seed)
            for epoch in range(1, config["epochs"] + 1):
                started = time.perf_counter()
                model.train()
                loader = DataLoader(
                    list(range(len(train))),
                    batch_size=config["batch_size"],
                    shuffle=True,
                    generator=generator,
                    num_workers=0,
                )
                loss_total = 0.0
                for step, ids in enumerate(loader):
                    if time.perf_counter() > deadline:
                        raise RuntimeError(
                            "Predeclared compute budget exceeded; no completed report or selection written"
                        )
                    batch_ids = ids.tolist()
                    batch = tokenizer.pad(
                        [train_inputs[i] for i in batch_ids], padding=True, return_tensors="pt"
                    ).to(device)
                    target = torch.tensor(labels[batch_ids], dtype=torch.long, device=device)
                    optimizer.zero_grad(set_to_none=True)
                    logits = model(**batch).logits
                    loss = torch.nn.functional.cross_entropy(logits, target, weight=loss_weights)
                    if not torch.isfinite(loss):
                        raise RuntimeError("Non-finite training loss")
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), config["gradient_clip_norm"])
                    optimizer.step()
                    scheduler.step()
                    loss_total += loss.item() * len(batch_ids)
                    if step % 40 == 0:
                        print(
                            json.dumps(
                                {
                                    "id": candidate["id"],
                                    "seed": seed,
                                    "epoch": epoch,
                                    "batch": step,
                                    "batches": len(loader),
                                    "loss": loss.item(),
                                }
                            ),
                            flush=True,
                        )
                model.eval()
                scores = []
                with torch.inference_mode():
                    for offset in range(0, len(valid_inputs), config["batch_size"]):
                        batch = tokenizer.pad(
                            valid_inputs[offset : offset + config["batch_size"]],
                            padding=True,
                            return_tensors="pt",
                        ).to(device)
                        scores.extend(torch.softmax(model(**batch).logits, dim=-1)[:, 0].cpu().tolist())
                scores = np.asarray(scores)
                row = {
                    "id": candidate["id"],
                    "class_weight": candidate["class_weight"],
                    "seed": seed,
                    "epoch": epoch,
                    "negative_threshold": config["negative_threshold"],
                    "mean_training_batch_loss": loss_total / len(train),
                    "epoch_train_and_validation_seconds": time.perf_counter() - started,
                    **metrics(vlabels.astype(bool), scores, config["negative_threshold"]),
                }
                results.append(row)
                score_arrays[(candidate["id"], seed, epoch)] = scores
                # Preserve the fixed representative seed's epochs; never cherry-pick a seed.
                if seed == config["representative_seed"]:
                    checkpoint = run_dir / candidate["id"] / f"epoch-{epoch}"
                    model.save_pretrained(checkpoint, safe_serialization=True)
                    tokenizer.save_pretrained(checkpoint)
                (run_dir / "progress.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
                print(
                    json.dumps(
                        {
                            k: row[k]
                            for k in [
                                "id",
                                "seed",
                                "epoch",
                                "macro_f1",
                                "negative_precision",
                                "negative_recall",
                            ]
                        }
                    ),
                    flush=True,
                )
            del model, optimizer, scheduler
            if device.type == "cuda":
                torch.cuda.empty_cache()
    selection, summary = select_common_checkpoint(results, config)
    chosen = next(
        r
        for r in results
        if r["id"] == selection["id"]
        and r["epoch"] == selection["epoch"]
        and r["seed"] == config["representative_seed"]
    )
    scores = score_arrays[(selection["id"], config["representative_seed"], selection["epoch"])]
    # Reconstruct classical validation scores from the trusted existing local model only.
    import joblib

    from .experiments import negative_scores

    original = joblib.load(folder / "baseline.joblib")
    original_predictions = recommendation_labels(
        negative_scores(original, [normalize(r["text"]) for r in validation]), 0.5
    )
    report = {
        "experiment_id": config["experiment_id"],
        "run_id": run_id,
        "mode": mode,
        "created_at": datetime.now(UTC).isoformat(),
        "status": "development validation only",
        "task": config["task"],
        "model_id": config["model_id"],
        "revision": config["revision"],
        "base_model_license": config["license"],
        "config": config,
        "split_hash": manifest["split_hash"],
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "source_sha256": source_fingerprints(),
        "code_commit_at_start": subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip(),
        "code_state": "Source fingerprints identify this experiment implementation, including uncommitted changes.",
        "counts": {
            "train": len(train),
            "validation": len(validation),
            "locked_temporal_test": len(manifest["partitions"]["locked_temporal_test"]),
        },
        "training_class_support": {
            "not_recommended": int(sum(labels == 0)),
            "recommended": int(sum(labels == 1)),
        },
        "validation_class_support": {
            "not_recommended": int(sum(vlabels == 0)),
            "recommended": int(sum(vlabels == 1)),
        },
        "train_only_class_weights": weights,
        "preprocessing": "Versioned normalize then pretrained uncased WordPiece; no stopword removal; right truncation",
        "token_lengths": {"train": train_lengths, "validation": valid_lengths},
        "parameter_count": parameter_count,
        "trainable_parameter_count": parameter_count,
        "results": results,
        "across_seed_summary": summary,
        "selection": selection,
        "representative_seed": config["representative_seed"],
        "selected": chosen,
        "uncertainty": paired_bootstrap(
            vlabels.astype(bool), recommendation_labels(scores, 0.5), original_predictions, 1000, 42
        ),
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "device": str(device),
            "hardware": torch.cuda.get_device_name() if device.type == "cuda" else platform.processor(),
            "cpu_threads": torch.get_num_threads(),
            "cuda_runtime": torch.version.cuda,
            "precision": "float32",
            "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated() if device.type == "cuda" else None,
            "determinism": "Seeded, deterministic algorithms warn-only; cross-platform bitwise reproducibility not claimed",
        },
        "training_and_evaluation_seconds": time.perf_counter() - training_started,
        "final_tests_opened": False,
        "calibrated": False,
        "limitations": [
            config["limits"],
            "Only 12 negative outer-validation examples; minority estimates are fragile.",
            "Pretrained language model introduces a pretraining-corpus exposure risk absent from the classical model; independence cannot be established.",
            "Right truncation may discard complaints late in long reviews. No aspect sentiment or generation result is established.",
        ],
    }
    checkpoint = run_dir / selection["id"] / f"epoch-{selection['epoch']}"
    report["checkpoint_files_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in checkpoint.iterdir() if p.is_file()
    }
    # Raw prediction-level errors remain private and explicitly unreviewed.
    errors = [
        {
            "version_id": r["version_id"],
            "text": r["text"],
            "recorded_recommendation": bool(label),
            "predicted_recommendation": bool(pred),
            "negative_score": float(score),
            "human_reviewed": False,
        }
        for r, label, pred, score in zip(
            validation, vlabels, recommendation_labels(scores, 0.5), scores, strict=True
        )
        if bool(label) != bool(pred)
    ]
    (run_dir / "errors-for-human-review.json").write_text(json.dumps(errors, indent=2), encoding="utf-8")
    (run_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (run_dir / "validation-scores.json").write_text(
        json.dumps({f"{k[0]}:{k[1]}:{k[2]}": v.tolist() for k, v in score_arrays.items()}), encoding="utf-8"
    )
    if (folder / "split.json").read_bytes() != manifest_bytes:
        raise ValueError("Frozen manifest changed during experiment")
    (ROOT / "reports" / f"transformer-{mode}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    pointer = folder / "neural-model.tmp"
    pointer.write_text(
        json.dumps(
            {
                "checkpoint": str(checkpoint.relative_to(folder)).replace("\\", "/"),
                "report": str((run_dir / "report.json").relative_to(folder)).replace("\\", "/"),
                "split_hash": manifest["split_hash"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    pointer.replace(folder / "neural-model.json")
    print(
        json.dumps(
            {
                "selected": selection,
                "representative": {
                    k: chosen[k] for k in ["macro_f1", "negative_precision", "negative_recall"]
                },
                "final_tests_opened": False,
            }
        ),
        flush=True,
    )
    return report
