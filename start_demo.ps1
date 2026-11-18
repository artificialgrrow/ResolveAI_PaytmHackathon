Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Starting Paytm QR Armor (Autonomous Merchant QR Provenance Agent)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$pythonCmd = "python"
if (Test-Path "venv\Scripts\python.exe") {
    $pythonCmd = "..\venv\Scripts\python.exe"
} elseif (Test-Path "venv\bin\python") {
    $pythonCmd = "..\venv\bin\python"
}

Write-Host "Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; $pythonCmd -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

Start-Sleep -Seconds 2

Write-Host "Starting Vite Frontend on http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host ""
Write-Host "Both servers are launching!" -ForegroundColor Yellow
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Swagger Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Frontend Console: http://localhost:5173" -ForegroundColor White
Write-Host ""
