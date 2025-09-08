#!/usr/bin/env python3
"""
Fetch competitor metrics and update data/system_metrics.json with timestamp and source.

Usage:
  python tools/fetch_competitors.py --source data/competitors.json
  python tools/fetch_competitors.py --url https://example.com/metrics.json

Input JSON shape:
  {
    "model": "SAVI-X",
    "metrics": {"accuracy_pct": 85.2, "inference_latency_ms": 45, ...},
    "comparisons": [
      {"name":"Competitor A","accuracy_pct":82,"latency_ms":60,"train_hours":1000,"tflops":100,"energy_cost_usd":12},
      ...
    ]
  }
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=str, help="Local JSON file with metrics")
    ap.add_argument("--url", type=str, help="Remote URL to fetch metrics JSON")
    args = ap.parse_args()

    data: Dict[str, Any]
    if args.source:
        data = json.loads(Path(args.source).read_text(encoding="utf-8"))
        source = f"file:{args.source}"
        method = "file"
    elif args.url:
        if requests is None:
            raise SystemExit("requests not available to fetch URL")
        r = requests.get(args.url, timeout=20)
        r.raise_for_status()
        data = r.json()
        source = args.url
        method = "http"
    else:
        raise SystemExit("Provide --source or --url")

    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    data.setdefault("source", source)
    data.setdefault("method", method)

    out = Path("data/system_metrics.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

