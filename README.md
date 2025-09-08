# savi-bench
Public, rolling SAVI Benchmarks. Hourly AGI cycle (Warm-up, Strength, Endurance, Competition) with pass rate, scores, recovery stats, and competitor deltas. Auto-updates from runner; data lives in `data/agi_benchmark_log.json`. Public, reproducible, investor-friendly.

## Investor Quick Start

1. Open the latest report: `reports/latest.html`
   - Badges show: mode, model, budget, stop reason, processed tasks, commit.
2. Check the proof pack: download `dist/proof_pack_FULL.tgz` and compare against `dist/sha256sums.txt`.
   - SHA256 hashes prove the artifacts are tamper-evident.
3. Headline: 10,000 agents, $250 budget cap, SHA256-verified and reproducible.

Full demos: see `DEMO_MODE.md` and `docs/GETTING_STARTED.md`.

## Latest DS005 Proof

- Release: https://github.com/FaithoverCP/savi-bench/releases/tag/DS005-20250908
- Assets: `proof_pack_FULL.tgz`, `sha256sums.txt`, `latency_summary.csv`, `latest.html`
- Highlights: 10k-agent run with budget cap enforcement (`stop_reason=budget_cap_reached_250.0`).

- Getting started: docs/GETTING_STARTED.md
