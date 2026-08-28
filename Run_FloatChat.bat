@echo off
setlocal
cd /d "%~dp0"
title FloatChat Launcher

powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing http://localhost:8502 -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
if not errorlevel 1 (
    start "FloatChat" http://localhost:8502
    exit /b 0
)

if not exist ".venv\Scripts\python.exe" (
    echo FloatChat environment not found. Creating it now...
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python was not found. Install Python 3.10 or newer and try again.
        pause
        exit /b 1
    )
    python -m venv .venv
    if errorlevel 1 (
        echo Could not create the virtual environment.
        pause
        exit /b 1
    )
)

if not exist ".venv\Scripts\streamlit.exe" (
    echo Installing FloatChat dependencies. This happens only once...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency installation failed.
        pause
        exit /b 1
    )
)

echo Starting FloatChat...
start "FloatChat Server" /D "%~dp0" "%~dp0.venv\Scripts\python.exe" -m streamlit run "%~dp0app.py" --server.headless true --server.address 127.0.0.1 --server.port 8502 --browser.gatherUsageStats false

:wait_for_server
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8502 -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_for_server
)
where msedge >nul 2>nul
if not errorlevel 1 (
    start "FloatChat" http://127.0.0.1:8502
) else (
    start "FloatChat" http://127.0.0.1:8502
)
exit /b 0
endlocal
