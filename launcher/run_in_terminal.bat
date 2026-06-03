@echo off
REM Open Windows Terminal and run jumperless (pipx app directly if installed).
setlocal EnableExtensions

set "HOME_DIR=%USERPROFILE%"
set "APP=%HOME_DIR%\pipx\venvs\jumperless\Scripts\jumperless.exe"
set "BOOTSTRAP=%~1"

if exist "%APP%" (
  where wt >nul 2>&1
  if %ERRORLEVEL%==0 (
    start "" wt.exe -w 0 -d "%HOME_DIR%" nt --hold --title "Jumperless" -- "%APP%"
    exit /b 0
  )
  start "Jumperless" cmd /k cd /d "%HOME_DIR%" ^&^& "%APP%"
  exit /b 0
)

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
  start "" wt.exe -w 0 -d "%HOME_DIR%" nt --hold --title "Jumperless" -- %PY_CMD% "%BOOTSTRAP%"
  exit /b 0
)

start "Jumperless" cmd /k cd /d "%HOME_DIR%" ^&^& %PY_CMD% "%BOOTSTRAP%"
exit /b 0
