@echo off
title TRACE - Darknet & Encrypted Platform Drug Intelligence
color 0A
echo.
echo  ████████╗██████╗  █████╗ ████████╗███████╗
echo  ╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝██╔════╝
echo     ██║   ██████╔╝███████║   ██║   ███████╗
echo     ██║   ██╔══██╗██╔══██║   ██║   ╚════██║
echo     ██║   ██║  ██║██║  ██║   ██║   ███████║
echo     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝
echo.
echo  [Transnational Darknet & Encrypted Commerce Examiner]
echo  Chandigarh Police Hackathon 2026
echo  ─────────────────────────────────────────────────────
echo.

echo  Checking for existing server on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo  Found process %%a on port 8000 — terminating...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

echo.
echo  Installing dependencies...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install dependencies. Check Python/pip installation.
    pause
    exit /b 1
)
echo  [OK] Dependencies installed.
echo.
echo  Initializing database and generating demo data...
echo  Starting TRACE server...
echo  ─────────────────────────────────────────────────────
echo.

start "" http://localhost:8000
python app.py

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Server crashed. Check the error above.
    pause
    exit /b 1
)
pause
