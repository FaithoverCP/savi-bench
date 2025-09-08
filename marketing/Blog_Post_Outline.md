# Why One‑Time AI Benchmarks Are Dead

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
