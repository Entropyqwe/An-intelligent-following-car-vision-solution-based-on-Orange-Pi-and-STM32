$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
Write-Host 'Creating a project environment with Python 3.12...'
& py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 first. See README.' }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed' }
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency install failed; copy the full error to your assistant.' }
& .\.venv\Scripts\python.exe verify_models.py
if ($LASTEXITCODE -ne 0) { throw 'Model verification failed.' }
Write-Host 'Ready. In VS Code select .venv\Scripts\python.exe and run camera_check.py.'
