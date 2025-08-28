import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _parse_result_file(text: str) -> Dict[str, Any]:
    """Parse a simple results txt file produced by bench.run.

    Expected lines:
      profile: <name>
      run: <ISO8601>
    """
    info: Dict[str, Any] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        info[k.strip().lower()] = v.strip()
    return info


def _load_json_array(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate benchmark report")
    parser.add_argument(
        "--config", default="bench/config.json", help="Path to configuration file"
    )
    parser.add_argument(
        "--output", default="reports/summary.json", help="Report output file"
    )
    parser.add_argument(
        "--html-data",
        default="data/agi_benchmark_log.json",
        help="Path to dashboard data JSON (array)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    results_dir = Path(config.get("results_dir", "results"))

    summary: Dict[str, str] = {}
    # Build summary from raw result files
    if results_dir.exists():
        for file in results_dir.glob("*.txt"):
            summary[file.stem] = file.read_text(encoding="utf-8").strip()

    report = {
        "generated": datetime.utcnow().isoformat(),
        "results": summary,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Also emit/merge a lightweight entry list for the dashboard HTML
    html_data_path = Path(args.html_data)
    html_data_path.parent.mkdir(parents=True, exist_ok=True)

    existing = _load_json_array(html_data_path)
    # Index existing entries by run_id if present else (profile,timestamp,phase)
    def key_of(e: Dict[str, Any]):
        return e.get("run_id") or (e.get("profile"), e.get("timestamp"), e.get("phase"))

    seen = {key_of(e) for e in existing}

    new_entries: List[Dict[str, Any]] = []
    if results_dir.exists():
        # Import structured results first (preferred)
        for jf in results_dir.glob("*.json"):
            try:
                obj = json.loads(jf.read_text(encoding="utf-8"))
            except Exception:
                continue
            records: List[Dict[str, Any]]
            if isinstance(obj, list):
                records = [x for x in obj if isinstance(x, dict)]
            elif isinstance(obj, dict):
                records = [obj]
            else:
                records = []
            for rec in records:
                k = key_of(rec)
                if k in seen:
                    continue
                # ensure required fields exist
                rec.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
                rec.setdefault("profile", jf.stem.split("-")[0])
                rec.setdefault("phase", "Competition")
                rec.setdefault("status", "pass")
                rec.setdefault("score", 0.0)
                rec.setdefault("retries", 0)
                rec.setdefault("trace", "report-import-json")
                new_entries.append(rec)
                seen.add(k)

        # Fall back to minimal entries from txt files (back-compat)
        for file in results_dir.glob("*.txt"):
            info = _parse_result_file(file.read_text(encoding="utf-8"))
            profile = info.get("profile", file.stem)
            ts = info.get("run") or datetime.utcnow().isoformat()
            minimal = {
                "run_id": f"{profile}-{ts}",
                "profile": profile,
                "phase": "Competition",
                "timestamp": ts if ts.endswith("Z") else f"{ts}Z" if "T" in ts else ts,
                "status": "pass",
                "score": 0.0,
                "retries": 0,
                "trace": "report-import",
            }
            k = key_of(minimal)
            if k in seen:
                continue
            new_entries.append(minimal)
            seen.add(k)

    merged = existing + new_entries
    html_data_path.write_text(json.dumps(merged, indent=2), encoding="utf-8")

    print(
        f"Wrote report to {output_path} and updated {html_data_path} (+{len(new_entries)})"
    )


if __name__ == "__main__":
    main()
