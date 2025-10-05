@echo off
setlocal EnableExtensions
title Install Python 3.11 and 3.13
cd /d "%~dp0"

set "TARGETS=3.11 3.13"
set "TMPDIR=%TEMP%\py-multi-setup-%RANDOM%"
md "%TMPDIR%" 2>nul

where py >nul 2>&1
if errorlevel 1 echo Note: py.exe launcher not found yet. That’s OK.

for %%V in (%TARGETS%) do call :ensure_py %%V

echo.
echo Done. Press any key to close.
pause >nul
exit /b 0

:ensure_py
set "VER=%~1"
echo.
echo === Checking Python %VER% ===
py -%VER% --version >nul 2>&1 && (echo Found Python %VER%. & goto :eof)

rem Prefer winget if available
where winget >nul 2>&1
if not errorlevel 1 (
  echo Installing %VER% via winget...
  winget install -e --id Python.Python.%VER% -h
  if not errorlevel 1 goto verify
  echo winget failed. Falling back to python.org installer.
) else (
  echo winget not found. Using python.org installer.
)

set "PKG=python-%VER%.0-amd64.exe"
set "URL=https://www.python.org/ftp/python/%VER%.0/%PKG%"
echo Downloading %PKG%...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "[Net.ServicePointManager]::SecurityProtocol='Tls12,Tls13'; iwr '%URL%' -OutFile '%TMPDIR%\%PKG%'" || (
    echo Download failed for %VER%.
    goto :pauseerr
)

rem If admin, install for all users; else per-user
net session >nul 2>&1 && (
  set "FLAGS=/quiet InstallAllUsers=1 PrependPath=1 Include_launcher=1 Include_pip=1"
) || (
  set "FLAGS=/quiet PrependPath=1 Include_launcher=1 Include_pip=1"
)

echo Running installer...
"%TMPDIR%\%PKG%" %FLAGS%
if errorlevel 1 (
  echo Installer error for %VER%.
  goto :pauseerr
)

:verify
py -%VER% --version >nul 2>&1 && (
  echo Installed Python %VER%.
  goto :eof
) || (
  echo Python %VER% not on PATH yet. Open a new terminal and re-run if needed.
  goto :eof
)

:pauseerr
echo Press any key to continue with the next version...
pause >nul
goto :eof
