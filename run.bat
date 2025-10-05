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
    "%TEMP%\python-%PYTHON_INSTALLER%.exe"
    pause
)

git pull origin main
git pull

:: Create venv if missing
if not exist "venv\Scripts\python.exe" (
    echo Creating venv with Python %PYTHON_VERSION%...
    py -%PYTHON_VERSION% -m venv venv
)

:: Recreate venv if using the wrong Python
for /f "delims=" %%v in ('"venv\Scripts\python.exe" -c "import sys;print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set "VENV_VER=%%v"
if not "%VENV_VER%"=="%PYTHON_VERSION%" (
    echo venv Python %VENV_VER% != %PYTHON_VERSION%. Recreating...
    rmdir /s /q venv
    py -%PYTHON_VERSION% -m venv venv
)

echo Activating virtual environment...
call "venv\Scripts\activate.bat" || ( echo Failed to activate venv.& pause & exit /b )

echo Ensuring dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo Running main.py...
"venv\Scripts\python.exe" "%CD%\main.py"

echo Deactivating virtual environment...
if exist "venv\Scripts\deactivate.bat" call "venv\Scripts\deactivate.bat"
pause
endlocal
