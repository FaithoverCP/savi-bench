#!/usr/bin/env python3
"""Run one matched ARC-AGI-3 game pair sequentially and preserve evidence."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time


def run_command(command: list[str], *, cwd: pathlib.Path, log_path: pathlib.Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.run(
            command,
            cwd=cwd,
            env=os.environ.copy(),
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    return process.returncode


def copy_recordings(benchmark_dir: pathlib.Path, destination: pathlib.Path) -> None:
    source = benchmark_dir / "recordings"
    if destination.exists():
        shutil.rmtree(destination)
    if source.exists():
        shutil.copytree(source, destination)
    else:
        destination.mkdir(parents=True, exist_ok=True)


def clear_runtime_files(benchmark_dir: pathlib.Path) -> None:
    recordings = benchmark_dir / "recordings"
    if recordings.exists():
        shutil.rmtree(recordings)
    recordings.mkdir(parents=True, exist_ok=True)
    for path in (benchmark_dir / "logs.log", benchmark_dir / "arc_quota_exhausted.marker"):
        if path.exists():
            path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", required=True)
    parser.add_argument("--order", choices=("savi-first", "baseline-first"), required=True)
    parser.add_argument("--benchmark-dir", default="arc3-benchmarking")
    parser.add_argument("--config", default="savi-sequential-v3")
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--cooldown-seconds", type=float, default=65.0)
    args = parser.parse_args()

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    benchmark_dir = (repo_root / args.benchmark_dir).resolve()
    evidence_dir = (repo_root / args.evidence_dir).resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)

    conditions = ["savi", "baseline"] if args.order == "savi-first" else ["baseline", "savi"]
    return_codes: dict[str, int] = {}

    for index, condition in enumerate(conditions):
        clear_runtime_files(benchmark_dir)
        log_path = evidence_dir / f"{condition}.log"
        command = [
            "uv",
            "run",
            "python",
            "run_condition.py",
            f"--game={args.game}",
            f"--condition={condition}",
            f"--config={args.config}",
        ]
        return_codes[condition] = run_command(command, cwd=benchmark_dir, log_path=log_path)

        internal_log = benchmark_dir / "logs.log"
        if internal_log.exists():
            shutil.copy2(internal_log, evidence_dir / f"{condition}_internal.log")
        copy_recordings(benchmark_dir, evidence_dir / f"{condition}_recordings")

        extractor_command = [
            sys.executable,
            str(repo_root / "tools" / "arc3_extract_scorecard.py"),
            "--log",
            str(log_path),
            "--output",
            str(evidence_dir / f"{condition}_summary.json"),
            "--label",
            "SAVI v6.2.2 ARC profile" if condition == "savi" else "Matched host-model baseline",
        ]
        subprocess.run(extractor_command, cwd=repo_root, check=False)

        quota_marker = benchmark_dir / "arc_quota_exhausted.marker"
        if quota_marker.exists():
            shutil.copy2(quota_marker, evidence_dir / f"{condition}_quota_exhausted.marker")
            break

        if index == 0:
            print(
                f"Cooling down {args.cooldown_seconds:.0f}s before the matched condition ",
                f"for game {args.game}.",
                flush=True,
            )
            time.sleep(args.cooldown_seconds)

    pair_output = evidence_dir / "pair_comparison.json"
    pair_command = [
        sys.executable,
        str(repo_root / "tools" / "arc3_pair_summary.py"),
        "--game",
        args.game,
        "--order",
        args.order,
        "--savi-summary",
        str(evidence_dir / "savi_summary.json"),
        "--baseline-summary",
        str(evidence_dir / "baseline_summary.json"),
        "--savi-log",
        str(evidence_dir / "savi.log"),
        "--baseline-log",
        str(evidence_dir / "baseline.log"),
        "--savi-recordings",
        str(evidence_dir / "savi_recordings"),
        "--baseline-recordings",
        str(evidence_dir / "baseline_recordings"),
        "--output",
        str(pair_output),
    ]
    pair_result = subprocess.run(pair_command, cwd=repo_root, check=False)

    manifest = {
        "game": args.game,
        "order": args.order,
        "condition_return_codes": return_codes,
        "pair_summary_return_code": pair_result.returncode,
    }
    (evidence_dir / "driver_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return pair_result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
