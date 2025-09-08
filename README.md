# savi-bench
Public, rolling SAVI Benchmarks. Hourly AGI cycle (Warm-up, Strength, Endurance, Competition) with pass rate, scores, recovery stats, and competitor deltas. Auto-updates from runner; data lives in `data/agi_benchmark_log.json`. Public, reproducible, investor-friendly.

Live, verifiable benchmark. Reproduce a 10k-agent run with a $250 cap; verify with SHA256; view human-readable results in `reports/latest.html`.

## Try it now
- Live Report: https://faithovercp.github.io/savi-bench/
- DS005 Proof Pack: https://github.com/FaithoverCP/savi-bench/releases/tag/DS005-20250908

## Latest DS005 Proof

- Release: https://github.com/FaithoverCP/savi-bench/releases/tag/DS005-20250908
- Assets: `proof_pack_FULL.tgz`, `sha256sums.txt`, `latency_summary.csv`, `latest.html`
- Highlights: 10k-agent run with budget cap enforcement (`stop_reason=budget_cap_reached_250.0`).

## Quick Test Checklist
1) Run: `python -m bench.run --config bench/config.json --profile savi_openai_1000 --budget-usd 250`
2) Report: `python -m bench.report results/latest.jsonl --out reports/latest.html`
3) Pack: `python tools/summarize_and_pack.py`
4) Verify: `./tools/verify.ps1 -Dir ./dist` (or `sha256sum` on macOS/Linux)

Demo modes: see `DEMO_MODE.md`

- Getting started: docs/GETTING_STARTED.md
