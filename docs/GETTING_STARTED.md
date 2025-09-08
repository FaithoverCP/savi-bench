# SAVI Bench — Getting Started (DS005 replay)

This guide explains how to set up the repo, run capped + 10k scenarios, and verify integrity.

## Setup (Windows PowerShell)

```powershell
Set-Location "$HOME\Documents"
git clone https://github.com/FaithoverCP/savi-bench.git
Set-Location .\savi-bench

# Python 3.11 virtual env
py -3.11 -m venv .venv
 .\.venv\Scripts\Activate.ps1

pip install --upgrade pip
# Optional utilities if your adapter uses them:
pip install requests
# If your config is YAML-based:
# pip install pyyaml

# Sanity check
Test-Path bench\run.py  # should return True
```

## API Config

If you’re using OpenAI profiles (savi_openai_*), set:

```powershell
Set-Item Env:OPENAI_API_KEY  "sk-...real-key..."
# Optional for custom gateways:
# Set-Item Env:OPENAI_BASE_URL "https://api.openai.com/v1"
```

If you use custom names like SAVI_API_BASE / SAVI_API_KEY / SAVI_MODEL, the built-in adapter also supports them.

## Replay — capped run (DS005)

```powershell
python -m bench.run --config bench/config.json --profile savi_openai_1000 --budget-usd 250
python -m bench.report results/latest.jsonl --out reports/latest.html
# Check manifests\run-*.json for:
#  "total_cost_usd": ...,
#  "stop_reason": "budget_cap_reached_250.0"
```

## Full 10k Scenario (pods 10 × size 1000)

```powershell
python -m bench.run --config bench/config.json --profile savi_openai_1000 `
  --set pods.count=10 --set pods.size=1000 --set concurrency=256 `
  --budget-usd 250

python -m bench.report results/latest.jsonl --out reports/latest.html
```

## Integrity Check (Windows)

Download from the GitHub Release:

- proof_pack_FULL.tgz
- sha256sums.txt
- latency_summary.csv
- latest.html

Then:

```powershell
Set-Location "C:\\Path\\To\\Your\\Download\\Folder"

Get-FileHash .\proof_pack_FULL.tgz -Algorithm SHA256
Get-FileHash .\latency_summary.csv -Algorithm SHA256
Get-FileHash .\latest.html         -Algorithm SHA256
Get-Content   .\sha256sums.txt
```

Compare the printed hashes to the expected values in sha256sums.txt.
Case-insensitive match = integrity confirmed.

## Troubleshooting

- Activation blocked: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
- Wrong Python: ensure `py -3.11` and your prompt shows `(.venv)`
- Missing API vars: set `OPENAI_API_KEY` (and optionally `OPENAI_BASE_URL`)
- Concurrency flag: always use `--set concurrency=...`

