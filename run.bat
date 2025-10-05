@echo off
setlocal EnableExtensions

:: Always run relative to this script’s folder
cd /d "%~dp0"

:: Specify the required Python version
set "PYTHON_VERSION=3.11"

:: Check if Python 3.11 is installed
echo Checking for Python %PYTHON_VERSION%...
py -%PYTHON_VERSION% --version >nul 2>&1
if errorlevel 1 (
    :: python is not installed
    echo Python not installed, downloading installer...
    powershell -c "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.1/python-3.11.1-amd64.exe' -OutFile '%USERPROFILE%\AppData\Local\Temp\python-3.11.1.exe'"
    echo Launching installer, please make sure to follow the correct setup instructions Adding python to environment variables!
    echo:

    "%USERPROFILE%\AppData\Local\Temp\python-3.11.1.exe"
    pause
    echo Please press any button once you have completed the python setup, so we can continue installing the depedencies.
) else (
    echo Python is already installed. Please make sure its of version 3.10 or higher, using an older version will NOT work!
)

:: Pull updates from Git
git pull origin main
git pull

:: Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found. Creating a new one using Python %PYTHON_VERSION%...
    py -%PYTHON_VERSION% -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment with Python %PYTHON_VERSION%. Ensure Python is installed and accessible.
        pause
        exit /b
    )
    echo Virtual environment created successfully.

    :: Install dependencies immediately after creating the venv
    echo Installing dependencies from requirements.txt...
    call "venv\Scripts\activate.bat"
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if exist "venv\Scripts\deactivate.bat" call "venv\Scripts\deactivate.bat"
)

:: Activate the virtual environment
echo Activating virtual environment...
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment. Please activate it manually using:
    echo venv\Scripts\activate
    pause
    exit /b
)

:: Run the main Python script using the venv interpreter
echo Running main.py...
"venv\Scripts\python.exe" "%CD%\main.py"

:: Deactivate virtual environment
echo Deactivating virtual environment...
if exist "venv\Scripts\deactivate.bat" call "venv\Scripts\deactivate.bat"

pause
endlocal
