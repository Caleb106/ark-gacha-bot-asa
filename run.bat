@echo off
setlocal

echo Pulling latest updates...
git pull

if not exist "venv" (
    echo Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b
)
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment. Try running setup.bat again.
    pause
    exit /b
)
echo.

echo Running main.py...
echo.
python main.py

echo Deactivating virtual environment...
call venv\Scripts\deactivate.bat

pause