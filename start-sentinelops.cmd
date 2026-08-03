@echo off
setlocal
cd /d "%~dp0"
title SentinelOps Nexus
set "SENTINELOPS_OPEN_BROWSER=1"

where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 scripts\ensure_dependencies.py
) else (
  python scripts\ensure_dependencies.py
)

if errorlevel 1 (
  echo.
  echo SentinelOps could not start. Review the error above.
  pause
  exit /b 1
)
