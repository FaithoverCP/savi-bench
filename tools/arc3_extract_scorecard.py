#!/usr/bin/env python3
"""Extract a compact, auditable ARC-AGI-3 result summary from benchmark logs.

This script deliberately preserves the raw scorecard object rather than guessing a
single schema. ARC Prize may revise field names over time; the normalized fields
are best-effort conveniences, while ``raw_scorecard`` remains the source of truth.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import pathlib
import re
from datetime import datetime, timezone
from typing import Any


SCORECARD_MARKERS = (
    "--- FINAL SCORECARD REPORT ---",
    "--- EXISTING SCORECARD REPORT ---",
)


def _extract_balanced_json(text: str, start: int) -> Any | None:
    """Return the first JSON object beginning at or after *start*."""
    decoder = json.JSONDecoder()
    cursor = start
    while True:
        brace = text.find("{", cursor)
        if brace < 0:
            return None
        try:
            value, _ = decoder.raw_decode(text[brace:])
            return value
        except json.JSONDecodeError:
            cursor = brace + 1


def extract_scorecard(text: str) -> Any | None:
    candidates: list[tuple[int, Any]] = []
    for marker in SCORECARD_MARKERS:
        search_at = 0
        while True:
            pos = text.find(marker, search_at)
            if pos < 0:
                break
            value = _extract_balanced_json(text, pos + len(marker))
            if value is not None:
                candidates.append((pos, value))
            search_at = pos + len(marker)
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def recursive_find(obj: Any, names: set[str]) -> list[Any]:
    found: list[Any] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key).lower() in names:
                found.append(value)
            found.extend(recursive_find(value, names))
    elif isinstance(obj, list):
        for value in obj:
            found.extend(recursive_find(value, names))
    return found


def first_scalar(values: list[Any]) -> Any | None:
    for value in values:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
    return None


def parse_game_list(text: str) -> list[str]:
    matches = re.findall(r"Game list:\s*(\[[^\n]*\])", text)
    if not matches:
        return []
    try:
        value = ast.literal_eval(matches[-1])
    except (SyntaxError, ValueError):
        return []
    return [str(item) for item in value] if isinstance(value, list) else []


def parse_exit_reasons(text: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r"AGENT EXIT REASON -- Agent: \[(?P<agent>.*?)\] "
        r"Game: \[(?P<game>.*?)\] Reason: \[(?P<reason>.*?)\]"
    )
    return [match.groupdict() for match in pattern.finditer(text)]


def parse_scorecard_url(text: str) -> str | None:
    urls = re.findall(r"View your scorecard online:\s*(https?://\S+)", text)
    return urls[-1].rstrip(".,)") if urls else None


def summarize_scorecard(scorecard: Any | None) -> dict[str, Any]:
    if scorecard is None:
        return {
            "score": None,
            "score_percent": None,
            "scorecard_id": None,
            "environments_count": None,
        }

    score = first_scalar(
        recursive_find(scorecard, {"score", "total_score", "aggregate_score", "overall_score"})
    )
    percent = first_scalar(
        recursive_find(scorecard, {"score_percent", "percentage", "percent", "overall_percentage"})
    )
    card_id = first_scalar(
        recursive_find(scorecard, {"scorecard_id", "card_id", "id"})
    )

    environments_count: int | None = None
    for key in ("environments", "games", "results", "scores"):
        values = recursive_find(scorecard, {key})
        for value in values:
            if isinstance(value, (list, dict)):
                environments_count = len(value)
                break
        if environments_count is not None:
            break

    return {
        "score": score,
        "score_percent": percent,
        "scorecard_id": card_id,
        "environments_count": environments_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()

    log_path = pathlib.Path(args.log)
    text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    scorecard = extract_scorecard(text)
    exit_reasons = parse_exit_reasons(text)
    normalized = summarize_scorecard(scorecard)

    api_error_lines = [
        line[-1000:]
        for line in text.splitlines()
        if any(token in line.lower() for token in ("api_error", "traceback", "exception", "error"))
    ][-50:]

    result = {
        "schema": "savi.arc_agi_3.run_summary.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "label": args.label,
        "log_path": str(log_path),
        "log_exists": log_path.exists(),
        "log_sha256": hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest(),
        "log_bytes": len(text.encode("utf-8", errors="replace")),
        "scorecard_found": scorecard is not None,
        "scorecard_url": parse_scorecard_url(text),
        "games_requested": parse_game_list(text),
        "games_requested_count": len(parse_game_list(text)),
        "exit_reasons": exit_reasons,
        "exit_reason_counts": {
            reason: sum(1 for item in exit_reasons if item["reason"] == reason)
            for reason in sorted({item["reason"] for item in exit_reasons})
        },
        "normalized": normalized,
        "raw_scorecard": scorecard,
        "diagnostic_error_lines": api_error_lines,
    }

    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "label": args.label,
        "scorecard_found": result["scorecard_found"],
        "scorecard_url": result["scorecard_url"],
        "games_requested_count": result["games_requested_count"],
        "normalized": normalized,
        "exit_reason_counts": result["exit_reason_counts"],
        "output": str(output_path),
    }, indent=2))
    return 0 if scorecard is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
