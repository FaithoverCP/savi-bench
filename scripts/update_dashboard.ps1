param(
  [string]$RepoRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

try {
  if (-not $RepoRoot -or -not (Test-Path -LiteralPath $RepoRoot)) {
    $RepoRoot = Split-Path -Parent $PSScriptRoot
  }
  Set-Location -LiteralPath $RepoRoot

  $logDir = Join-Path $RepoRoot 'logs'
  if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $log   = Join-Path $logDir "run-$stamp.txt"

  function Write-Log([string]$msg) {
    $line = "[$(Get-Date -Format o)] $msg"
    $line | Tee-Object -FilePath $log -Append | Out-Null
  }

  function Run($exe, [string[]]$arguments) {
    Write-Log ">>> $exe $($arguments -join ' ')"
    & $exe @arguments 2>&1 | Tee-Object -FilePath $log -Append | Out-Null
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { Write-Log "exit=$LASTEXITCODE" }
  }

  Write-Log "SAVI update start"

  # Ensure local server is running
  $serverOk = $false
  try {
    Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8000/index.html' -TimeoutSec 5 | Out-Null
    $serverOk = $true
  } catch {
    Write-Log "http.server not responding; starting..."
    Start-Process -WindowStyle Hidden -FilePath 'python' -ArgumentList '-m','http.server','8000' -WorkingDirectory $RepoRoot | Out-Null
    Start-Sleep -Seconds 1
    try {
      Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8000/index.html' -TimeoutSec 5 | Out-Null
      $serverOk = $true
    } catch {
      $serverOk = $false
    }
  }
  Write-Log ("server=" + ($serverOk ? 'up' : 'down'))

  # Produce/update benchmark data
  Run 'python' @('-m','bench.run','--config','bench/config.json','--profile','savi_openai_62')
  Run 'python' @('-m','bench.run','--config','bench/config.json','--profile','savi_openai_63')
  Run 'python' @('-m','bench.report','--config','bench/config.json')

  Write-Log "SAVI update done"
} catch {
  $_ | Out-String | Tee-Object -FilePath $log -Append | Out-Null
  exit 1
}
