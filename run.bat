@echo off 
setlocal EnableExtensions

cd /d "%~dp0"

:: Required Python version
set "PYTHON_VERSION=3.13"
set "PYTHON_INSTALLER=3.13.0"

echo Checking for Python %PYTHON_VERSION%...
py -%PYTHON_VERSION% --version >nul 2>&1
if errorlevel 1 (
    echo Python not installed, downloading installer...
    powershell -c "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/%PYTHON_INSTALLER%/python-%PYTHON_INSTALLER%-amd64.exe' -OutFile '%TEMP%\python-%PYTHON_INSTALLER%.exe'"
    echo Launching installer. Be sure to add Python to PATH.
    "%TEMP%\python-%PYTHON_INSTALLER%.exe"
    pause
    echo Press any key after completing the installer.
) else (
    echo Python %PYTHON_VERSION% detected.
)

git pull origin main
git pull

if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found. Creating with Python %PYTHON_VERSION%...
    py -%PYTHON_VERSION% -m venv venv
    if errorlevel 1 (
        echo Failed to create venv. Ensure Python is installed and accessible.
        pause
        exit /b
    )
    echo Installing dependencies...
    call "venv\Scripts\activate.bat"
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if exist "venv\Scripts\deactivate.bat" call "venv\Scripts\deactivate.bat"
)

echo Activating virtual environment...
call "venv\Scripts\activate.bat" || (
    echo Failed to activate venv.
    pause
    exit /b
)

:: Ensure deps are present on every run (handles machines missing pydirectinput, etc.)
echo Ensuring dependencies are installed...
python -m pip install -r requirements.txt

echo Running main.py...
"venv\Scripts\python.exe" "%CD%\main.py"

echo Deactivating virtual environment...
if exist "venv\Scripts\deactivate.bat" call "venv\Scripts\deactivate.bat"

pause
endlocal
