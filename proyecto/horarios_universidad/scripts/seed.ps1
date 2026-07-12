Set-Location "$PSScriptRoot\..\backend"
& ".\.venv\Scripts\Activate.ps1"
python -m scripts.seed_auth
