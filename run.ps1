# run.ps1 - one-command local setup + launch for Project Overlord (Windows).
#
#   .\run.ps1            # create .venv, install deps, start the UI on :7860
#   .\run.ps1 -Test      # create .venv, install dev deps, run pytest, exit
#   .\run.ps1 -Docker    # build and run the container instead
param(
  [switch]$Test,
  [switch]$Docker,
  [int]$Port = 7860
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Get-Python {
  $candidates = @(
    @{ Exe = 'py'; Arg = '-3.13' },
    @{ Exe = 'py'; Arg = '-3.12' },
    @{ Exe = 'py'; Arg = '-3' },
    @{ Exe = 'python'; Arg = '' },
    @{ Exe = 'python3'; Arg = '' }
  )
  $prevEAP = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'   # py.exe writes "No suitable runtime" to stderr
  try {
    foreach ($c in $candidates) {
      if (-not (Get-Command $c.Exe -ErrorAction SilentlyContinue)) { continue }
      $probe = @()
      if ($c.Arg) { $probe += $c.Arg }
      $probe += @('-c', 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)')
      & $c.Exe @probe 1>$null 2>$null
      if ($LASTEXITCODE -eq 0) { return $c }
    }
  } finally {
    $ErrorActionPreference = $prevEAP
  }
  throw "Python 3.10+ not found on PATH."
}

if ($Docker) {
  docker build -t zerotouch-ap-auditor:local .
  docker run --rm -p "${Port}:7860" --env-file .env -v "${PWD}/workspace:/app/workspace" zerotouch-ap-auditor:local
  exit $LASTEXITCODE
}

$py = Get-Python
$venv = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venv)) {
  Write-Host "Creating virtualenv ..." -ForegroundColor Cyan
  if ($py.Arg) { & $py.Exe $py.Arg -m venv $venv } else { & $py.Exe -m venv $venv }
}
$vpy = Join-Path $venv "Scripts\python.exe"

Write-Host "Installing dependencies ..." -ForegroundColor Cyan
& $vpy -m pip install --upgrade pip --quiet
if ($Test) {
  & $vpy -m pip install -r requirements-dev.txt --quiet
  & $vpy -m pytest
  exit $LASTEXITCODE
}
& $vpy -m pip install -r requirements.txt --quiet

if (-not (Test-Path (Join-Path $PSScriptRoot ".env"))) {
  Copy-Item .env.example .env
  Write-Host "Created .env from .env.example - add GOOGLE_API_KEY and set OVERLORD_LIVE_LLM=1 for live Gemini." -ForegroundColor Yellow
}

$env:GRADIO_SERVER_PORT = "$Port"
Write-Host "Starting Project Overlord on http://127.0.0.1:$Port" -ForegroundColor Green
& $vpy app.py
