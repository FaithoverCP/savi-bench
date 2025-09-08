#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any, List


def load(path: Path) -> List[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: merge_json_log.py BASE OURS THEIRS")
        return 2
    base = Path(sys.argv[1])
    ours = Path(sys.argv[2])
    theirs = Path(sys.argv[3])

    all_rows: List[Dict[str, Any]] = []
    all_rows.extend(load(base))
    all_rows.extend(load(ours))
    all_rows.extend(load(theirs))

    seen = set()
    merged: List[Dict[str, Any]] = []
    for row in all_rows:
        if not isinstance(row, dict):
            continue
        key = row.get("run_id")
        if key in seen:
            continue
        seen.add(key)
        merged.append(row)

    ours.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

