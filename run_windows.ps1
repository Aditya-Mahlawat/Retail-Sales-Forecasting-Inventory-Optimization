# Windows PowerShell Launch Script for NexStock Enterprise Suite
Write-Host "Starting NexStock Enterprise Platform..." -ForegroundColor Cyan

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

.\.venv\Scripts\Activate.ps1
Write-Host "Checking dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

Write-Host "Starting FastAPI Backend on port 8001..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", ".\.venv\Scripts\Activate.ps1; python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload"

Start-Sleep -Seconds 3

Write-Host "Starting Streamlit Executive Dashboard on port 8501..." -ForegroundColor Green
streamlit run frontend/app.py --server.port 8501
