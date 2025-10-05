@echo off
setlocal EnableExtensions
cd /d "%~dp0"

:: Target Python
set "PYTHON_VERSION=3.13"
set "PYTHON_INSTALLER=3.13.0"

cd

>nul 2>nul assoc .py
if errorlevel 1 (
    echo Python not installed, downloading installer...
    powershell -c "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/%PYTHON_INSTALLER%/python-%PYTHON_INSTALLER%-amd64.exe' -OutFile '%TEMP%\python-%PYTHON_INSTALLER%.exe'"
    echo Launching installer. Be sure to add Python to PATH.
    "%TEMP%\python-%PYTHON_INSTALLER%.exe"
    pause
    echo Press any key after completing the installer.
) else (
    echo Python is installed. Use %PYTHON_VERSION% or newer.
)

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -%PYTHON_VERSION% -m venv venv 2>nul || py -m venv venv || python -m venv venv
    if errorlevel 1 (
        echo Failed to create venv.
        pause
        exit /b
    )
    echo venv created.
)

echo Installing dependencies in venv...
call "venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo Finished installing dependencies.
if exist "venv\Scripts\deactivate.bat" call "venv\Scripts\deactivate.bat"

echo Setup finished.
pause
endlocal
