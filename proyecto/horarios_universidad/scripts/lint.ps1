Set-Location "$PSScriptRoot\..\backend"
& ".\.venv\Scripts\Activate.ps1"
Write-Host "=== Ruff check ===" -ForegroundColor Cyan
ruff check app/
Write-Host "=== Ruff format ===" -ForegroundColor Cyan
ruff format app/
