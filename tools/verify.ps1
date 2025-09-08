Param(
  [string]$Dir = "."
)

Set-Location $Dir

if (-not (Test-Path .\sha256sums.txt)) { Write-Error "sha256sums.txt not found in $Dir"; exit 1 }

Write-Host "==> Expected (sha256sums.txt):"
Get-Content .\sha256sums.txt

Write-Host "`n==> Local hashes:"
$files = @("proof_pack_FULL.tgz","latency_summary.csv","latest.html")
foreach ($f in $files) {
  if (Test-Path ".\$f") {
    Get-FileHash ".\$f" -Algorithm SHA256 | Format-Table -Auto
  } else {
    Write-Host "(missing) $f"
  }
}

Write-Host "`nCompare the values above with sha256sums.txt (case-insensitive)."

