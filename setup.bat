@echo off
setlocal EnableExtensions
cd /d "%~dp0"

:: ---- config ----
set "PYTHON_VERSION=3.13"
set "VENV_DIR=venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "REQ_FILE=requirements.txt"
set "REQ_STAMP=%VENV_DIR%\requirements.sha256"

:: ---- compute requirements hash (PowerShell, fallback to certutil) ----
set "REQ_HASH="
for /f %%H in ('powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 ''%REQ_FILE%'' ).Hash" 2^>NUL') do set "REQ_HASH=%%H"
if not defined REQ_HASH (
  for /f "skip=1 tokens=* delims=" %%H in ('certutil -hashfile "%REQ_FILE%" SHA256 ^| findstr /r /v /c:"^$" /c:"hash of file" /c:"CertUtil"') do if not defined REQ_HASH set "REQ_HASH=%%H"
)
if not defined REQ_HASH (
  echo Failed to compute hash for %REQ_FILE%.
  pause & exit /b 1
)
set "REQ_HASH=%REQ_HASH: =%"

:: ---- fast path: venv exists and matches requirements ----
if exist "%VENV_PY%" if exist "%REQ_STAMP%" (
  set /p CUR_HASH=<"%REQ_STAMP%"
  if /i "%CUR_HASH%"=="%REQ_HASH%" (
    echo Environment OK. Nothing to do.
    echo Press any key to exit.
    pause >NUL
    exit /b 0
  )
)

:: ---- ensure Python ----
echo Checking for Python %PYTHON_VERSION%...
py -%PYTHON_VERSION% --version >NUL 2>&1
if errorlevel 1 (
  echo Python %PYTHON_VERSION% not found. Will use default py/python.
  where py >NUL 2>&1 || where python >NUL 2>&1 || (
    echo No Python found on PATH. Install Python and re-run setup.
    pause & exit /b 1
  )
) else (
  echo Python %PYTHON_VERSION% detected.
)

:: ---- rebuild environment (only when missing or requirements changed) ----
if exist "%VENV_DIR%" (
  echo Removing old virtual environment...
  rd /s /q "%VENV_DIR%"
)

echo Creating virtual environment...
py -%PYTHON_VERSION% -m venv "%VENV_DIR%" 2>NUL || py -m venv "%VENV_DIR%" 2>NUL || python -m venv "%VENV_DIR%"
if not exist "%VENV_PY%" (
  echo Failed to create venv.
  pause & exit /b 1
)

echo Installing dependencies...
"%VENV_PY%" -m pip install --upgrade pip
"%VENV_PY%" -m pip install -r "%REQ_FILE%"
if errorlevel 1 (
  echo Dependency installation failed.
  pause & exit /b 1
)

> "%REQ_STAMP%" echo %REQ_HASH%

echo Setup complete. Press any key to exit.
pause >NUL
exit /b 0
