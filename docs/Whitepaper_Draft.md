# SAVI Bench — Technical White Paper (Draft)

## Abstract
Benchmarks often fail reproducibility and integrity. SAVI Bench introduces continuous, transparent AGI benchmarking with cryptographic proof packs and a patent‑pending 4‑phase cognitive cycle.

## 1. Background and Motivation
- One‑off, cherry‑picked results mislead stakeholders.
- “Marketing benchmarks” lack public raw data, manifests, and integrity checks.

## 2. Methodology: 4‑Phase Cognitive Cycle
- Warm‑up → Strength → Endurance → Competition.
- Profiles define suites, evaluators, and budget controls.
- Budget cap enforcements recorded as `stop_reason` in manifests.

## 3. System Architecture
- Runner (`bench.run`) executes suites, records task traces and phase summaries.
- Grader (`bench.grade`) supports exact/fuzzy/regex/numeric/JSON checks.
- Reporter (`bench.report`) aggregates to HTML + dashboard JSON.
- Packager (`tools/summarize_and_pack.py`) outputs JSONL, CSV (p50/p90/p95/p99, success), tarball, and SHA256.

## 4. Deterministic Evaluation
- Reasoning, Tool‑Use, Safety/Guardrail suites target >100 tasks.
- Deterministic evaluators: unit tests, regex, numeric tolerance, JSON equality.
- Persist `grade_details` per task for audit (extensible in `bench.grade`).

## 5. Competitor Deltas
- `tools/fetch_competitors.py` updates `data/system_metrics.json` with timestamps and sources.
- Dashboard renders competitor table; 7/30‑day deltas and error bars planned.

## 6. Reproducibility
- Manifests include `mode`, `model`, `api_base`, `git_commit`, `config_hash`, `budget_usd`, `processed_tasks`.
- Seed via `RUN_SEED` for synthetic mode; config overrides via `--set` are recorded in manifests.

## 7. Results (DS005)
- 10,000‑agent run with $250 cap; evidence: `stop_reason=budget_cap_reached_250.0`.
- Aggregated latency and success rate reproducible via JSONL/CSV.
- Public release: DS005 — Proof Pack + Replay Instructions.

## 8. Verification Procedure
1) Download `proof_pack_FULL.tgz` and `sha256sums.txt`.
2) Verify hashes; unpack artifacts; inspect manifests/logs.
3) Replay capped run; regenerate report; compare metrics within tolerance.

## 9. Patent‑Pending Claim
Continuous cognitive benchmarking with cryptographic integrity and budget‑aware constraints.

## 10. Discussion and Future Work
- Expand deterministic suites; stronger fuzzy metrics; add 7/30‑day deltas with error bars.
- Signed attestations and third‑party notaries.
