$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$logDirectory = Join-Path $projectRoot 'logs'
$logPath = Join-Path $logDirectory 'simulator.log'

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Project virtual environment not found at $pythonPath. Recreate .venv and install requirements.txt."
}

New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
$env:SEMS_API_URL = 'https://sems-api-v3yn.onrender.com'
Set-Location -LiteralPath $projectRoot

"[$(Get-Date -Format s)] Starting SEMS simulator. API: $env:SEMS_API_URL" | Add-Content -LiteralPath $logPath
& $pythonPath -u -m simulator.simulate *>> $logPath
exit $LASTEXITCODE
