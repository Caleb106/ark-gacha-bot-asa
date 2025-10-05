@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV_PY=venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
  echo No virtual environment found. Running setup...
  call "%~dp0setup.bat"
  if not exist "%VENV_PY%" (
    echo Setup failed or cancelled.
    pause & exit /b 1
  )
)

"%VENV_PY%" "%CD%\main.py"
exit /b %errorlevel%
