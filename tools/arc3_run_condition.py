#!/usr/bin/env python3
"""Run one ARC-AGI-3 game under either SAVI or matched-baseline conditions.

This wrapper leaves the official ARC agent and environment logic intact. It only:
- optionally prepends a public-safe SAVI reasoning profile;
- applies a shared minimum interval between model calls;
- adds a longer pause after rate-limit responses; and
- records a quota marker when the provider reports insufficient quota.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import random
import re
import sys
import threading
import time
from collections.abc import Callable
from typing import Any

import main as arc_main
from benchmarking.agent import BenchmarkingAgent
from benchmarking.runtime_adapters import (
    OpenAIResponsesAdapter,
    OpenAIResponsesServerStateAdapter,
)

SAVI_ARC_PROFILE = """SAVI ARC operating profile:
Maintain a compact state ledger containing observed objects, controllable entities, goals, obstacles, action effects, level changes, contradictions, and unresolved hypotheses.
Use a bounded observe -> update -> predict -> act -> verify cycle. Distinguish observations from hypotheses. Prefer the next action that either advances the objective or efficiently separates competing explanations.
When progress stalls, step back, compare alternative world models, and change the pathway rather than repeating an unsuccessful action. Plan ahead only when the inferred mechanics justify it, then verify the predicted result after every action.
Preserve the action budget and keep notes concise. End every response with exactly one valid available action; the final action mentioned is the action that executes."""

_CALL_LOCK = threading.Lock()
_LAST_CALL_AT = 0.0


def _parse_retry_seconds(message: str) -> float:
    match = re.search(r"try again in\s+([0-9.]+)\s*(ms|s)", message, flags=re.I)
    if not match:
        return 0.0
    value = float(match.group(1))
    return value / 1000.0 if match.group(2).lower() == "ms" else value


def _wrap_invoke(original: Callable[..., Any]) -> Callable[..., Any]:
    def controlled_invoke(self: Any, request: Any) -> Any:
        global _LAST_CALL_AT

        minimum_interval = float(os.getenv("ARC_MIN_CALL_INTERVAL_SECONDS", "6"))
        with _CALL_LOCK:
            elapsed = time.monotonic() - _LAST_CALL_AT
            wait = max(0.0, minimum_interval - elapsed)
            if wait:
                time.sleep(wait)
            _LAST_CALL_AT = time.monotonic()

        try:
            return original(self, request)
        except Exception as exc:
            message = str(exc)
            lowered = message.lower()
            if "insufficient_quota" in lowered or "exceeded your current quota" in lowered:
                marker = pathlib.Path(
                    os.getenv("ARC_QUOTA_MARKER", "arc_quota_exhausted.marker")
                )
                marker.write_text(message[:4000], encoding="utf-8")
            elif (
                "rate_limit_exceeded" in lowered
                or "rate limit" in lowered
                or "error code: 429" in lowered
            ):
                provider_wait = _parse_retry_seconds(message)
                backoff = max(10.0, provider_wait + 5.0) + random.uniform(0.5, 2.5)
                print(
                    f"ARC rate controller: pausing {backoff:.1f}s after provider limit.",
                    flush=True,
                )
                time.sleep(backoff)
            raise

    return controlled_invoke


def install_rate_control() -> None:
    for adapter_cls in (OpenAIResponsesAdapter, OpenAIResponsesServerStateAdapter):
        adapter_cls.invoke = _wrap_invoke(adapter_cls.invoke)  # type: ignore[method-assign]


def install_savi_profile() -> None:
    original = BenchmarkingAgent._build_system_prompt

    def savi_system_prompt(self: BenchmarkingAgent) -> str:
        return SAVI_ARC_PROFILE + "\n\n" + original(self)

    BenchmarkingAgent._build_system_prompt = savi_system_prompt  # type: ignore[method-assign]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", required=True)
    parser.add_argument("--condition", choices=("savi", "baseline"), required=True)
    parser.add_argument("--config", default="savi-sequential-v3")
    args = parser.parse_args()

    install_rate_control()
    if args.condition == "savi":
        install_savi_profile()

    print(
        f"ARC paired condition start: game={args.game} condition={args.condition} "
        f"config={args.config} min_interval={os.getenv('ARC_MIN_CALL_INTERVAL_SECONDS', '6')}s",
        flush=True,
    )

    os.environ["TESTING"] = "False"
    sys.argv = [
        "main.py",
        f"--game={args.game}",
        f"--config={args.config}",
        f"--tags={args.condition},sequential-paired,savi-v6.2.2",
    ]
    arc_main.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
