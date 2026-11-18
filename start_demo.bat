@echo off
echo ======================================================================
echo   Starting Paytm QR Armor (Autonomous Merchant QR Provenance Agent)
echo ======================================================================
echo.

set PYTHON_CMD=python
if exist "venv\Scripts\python.exe" (
    set PYTHON_CMD=..\venv\Scripts\python.exe
) else if exist "venv\bin\python" (
    set PYTHON_CMD=..\venv\bin\python
)

echo Starting FastAPI Backend on http://localhost:8000 ...
start "Paytm QR Armor Backend" cmd /k "cd backend && %PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak > nul

echo Starting Vite Frontend on http://localhost:5173 ...
start "Paytm QR Armor Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are launching!
echo Backend API Docs: http://localhost:8000/docs
echo Frontend Console: http://localhost:5173
echo.
pause
