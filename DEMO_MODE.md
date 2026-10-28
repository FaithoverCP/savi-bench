# SAVI Bench — Demo Modes (DS005)

> **Status notice (2026-10-28).** This repository is a benchmark harness under repair and does not currently publish verified benchmark results. The DS005 "10,000-agent / $250-cap" proof pack was generated in synthetic mode: its manifest records `mode: synthetic` with no model or API, and its task count and cost were computed from configuration rather than executed. Dashboard scores produced in synthetic mode were random placeholders, an automatic "pass" row was added for every run regardless of outcome, and every real-mode task logged so far scored 0. Automatic hourly runs are paused. Please do not cite figures from this repository until a verified run is published.

## Investor Quick Demo (2–3 minutes)
- Open DS005: https://github.com/FaithoverCP/savi-bench/releases/tag/DS005-20250908
- Show the investor summary, assets list, and open `latest.html`.
- Point to `proof_pack_FULL.tgz` + `sha256sums.txt` and explain verifiability.

## Technical Deep-Dive (5–10 minutes)
```powershell
# Optional: real mode
Set-Item Env:OPENAI_API_KEY "sk-..."   # Optional: Set-Item Env:OPENAI_BASE_URL "https://api.openai.com/v1"

# Capped run + report
python -m bench.run --config bench/config.json --profile savi_openai_1000 --budget-usd 250
python -m bench.report results/latest.jsonl --out reports/latest.html

# Inspect manifest (mode, model, api_base, git_commit, config_hash, budget_usd, stop_reason, processed_tasks)
Get-ChildItem manifests -Filter "run-*.json" | Sort-Object LastWriteTime -Desc | Select-Object -First 1 | % { $_.FullName; Get-Content $_.FullName }
```

## 10k Proof (budget-capped)
```powershell
python -m bench.run --config bench/config.json --profile savi_openai_1000 `
  --set pods.count=10 --set pods.size=1000 --set concurrency=256 `
  --budget-usd 250
python -m bench.report results/latest.jsonl --out reports/latest.html
```

## Competitor Compare (optional)
```powershell
# Update competitor metrics (local file or URL)
python tools/fetch_competitors.py --source data/competitors.json
# Refresh index.html to show delta table with timestamp/source
```

## Pack + Verify
```powershell
python tools/summarize_and_pack.py
.\tools\verify.ps1 -Dir (Resolve-Path .\dist).Path
```

Notes
- Real mode if `OPENAI_API_KEY` (or `SAVI_API_KEY`) is set; otherwise synthetic.
- Budget enforcement is explicit in manifests: `stop_reason=budget_cap_reached_250.0`.
- No secrets are logged; manifests only include non-sensitive fields.
