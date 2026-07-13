#!/usr/bin/env python3
"""Build and validate one matched SAVI-versus-baseline ARC game pair."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

INFRASTRUCTURE_ERROR_TOKENS = (
    "rate_limit_exceeded",
    "insufficient_quota",
    "exceeded your current quota",
    "invalid_api_key",
    "authenticationerror",
    "failed to get a valid action after",
)


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def number(value: Any, default: float = 0.0) -> float:
    return float(value) if isinstance(value, (int, float)) else default


def recording_usage(root: pathlib.Path) -> dict[str, Any]:
    totals: dict[str, Any] = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "reasoning_tokens": 0,
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "duration_seconds": 0.0,
        "total_steps": 0,
    }
    outcomes: list[str] = []
    models: set[str] = set()
    run_meta_files = sorted(root.rglob("run_meta.json")) if root.exists() else []

    for path in run_meta_files:
        data = load_json(path)
        usage = data.get("total_usage") or {}
        for key in (
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "reasoning_tokens",
            "cached_tokens",
            "cache_write_tokens",
        ):
            value = usage.get(key, 0)
            if isinstance(value, (int, float)):
                totals[key] += value
        for key in ("duration_seconds", "total_steps"):
            value = data.get(key, 0)
            if isinstance(value, (int, float)):
                totals[key] += value
        if data.get("outcome"):
            outcomes.append(str(data["outcome"]))
        if data.get("model"):
            models.add(str(data["model"]))

    totals["run_meta_count"] = len(run_meta_files)
    totals["outcomes"] = outcomes
    totals["models"] = sorted(models)
    return totals


def raw_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    raw = summary.get("raw_scorecard") or {}
    environments = (raw.get("environments") or []) if isinstance(raw, dict) else []
    environment = environments[0] if len(environments) == 1 else {}
    run: dict[str, Any] = {}
    if isinstance(environment, dict):
        runs = environment.get("runs") or []
        if len(runs) == 1 and isinstance(runs[0], dict):
            run = runs[0]

    return {
        "score": raw.get("score") if isinstance(raw, dict) else None,
        "total_actions": raw.get("total_actions") if isinstance(raw, dict) else None,
        "total_environments": raw.get("total_environments") if isinstance(raw, dict) else None,
        "total_environments_completed": raw.get("total_environments_completed") if isinstance(raw, dict) else None,
        "total_levels": raw.get("total_levels") if isinstance(raw, dict) else None,
        "total_levels_completed": raw.get("total_levels_completed") if isinstance(raw, dict) else None,
        "environment_id": environment.get("id") if isinstance(environment, dict) else None,
        "resets": environment.get("resets") if isinstance(environment, dict) else None,
        "completed": environment.get("completed") if isinstance(environment, dict) else None,
        "run_state": run.get("state") if isinstance(run, dict) else None,
        "level_actions": run.get("level_actions") if isinstance(run, dict) else None,
        "level_scores": run.get("level_scores") if isinstance(run, dict) else None,
    }


def condition_result(
    *,
    label: str,
    summary_path: pathlib.Path,
    log_path: pathlib.Path,
    recordings_path: pathlib.Path,
) -> dict[str, Any]:
    summary = load_json(summary_path)
    metrics = raw_metrics(summary)
    usage = recording_usage(recordings_path)
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    lowered = log_text.lower()

    errors: list[str] = []
    if not summary.get("scorecard_found"):
        errors.append("missing scorecard object")
    if not summary.get("scorecard_url"):
        errors.append("missing official scorecard URL")
    if metrics.get("total_environments") != 1:
        errors.append(f"expected one environment, found {metrics.get('total_environments')!r}")
    if not isinstance(metrics.get("total_actions"), int) or metrics.get("total_actions", 0) <= 0:
        errors.append("no successful ARC actions recorded")
    if usage.get("run_meta_count", 0) != 1:
        errors.append(f"expected one run_meta record, found {usage.get('run_meta_count')}")
    if number(usage.get("total_steps")) <= 0:
        errors.append("no model steps recorded")

    agent_errors = summary.get("exit_reason_counts", {}).get("ExitReason.AGENT_ERROR", 0)
    if agent_errors:
        errors.append(f"agent error count={agent_errors}")

    detected = [token for token in INFRASTRUCTURE_ERROR_TOKENS if token in lowered]
    if detected:
        errors.append("infrastructure errors detected: " + ", ".join(detected))

    return {
        "label": label,
        "valid": not errors,
        "validation_errors": errors,
        "scorecard_url": summary.get("scorecard_url"),
        "scorecard_id": (summary.get("raw_scorecard") or {}).get("card_id") if isinstance(summary.get("raw_scorecard"), dict) else None,
        "exit_reason_counts": summary.get("exit_reason_counts", {}),
        "metrics": metrics,
        "usage": usage,
        "log_path": str(log_path),
        "log_bytes": log_path.stat().st_size if log_path.exists() else 0,
        "log_sha256": summary.get("log_sha256"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", required=True)
    parser.add_argument("--order", required=True)
    parser.add_argument("--savi-summary", required=True)
    parser.add_argument("--baseline-summary", required=True)
    parser.add_argument("--savi-log", required=True)
    parser.add_argument("--baseline-log", required=True)
    parser.add_argument("--savi-recordings", required=True)
    parser.add_argument("--baseline-recordings", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    savi = condition_result(
        label="SAVI v6.2.2 ARC profile",
        summary_path=pathlib.Path(args.savi_summary),
        log_path=pathlib.Path(args.savi_log),
        recordings_path=pathlib.Path(args.savi_recordings),
    )
    baseline = condition_result(
        label="Matched host-model baseline",
        summary_path=pathlib.Path(args.baseline_summary),
        log_path=pathlib.Path(args.baseline_log),
        recordings_path=pathlib.Path(args.baseline_recordings),
    )

    s_score = savi["metrics"].get("score")
    b_score = baseline["metrics"].get("score")
    absolute_delta = (
        float(s_score) - float(b_score)
        if isinstance(s_score, (int, float)) and isinstance(b_score, (int, float))
        else None
    )
    relative_delta = (
        absolute_delta / float(b_score) * 100
        if isinstance(absolute_delta, (int, float))
        and isinstance(b_score, (int, float))
        and b_score != 0
        else None
    )

    game_ids = {
        value
        for value in (
            savi["metrics"].get("environment_id"),
            baseline["metrics"].get("environment_id"),
        )
        if value
    }
    pair_errors: list[str] = []
    if len(game_ids) != 1:
        pair_errors.append(f"condition environment mismatch: {sorted(game_ids)}")
    if not savi["valid"]:
        pair_errors.append("SAVI condition invalid")
    if not baseline["valid"]:
        pair_errors.append("baseline condition invalid")

    output = {
        "schema": "savi.arc_agi_3.paired_game.v3",
        "game_requested": args.game,
        "environment_id": next(iter(game_ids)) if len(game_ids) == 1 else None,
        "condition_order": args.order,
        "valid": not pair_errors,
        "validation_errors": pair_errors,
        "conditions": {"savi": savi, "baseline": baseline},
        "paired_metrics": {
            "absolute_score_uplift": absolute_delta,
            "relative_score_uplift_percent": relative_delta,
            "levels_completed_delta": number(savi["metrics"].get("total_levels_completed")) - number(baseline["metrics"].get("total_levels_completed")),
            "actions_delta": number(savi["metrics"].get("total_actions")) - number(baseline["metrics"].get("total_actions")),
            "total_tokens_delta": number(savi["usage"].get("total_tokens")) - number(baseline["usage"].get("total_tokens")),
        },
    }

    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
