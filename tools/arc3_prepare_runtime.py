#!/usr/bin/env python3
"""Append a frozen, rate-efficient GPT runtime to ARC-AGI-3 model configs."""

from __future__ import annotations

import argparse
import os
import pathlib

import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-dir", default="arc3-benchmarking")
    parser.add_argument("--config-id", default="savi-sequential-v3")
    parser.add_argument("--max-output-tokens", type=int, default=2048)
    parser.add_argument("--compact-threshold", type=int, default=100000)
    args = parser.parse_args()

    benchmark_dir = pathlib.Path(args.benchmark_dir)
    config_path = benchmark_dir / "benchmarking" / "model_configs.yaml"
    entries = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    base = os.environ["SAVI_API_BASE"].rstrip("/")
    for suffix in ("/chat/completions", "/responses"):
        if base.endswith(suffix):
            base = base[: -len(suffix)].rstrip("/")
            break

    entry = {
        "id": args.config_id,
        "agent": {
            "MAX_ACTIONS_BASELINE_MULTIPLIER": 5.0,
            "MAX_CONTEXT_LENGTH": 175000,
            "MAX_RETRIES": 3,
            "MAX_RUNTIME_SECONDS": 2700,
            "MAX_ANIMATION_FRAMES": 7,
        },
        "runtime": {
            "sdk": "openai-python",
            "api": "responses",
            "state": "previous_response_id",
        },
        "client": {
            "base_url": base,
            "api_key_env": "SAVI_API_KEY",
        },
        "request": {
            "model": os.environ["SAVI_MODEL"],
            "max_output_tokens": args.max_output_tokens,
            "store": True,
            "compact_threshold": args.compact_threshold,
        },
        "pricing": {},
    }

    entries = [item for item in entries if item.get("id") != args.config_id]
    entries.append(entry)
    config_path.write_text(
        yaml.safe_dump(entries, sort_keys=False),
        encoding="utf-8",
    )

    print(
        {
            "config_id": args.config_id,
            "model": os.environ["SAVI_MODEL"],
            "api": "responses",
            "state": "previous_response_id",
            "max_output_tokens": args.max_output_tokens,
            "compact_threshold": args.compact_threshold,
            "base_configured": bool(base),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
