@echo off
echo ======================================================================
echo   Starting Paytm ResolveAI (Autonomous Merchant Resolution Teammate)
echo ======================================================================
echo.

echo Starting FastAPI Backend on http://localhost:8000 ...
start "ResolveAI Backend" cmd /k "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak > nul

echo Starting Vite Frontend on http://localhost:5173 ...
start "ResolveAI Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are launching!
echo Backend API Docs: http://localhost:8000/docs
echo Frontend Console: http://localhost:5173
echo.
pause

