#!/usr/bin/env python3
"""
Summarize latency metrics and build a DS005 proof pack.

Outputs:
  - results/latency_summary.csv (p50/p90/p95/p99 + success_rate)
  - results/latest.jsonl (task-by-task rows if available, else per-record JSON lines)
  - dist/proof_pack_FULL.tgz (logs/, manifests/, reports/, results artifacts)
  - dist/sha256sums.txt (sha256 for top-level artifacts)

This script is repo-aware and uses bench/config.json defaults.
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import tarfile


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "bench" / "config.json"


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _percentile(values: List[float], p: float) -> Optional[float]:
    if not values:
        return None
    if p <= 0:
        return float(values[0])
    if p >= 100:
        return float(values[-1])
    k = (len(values) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(values[int(k)])
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return float(d0 + d1)


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    yield obj
            except Exception:
                continue


def _to_jsonl_records(obj: Any) -> List[Dict[str, Any]]:
    """Normalize arbitrary JSON into a list[dict] for JSONL writing."""
    if isinstance(obj, dict):
        return [obj]
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    return []


def _pick_latest(pattern: str, base: Path) -> Optional[Path]:
    candidates = sorted(base.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def build_latest_jsonl(results_dir: Path) -> Path:
    out = results_dir / "latest.jsonl"
    # Prefer detailed task traces if present
    # 1) DS005 task traces for savi_openai_1000
    task_file = _pick_latest("tasks-savi_openai_1000-*.json", results_dir) or _pick_latest("tasks-*.json", results_dir)
    source_label = None
    records: List[Dict[str, Any]] = []
    if task_file and task_file.exists():
        data = _load_json(task_file) or []
        records = _to_jsonl_records(data)
        source_label = task_file.name
        # Ensure required fields exist for summarization
        for r in records:
            r.setdefault("kind", "task")
    else:
        # 2) Prefer DS005 structured JSON for savi_openai_1000, then fallback to latest
        latest_res = _pick_latest("savi_openai_1000-*.json", results_dir) or _pick_latest("*.json", results_dir)
        if latest_res and latest_res.exists():
            data = _load_json(latest_res) or []
            records = _to_jsonl_records(data)
            source_label = latest_res.name
            for r in records:
                r.setdefault("kind", "record")

    if not records:
        # Create an empty file to satisfy pipeline
        out.write_text("", encoding="utf-8")
        return out

    with out.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Wrote {out} from {source_label}")
    return out


def summarize_latency_and_success(jsonl_path: Path, out_csv: Path) -> Dict[str, Optional[float]]:
    lats: List[float] = []
    total = 0
    success = 0
    for obj in _iter_jsonl(jsonl_path):
        # latency (prefer explicit latency_ms; else parse from trace string)
        lat = obj.get("latency_ms")
        if lat is None:
            tr = obj.get("trace") or ""
            m = __import__("re").search(r"avg\s+latency\s*=\s*([0-9]+(?:\.[0-9]+)?)ms", str(tr))
            if m:
                try:
                    lat = float(m.group(1))
                except Exception:
                    lat = None
        try:
            if lat is not None:
                lats.append(float(lat))
        except Exception:
            pass
        # success
        ok = None
        if isinstance(obj.get("ok"), bool):
            ok = bool(obj.get("ok"))
        elif isinstance(obj.get("status"), str):
            ok = obj.get("status") == "pass"
        elif isinstance(obj.get("score"), (int, float)):
            ok = float(obj.get("score")) >= 60.0
        if ok is not None:
            total += 1
            if ok:
                success += 1

    lats.sort()
    p50 = _percentile(lats, 50)
    p90 = _percentile(lats, 90)
    p95 = _percentile(lats, 95)
    p99 = _percentile(lats, 99)
    sr = (success / total) if total else None

    _ensure_dir(out_csv.parent)
    # Write wide CSV: one row with columns
    headers = ["p50_ms", "p90_ms", "p95_ms", "p99_ms", "success_rate"]
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(headers)
        w.writerow([
            f"{p50:.1f}" if p50 is not None else "",
            f"{p90:.1f}" if p90 is not None else "",
            f"{p95:.1f}" if p95 is not None else "",
            f"{p99:.1f}" if p99 is not None else "",
            f"{sr:.4f}" if sr is not None else "",
        ])

    print(f"Wrote {out_csv}")
    return {"p50_ms": p50, "p90_ms": p90, "p95_ms": p95, "p99_ms": p99, "success_rate": sr}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_pack(dist_dir: Path, results_dir: Path, manifests_dir: Path, logs_dir: Path, reports_dir: Path) -> Path:
    _ensure_dir(dist_dir)
    out = dist_dir / "proof_pack_FULL.tgz"
    with tarfile.open(out, "w:gz") as tar:
        # Add directories (if missing, create empty markers)
        for d in [logs_dir, manifests_dir, reports_dir]:
            if d.exists():
                for p in sorted(d.rglob("*")):
                    if p.is_file():
                        tar.add(p, arcname=str(p.relative_to(REPO_ROOT)))
            else:
                # add an empty placeholder text to preserve tree in pack
                placeholder = dist_dir / f".empty_{d.name}"
                placeholder.write_text("", encoding="utf-8")
                tar.add(placeholder, arcname=str(Path(d.name) / ".empty"))
                placeholder.unlink(missing_ok=True)
        # Add results artifacts explicitly
        for name in ["latest.jsonl", "latency_summary.csv"]:
            p = results_dir / name
            if p.exists():
                tar.add(p, arcname=str(p.relative_to(REPO_ROOT)))
    print(f"Wrote {out}")
    return out


def write_checksums(out_dir: Path, files: List[Path]) -> Path:
    lines: List[str] = []
    for f in files:
        try:
            h = sha256_of(f)
            rel = f.relative_to(REPO_ROOT).as_posix()
            lines.append(f"{h}  {rel}")
        except Exception:
            continue
    sums = out_dir / "sha256sums.txt"
    sums.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    print(f"Wrote {sums}")
    return sums


def main() -> None:
    # Resolve dirs
    config = _load_json(DEFAULT_CONFIG) or {}
    results_dir = REPO_ROOT / config.get("results_dir", "results")
    manifests_dir = REPO_ROOT / config.get("manifests_dir", "manifests")
    logs_dir = REPO_ROOT / "logs"
    reports_dir = REPO_ROOT / "reports"
    dist_dir = REPO_ROOT / "dist"

    _ensure_dir(results_dir)
    _ensure_dir(manifests_dir)
    _ensure_dir(logs_dir)
    _ensure_dir(reports_dir)
    _ensure_dir(dist_dir)

    jsonl = build_latest_jsonl(results_dir)
    summary_csv = results_dir / "latency_summary.csv"
    summarize_latency_and_success(jsonl, summary_csv)

    pack = build_pack(dist_dir, results_dir, manifests_dir, logs_dir, reports_dir)
    # Include key top-level artifacts in checksums for easy verification
    html = reports_dir / "latest.html"
    sums = write_checksums(dist_dir, [pack, summary_csv, jsonl, html])

    # Friendly print for CI logs
    print("Artifacts:")
    print(f" - {jsonl}")
    print(f" - {summary_csv}")
    print(f" - {pack}")
    print(f" - {sums}")


if __name__ == "__main__":
    main()
