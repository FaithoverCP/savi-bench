# Contributing to SAVI Bench

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
