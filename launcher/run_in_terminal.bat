@echo off
REM Open Windows Terminal (or cmd) and run the uv bootstrap, which installs/
REM upgrades jumperless from PyPI via uv and then launches it.
setlocal EnableExtensions

set "BOOTSTRAP=%~1"

if not exist "%BOOTSTRAP%" (
  echo Bootstrap script not found: %BOOTSTRAP%
  pause
  exit /b 1
)

set "PY_CMD="
where py >nul 2>&1
if %ERRORLEVEL%==0 set "PY_CMD=py -3"
if not defined PY_CMD (
  where python3 >nul 2>&1
  if %ERRORLEVEL%==0 set "PY_CMD=python3"
)
if not defined PY_CMD (
  where python >nul 2>&1
  if %ERRORLEVEL%==0 set "PY_CMD=python"
)
if not defined PY_CMD (
  echo Python not found. Install from https://www.python.org/downloads/
  pause
  exit /b 1
)

where wt >nul 2>&1
if %ERRORLEVEL%==0 (
  start "" wt.exe -w 0 -d "%USERPROFILE%" nt --hold --title "Jumperless" -- %PY_CMD% "%BOOTSTRAP%"
  exit /b 0
)

start "Jumperless" cmd /k cd /d "%USERPROFILE%" ^&^& %PY_CMD% "%BOOTSTRAP%"
exit /b 0
