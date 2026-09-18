#!/usr/bin/env python3
"""Aggregate validated ARC game-pair evidence into a matched SAVI report."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import statistics
from typing import Any


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def bootstrap_mean_ci(values: list[float], *, samples: int = 10000) -> list[float] | None:
    if len(values) < 2:
        return None
    rng = random.Random(62022)
    means = []
    n = len(values)
    for _ in range(samples):
        means.append(statistics.fmean(rng.choice(values) for _ in range(n)))
    means.sort()
    return [means[int(0.025 * samples)], means[int(0.975 * samples) - 1]]


def two_sided_sign_test(wins: int, losses: int) -> float | None:
    n = wins + losses
    if n == 0:
        return None
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2.0 * tail)


def condition_metric(pair: dict[str, Any], condition: str, metric: str, default: Any = 0) -> Any:
    return pair["conditions"][condition]["metrics"].get(metric, default)


def usage_metric(pair: dict[str, Any], condition: str, metric: str, default: Any = 0) -> Any:
    return pair["conditions"][condition]["usage"].get(metric, default)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--expected-games-json", default="")
    args = parser.parse_args()

    root = pathlib.Path(args.root)
    pair_files = sorted(root.rglob("pair_comparison.json"))
    pairs = [load_json(path) for path in pair_files]
    expected_games = json.loads(args.expected_games_json) if args.expected_games_json else []

    by_game = {
        str(pair.get("environment_id") or pair.get("game_requested")): pair
        for pair in pairs
    }
    missing = [game for game in expected_games if game not in by_game]
    invalid = [
        str(pair.get("environment_id") or pair.get("game_requested"))
        for pair in pairs
        if not pair.get("valid")
    ]

    valid_pairs = [pair for pair in pairs if pair.get("valid")]
    differences = [
        float(pair["paired_metrics"]["absolute_score_uplift"])
        for pair in valid_pairs
        if isinstance(pair["paired_metrics"].get("absolute_score_uplift"), (int, float))
    ]

    wins = sum(value > 0 for value in differences)
    losses = sum(value < 0 for value in differences)
    ties = sum(value == 0 for value in differences)

    savi_scores = [float(condition_metric(pair, "savi", "score", 0.0)) for pair in valid_pairs]
    base_scores = [float(condition_metric(pair, "baseline", "score", 0.0)) for pair in valid_pairs]
    savi_mean = statistics.fmean(savi_scores) if savi_scores else None
    base_mean = statistics.fmean(base_scores) if base_scores else None
    absolute = savi_mean - base_mean if savi_mean is not None and base_mean is not None else None
    relative = absolute / base_mean * 100 if absolute is not None and base_mean else None

    valid = bool(valid_pairs) and not missing and not invalid and (
        not expected_games or len(valid_pairs) == len(expected_games)
    )

    result = {
        "schema": "savi.arc_agi_3.aggregate.v3",
        "valid": valid,
        "expected_games": expected_games,
        "pair_files_found": len(pair_files),
        "valid_pair_count": len(valid_pairs),
        "missing_games": missing,
        "invalid_games": invalid,
        "aggregate_scores": {
            "savi_mean_score": savi_mean,
            "baseline_mean_score": base_mean,
            "absolute_score_uplift": absolute,
            "relative_score_uplift_percent": relative,
        },
        "paired_statistics": {
            "savi_wins": wins,
            "baseline_wins": losses,
            "ties": ties,
            "mean_paired_difference": statistics.fmean(differences) if differences else None,
            "median_paired_difference": statistics.median(differences) if differences else None,
            "bootstrap_95_percent_ci_mean_difference": bootstrap_mean_ci(differences),
            "two_sided_sign_test_p": two_sided_sign_test(wins, losses),
        },
        "totals": {
            "savi_levels_completed": sum(condition_metric(pair, "savi", "total_levels_completed", 0) for pair in valid_pairs),
            "baseline_levels_completed": sum(condition_metric(pair, "baseline", "total_levels_completed", 0) for pair in valid_pairs),
            "savi_actions": sum(condition_metric(pair, "savi", "total_actions", 0) for pair in valid_pairs),
            "baseline_actions": sum(condition_metric(pair, "baseline", "total_actions", 0) for pair in valid_pairs),
            "savi_prompt_tokens": sum(usage_metric(pair, "savi", "prompt_tokens", 0) for pair in valid_pairs),
            "baseline_prompt_tokens": sum(usage_metric(pair, "baseline", "prompt_tokens", 0) for pair in valid_pairs),
            "savi_completion_tokens": sum(usage_metric(pair, "savi", "completion_tokens", 0) for pair in valid_pairs),
            "baseline_completion_tokens": sum(usage_metric(pair, "baseline", "completion_tokens", 0) for pair in valid_pairs),
            "savi_total_tokens": sum(usage_metric(pair, "savi", "total_tokens", 0) for pair in valid_pairs),
            "baseline_total_tokens": sum(usage_metric(pair, "baseline", "total_tokens", 0) for pair in valid_pairs),
        },
        "pairs": valid_pairs,
    }

    output_path = pathlib.Path(args.output)
    report_path = pathlib.Path(args.report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# SAVI ARC-AGI-3 Matched Paired Report",
        "",
        f"**Validity:** {'VALID' if valid else 'INVALID / INCOMPLETE'}",
        f"**Validated game pairs:** {len(valid_pairs)} / {len(expected_games) if expected_games else len(pair_files)}",
        "",
        "## Aggregate scores",
        "",
        f"- SAVI mean score: {savi_mean}",
        f"- Matched baseline mean score: {base_mean}",
        f"- Absolute uplift: {absolute}",
        f"- Relative uplift: {relative}%" if relative is not None else "- Relative uplift: not defined",
        "",
        "## Paired outcomes",
        "",
        f"- SAVI wins: {wins}",
        f"- Baseline wins: {losses}",
        f"- Ties: {ties}",
        f"- Mean paired difference: {result['paired_statistics']['mean_paired_difference']}",
        f"- Median paired difference: {result['paired_statistics']['median_paired_difference']}",
        f"- Bootstrap 95% CI: {result['paired_statistics']['bootstrap_95_percent_ci_mean_difference']}",
        f"- Two-sided sign-test p-value: {result['paired_statistics']['two_sided_sign_test_p']}",
        "",
        "## Validation exceptions",
        "",
        f"- Missing games: {missing}",
        f"- Invalid games: {invalid}",
        "",
        "This report is a matched ARC comparison, not an official Artificial Analysis Intelligence Index and not, by itself, proof of AGI.",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
