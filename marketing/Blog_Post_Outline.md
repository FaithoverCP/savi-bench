# Why One‑Time AI Benchmarks Are Dead

> **Status notice (2026-10-28).** This repository is a benchmark harness under repair and does not currently publish verified benchmark results. The DS005 "10,000-agent / $250-cap" proof pack was generated in synthetic mode: its manifest records `mode: synthetic` with no model or API, and its task count and cost were computed from configuration rather than executed. Dashboard scores produced in synthetic mode were random placeholders, an automatic "pass" row was added for every run regardless of outcome, and every real-mode task logged so far scored 0. Automatic hourly runs are paused. Please do not cite figures from this repository until a verified run is published.

## TL;DR
- One‑off, non‑verifiable benchmarks are out.
- Continuous, transparent, cryptographically verifiable benchmarks are in.
- See DS005 proof pack and replay: https://github.com/FaithoverCP/savi-bench/releases/tag/DS005-20250908

## The Problem
- Benchmarks shared as slides; no raw data; no manifests; no budgets.

## The SAVI Approach
- 4‑phase cognitive cycle; budget‑aware runs; public artifacts.
- Proof packs: JSONL rows, CSV latency summary, HTML report, logs, manifests, checksums.

## Results That Hold Up
- 10k‑agent run with $250 cap; reproducible metrics; public integrity hashes.

## Replay in Minutes
- Clone repo, run `tools/replay.ps1` (capped), regenerate report, verify hashes.

## What’s Next
- More deterministic suites; third‑party notaries; longitudinal deltas with error bars.
