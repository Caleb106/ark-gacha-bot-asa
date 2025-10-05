@echo off
setlocal EnableExtensions
cd /d "%~dp0"

:: ---- config ----
set "PYTHON_VERSION=3.13"
set "VENV_DIR=venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "REQ_FILE=requirements.txt"
set "REQ_STAMP=%VENV_DIR%\requirements.sha256"

:: ---- ensure Python ----
echo Checking for Python %PYTHON_VERSION%...
py -%PYTHON_VERSION% --version >NUL 2>&1
if errorlevel 1 (
  echo Python %PYTHON_VERSION% not found. Using default "py" or "python".
  where py >NUL 2>&1 || where python >NUL 2>&1 || (
    echo No Python found on PATH. Install Python and re-run setup.
    pause
    exit /b 1
  )
) else (
  echo Python %PYTHON_VERSION% detected.
)

:: ---- compute requirements hash ----
if not exist "%REQ_FILE%" (
  echo %REQ_FILE% not found.
  pause
  exit /b 1
)

for /f "skip=1 tokens=* delims=" %%H in ('certutil -hashfile "%REQ_FILE%" SHA256 ^| findstr /v /i "hash of file CertUtil"') do (
  if not defined REQ_HASH set "REQ_HASH=%%H"
)
if not defined REQ_HASH (
  echo Failed to compute hash for %REQ_FILE%.
  pause
  exit /b 1
)
set "REQ_HASH=%REQ_HASH: =%"

:: ---- check if everything is already installed ----
if exist "%VENV_PY%" if exist "%REQ_STAMP%" (
  set /p CUR_HASH=<"%REQ_STAMP%"
  if /i "%CUR_HASH%"=="%REQ_HASH%" (
    echo Environment OK. Nothing to do.
    echo Press any key to exit.
    pause >NUL
    exit /b 0
  )
)

:: ---- (re)build environment ----
if exist "%VENV_DIR%" (
  echo Removing old virtual environment...
  rmdir /s /q "%VENV_DIR%"
)

echo Creating virtual environment...
py -%PYTHON_VERSION% -m venv "%VENV_DIR%" 2>NUL || py -m venv "%VENV_DIR%" 2>NUL || python -m venv "%VENV_DIR%"
if not exist "%VENV_PY%" (
  echo Failed to create venv.
  pause
  exit /b 1
)

echo Installing dependencies...
"%VENV_PY%" -m pip install --upgrade pip
"%VENV_PY%" -m pip install -r "%REQ_FILE%"
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)

> "%REQ_STAMP%" echo %REQ_HASH%

echo Setup complete. Press any key to exit.
pause >NUL
exit /b 0
