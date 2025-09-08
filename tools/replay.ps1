Param(
  [string]$Profile = "savi_openai_1000",
  [double]$Budget = 250.0,
  [string]$Config = "bench/config.json"
)

Write-Host "==> Activating venv"
if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
  Write-Error "Virtual env not found. Run setup steps first."
  exit 1
}
. .\.venv\Scripts\Activate.ps1

Write-Host "==> Running bench (capped)"
python -m bench.run --config $Config --profile $Profile --budget-usd $Budget
if ($LASTEXITCODE -ne 0) { Write-Error "bench.run failed"; exit 1 }

Write-Host "==> Building report"
python -m bench.report results/latest.jsonl --out reports/latest.html
if ($LASTEXITCODE -ne 0) { Write-Error "bench.report failed"; exit 1 }

Write-Host "==> Done. Check manifests/run-*.json for total_cost_usd & stop_reason."

