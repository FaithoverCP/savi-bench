# Contributing to SAVI Bench

## Contributor Quick Start

If you only need the essentials:

1. Setup Environment
   - Windows: `py -3.11 -m venv .venv && .\\.venv\\Scripts\\Activate.ps1`
   - macOS/Linux: `python3.11 -m venv .venv && source .venv/bin/activate`

2. Run a Demo
   - `python -m bench.run --config bench/config.json --profile savi_openai_1000 --budget-usd 250`
   - `python -m bench.report results/latest.jsonl --out reports/latest.html`

3. Proof Pack
   - `python tools/summarize_and_pack.py`
   - Verify with `./tools/verify.ps1 -Dir ./dist` or `sha256sum`

4. Merging JSON Logs
   - Already configured via `.gitattributes` + `tools/merge_json_log.py`
   - Conflicts resolve automatically by appending unique `run_id`s

5. Security
   - Never commit API keys, secrets, or raw headers
   - Manifests and reports are scrubbed automatically

Thanks for helping improve SAVI Bench. A few notes to keep merges smooth and results reproducible.

## JSON Log Merge Driver (data/agi_benchmark_log.json)

Our dashboard log `data/agi_benchmark_log.json` is an append‑only array of run entries. To avoid manual conflict resolution, we use a content‑aware merge driver that appends and de‑duplicates by `run_id`.

Already included:
- `.gitattributes` marks the file with `merge=jqappend`.
- `tools/merge_json_log.py` is a portable Python merge driver.

Set it up (one‑time):

```bash
# From the repo root
git config merge.jqappend.name "JSON append + unique by run_id"
git config merge.jqappend.driver "python tools/merge_json_log.py %O %A %B"
```

This ensures merges keep all unique entries across branches.

## Real vs Synthetic

- Real mode triggers when `OPENAI_API_KEY` (or `SAVI_API_KEY`) is set.
- Synthetic mode uses seeded randomness (set `RUN_SEED`) for reproducibility.

## Security

- Do not print or commit secrets (API keys, tokens, auth headers).
- Manifests and reports include only non‑sensitive fields (model/base URI, commit SHA).

## Commit Hygiene

- Keep changes scoped; prefer small, descriptive commits.
- If adding large artifacts (e.g., screenshots), use the `marketing/` folder and avoid committing raw logs unless necessary.

## Quick Test

```bash
python -m bench.run --config bench/config.json --profile savi_openai_1000 --budget-usd 250
python -m bench.report results/latest.jsonl --out reports/latest.html
python tools/summarize_and_pack.py
```

- Verify `reports/latest.html` badges (mode/model/budget/stop/processed/commit)
- Verify `dist/proof_pack_FULL.tgz` + `dist/sha256sums.txt`
