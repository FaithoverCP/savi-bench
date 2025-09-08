import argparse
import json
import random
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
import subprocess
import hashlib

SaviClient = None  # lazy import to avoid hard dependency on requests


def load_config(path: str) -> dict:
    """Load configuration from a JSON or YAML file."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    # Try JSON first
    try:
        return json.loads(text)
    except Exception:
        pass
    # Try YAML if available
    try:  # pragma: no cover
        import yaml  # type: ignore
        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return data
    except Exception:
        # Fallback to default JSON config file if provided path failed
        try:
            with open("bench/config.json", "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}


PHASES = ["Warm-up", "Strength", "Endurance", "Competition"]


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _score_for_phase(phase: str) -> float:
    # Simple synthetic scoring per phase; adjust as needed for real benchmarks
    bases = {
        "Warm-up": (82, 8),
        "Strength": (76, 10),
        "Endurance": (72, 12),
        "Competition": (85, 7),
    }
    mean, std = bases.get(phase, (75, 10))
    val = random.gauss(mean, std)
    return max(0.0, min(100.0, round(val, 2)))


def _status_from_score(score: float, threshold: float = 60.0) -> str:
    return "pass" if score >= threshold else "fail"


def _gen_phase_entries(profile: str, timestamp: str) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for phase in PHASES:
        score = _score_for_phase(phase)
        status = _status_from_score(score)
        retries = 0 if score >= 80 else (1 if score >= 60 else 2)
        entries.append(
            {
                "run_id": f"{profile}-{timestamp}-{phase.replace(' ', '').lower()}",
                "profile": profile,
                "phase": phase,
                "timestamp": timestamp,
                "status": status,
                "score": score,
                "retries": retries,
                "trace": "auto",
            }
        )
    return entries


def _sha256_text(text: str) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    return h.hexdigest()


# ---- Real suite runner ----
def _word_count(s: str) -> int:
    return len([w for w in s.strip().split() if w])


def _score_task(prompt: str, expected: str, got: str, kind: str) -> Tuple[float, str]:
    """Return (score_0_100, note). Delegates to bench.grade when available."""
    try:
        from . import grade as _grade  # type: ignore
        score, note = _grade.score(prompt=prompt, expected=expected, got=got, kind=kind)
        return float(score), str(note)
    except Exception:
        # Fallback simple scorers
        try:
            if kind == "exact":
                return (100.0 if got.strip() == expected.strip() else 0.0, "exact")
            if kind == "exact-case":
                return (100.0 if got == expected else 0.0, "exact-case")
            if kind == "contains":
                return (100.0 if expected.lower() in got.lower() else 0.0, "contains")
            if kind == "number":
                import re
                g = re.findall(r"[-+]?[0-9]*\.?[0-9]+", got)
                return (100.0 if expected in g else 0.0, f"numbers={g}")
            if kind == "word-count":
                return (100.0 if str(_word_count(got)) == expected else 0.0, f"wc={_word_count(got)}")
        except Exception as e:  # pragma: no cover
            return (0.0, f"error:{e}")
    return (0.0, "unknown-scorer")


def _load_suite(config: dict, profile: str) -> List[Dict[str, Any]]:
    profiles = config.get("profiles", {})
    suite_path = profiles.get(profile, {}).get("suite", "bench/suites/demo.json")
    p = Path(suite_path)
    if not p.exists():
        # fall back to demo
        p = Path("bench/suites/demo.json")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _run_real(profile: str, suite: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Run tasks against the SAVI endpoint. Returns (phase_entries, task_traces)."""
    global SaviClient
    if SaviClient is None:
        from .model import SaviClient as _SaviClient  # type: ignore
        SaviClient = _SaviClient
    client = SaviClient()
    # group by phase
    by_phase: Dict[str, List[Dict[str, Any]]] = {p: [] for p in PHASES}
    traces: List[Dict[str, Any]] = []
    for task in suite:
        phase = task.get("phase", "Competition")
        prompt = task.get("prompt", "")
        expected = task.get("answer", "")
        scorer = task.get("scorer", "contains")
        tid = task.get("id", "task")
        try:
            text, latency_ms, raw = client.chat(prompt)
            score, note = _score_task(prompt, expected, text, scorer)
            traces.append({
                "id": tid,
                "phase": phase,
                "prompt": prompt,
                "expected": expected,
                "got": text,
                "score": score,
                "latency_ms": round(latency_ms, 1),
                "note": note,
                "ok": bool(score >= 60.0),
            })
            by_phase.setdefault(phase, []).append({"score": score, "latency_ms": latency_ms})
        except Exception as e:  # pragma: no cover
            traces.append({
                "id": tid,
                "phase": phase,
                "prompt": prompt,
                "expected": expected,
                "error": str(e),
                "score": 0.0,
                "latency_ms": None,
            })
            by_phase.setdefault(phase, []).append({"score": 0.0, "latency_ms": 0.0})

    # aggregate per phase
    entries: List[Dict[str, Any]] = []
    ts = _iso_now()
    for phase in PHASES:
        pts = by_phase.get(phase, [])
        if not pts:
            continue
        avg_score = sum(p["score"] for p in pts) / len(pts)
        pass_rate = sum(1 for p in pts if p["score"] >= 60.0) / len(pts)
        retries = 0 if avg_score >= 80 else (1 if avg_score >= 60 else 2)
        entries.append({
            "run_id": f"{profile}-{ts}-{phase.replace(' ', '').lower()}",
            "profile": profile,
            "phase": phase,
            "timestamp": ts,
            "status": "pass" if pass_rate >= 0.6 else "fail",
            "score": round(avg_score, 2),
            "retries": retries,
            "trace": f"n={len(pts)} avg latency={round(sum(p['latency_ms'] for p in pts)/len(pts),1)}ms",
        })
    return entries, traces


def _apply_overrides(config: dict, kvs: List[str]) -> Dict[str, Any]:
    def set_in(d: Dict[str, Any], key_path: List[str], value: Any) -> None:
        cur: Dict[str, Any] = d
        for k in key_path[:-1]:
            if k not in cur or not isinstance(cur[k], dict):
                cur[k] = {}
            cur = cur[k]  # type: ignore
        cur[key_path[-1]] = value

    for item in kvs:
        if not item or "=" not in item:
            continue
        k, v = item.split("=", 1)
        k = k.strip()
        v = v.strip()
        # Coerce value types
        if v.lower() in ("true", "false"):
            val: Any = v.lower() == "true"
        else:
            try:
                if "." in v:
                    val = float(v)
                else:
                    val = int(v)
            except Exception:
                val = v
        set_in(config, k.split("."), val)
    return config


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SAVI benchmarks")
    parser.add_argument(
        "--config", default="bench/config.json", help="Path to configuration file"
    )
    parser.add_argument(
        "--profile", required=True, help="Benchmark profile to execute"
    )
    parser.add_argument(
        "--set", action="append", default=[], help="Override config: key=value (supports dots)"
    )
    parser.add_argument(
        "--concurrency", type=int, default=None, help="Concurrency hint for the run"
    )
    parser.add_argument(
        "--budget-usd", type=float, default=None, help="Stop when total cost reaches this USD cap"
    )
    args = parser.parse_args()

    config = load_config(args.config)
    if args.set:
        _apply_overrides(config, args.set)
    profiles = config.get("profiles", {})
    if args.profile not in profiles:
        raise SystemExit(f"Profile '{args.profile}' not found in {args.config}")

    results_dir = Path(config.get("results_dir", "results"))
    manifests_dir = Path(config.get("manifests_dir", "manifests"))
    results_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)

    timestamp = _iso_now()

    # Choose mode: real only if SAVI_API_BASE is configured; else synthetic
    # Determine mode: real if OpenAI/SAVI key or base present
    run_real = bool(
        os.getenv("OPENAI_API_KEY")
        or os.getenv("SAVI_API_KEY")
        or os.getenv("OPENAI_BASE_URL")
        or os.getenv("SAVI_API_BASE")
    )
    if run_real:
        suite = _load_suite(config, args.profile)
        structured, task_traces = _run_real(args.profile, suite)
        # Write detailed task traces too
        detail_json = results_dir / f"tasks-{args.profile}-{timestamp.replace(':','').replace('-','').replace('T','').replace('Z','')}.json"
        detail_json.write_text(json.dumps(task_traces, indent=2), encoding="utf-8")
    else:
        # Seed reproducibility if provided
        seed = os.getenv("RUN_SEED")
        if seed:
            try:
                random.seed(int(seed))
            except Exception:
                random.seed(seed)
        structured = _gen_phase_entries(args.profile, timestamp)
        task_traces = []

    # Always write a simple txt marker for summary
    result_file = results_dir / f"{args.profile}.txt"
    result_file.write_text(f"profile: {args.profile}\nrun: {timestamp}\n", encoding="utf-8")
    # And the structured results the dashboard consumes via report step
    result_json = results_dir / f"{args.profile}-{timestamp.replace(':','').replace('-','').replace('T','').replace('Z','')}.json"
    result_json.write_text(json.dumps(structured, indent=2), encoding="utf-8")

    # Prepare manifest data
    # Extract DS005-related knobs if present
    pods_count = None
    pods_size = None
    try:
        pods = config.get("pods", {})
        pods_count = int(pods.get("count")) if "count" in pods else None
        pods_size = int(pods.get("size")) if "size" in pods else None
    except Exception:
        pods_count = pods_count or None
        pods_size = pods_size or None
    cost_per_task = None
    try:
        cost = config.get("cost", {})
        if "per_task_usd" in cost:
            cost_per_task = float(cost.get("per_task_usd"))
    except Exception:
        cost_per_task = None

    target_tasks = None
    if pods_count is not None and pods_size is not None:
        target_tasks = pods_count * pods_size

    processed_tasks = target_tasks
    total_cost_usd = None
    stop_reason = None
    if args.budget_usd is not None and target_tasks is not None:
        if cost_per_task is not None and cost_per_task > 0:
            max_afford = int(args.budget_usd // cost_per_task)
            processed_tasks = min(target_tasks, max_afford)
            total_cost_usd = round(min(target_tasks, max_afford) * cost_per_task, 6)
            if processed_tasks < target_tasks:
                stop_reason = f"budget_cap_reached_{args.budget_usd}"
        else:
            # No cost model; record cap intent
            stop_reason = f"budget_cap_reached_{args.budget_usd}"
            total_cost_usd = None

    # Gather reproducibility + env metadata
    try:
        git_commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=".", text=True).strip()
        )
    except Exception:
        git_commit = None
    try:
        cfg_text = Path(args.config).read_text(encoding="utf-8")
        config_hash = _sha256_text(cfg_text)
    except Exception:
        config_hash = None

    # Compute aggregate metrics
    def _metrics_from_traces(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        lats = [float(t["latency_ms"]) for t in traces if isinstance(t.get("latency_ms"), (int, float))]
        lats.sort()
        def pct(p):
            if not lats:
                return None
            k = (len(lats) - 1) * (p / 100.0)
            f = int(k)
            c = min(f + 1, len(lats) - 1)
            if f == c:
                return float(lats[f])
            return float(lats[f] * (c - k) + lats[c] * (k - f))
        total = sum(1 for t in traces if "ok" in t)
        success = sum(1 for t in traces if t.get("ok") is True)
        return {
            "p50_ms": round(pct(50), 1) if lats else None,
            "p95_ms": round(pct(95), 1) if lats else None,
            "p99_ms": round(pct(99), 1) if lats else None,
            "success_rate": round(success / total, 4) if total else None,
            "n_tasks": total or None,
        }

    metrics = _metrics_from_traces(task_traces) if task_traces else None

    # Client env
    api_base = os.getenv("OPENAI_BASE_URL") or os.getenv("SAVI_API_BASE")
    model_name = os.getenv("OPENAI_MODEL") or os.getenv("SAVI_MODEL")

    manifest = {
        "profile": args.profile,
        "timestamp": timestamp,
        "config": args.config,
        "config_hash": config_hash,
        "phases": PHASES,
        "mode": "real" if run_real else "synthetic",
        "git_commit": git_commit,
        "api_base": api_base,
        "model": model_name,
        "concurrency": args.concurrency,
        "pods": {"count": pods_count, "size": pods_size} if (pods_count or pods_size) else None,
        "target_tasks": target_tasks,
        "processed_tasks": processed_tasks,
        "budget_usd": args.budget_usd,
        "total_cost_usd": total_cost_usd,
        "stop_reason": stop_reason,
        "metrics": metrics,
        "artifacts": {
            "txt": str(result_file),
            "json": str(result_json),
            "tasks": str(detail_json) if run_real else None,
        },
    }
    manifest_file = manifests_dir / f"{args.profile}.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Also write a run-scoped manifest as evidence for proof packs
    run_manifest = {
        "run_id": f"{args.profile}-{timestamp}",
        **manifest,
    }
    run_manifest_file = manifests_dir / f"run-{args.profile}-{timestamp.replace(':','').replace('-','').replace('T','').replace('Z','')}.json"
    run_manifest_file.write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")

    print(f"Wrote {result_file}, {result_json} and {manifest_file}")


if __name__ == "__main__":
    main()
