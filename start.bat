@echo off
setlocal

set ROOT_DIR=%~dp0
set VENV_DIR=%ROOT_DIR%.venv
set MARKER_FILE=%VENV_DIR%\.cindergrace_git_gui_installed

set REFRESH=0
set NO_DEV=0

:parse
if "%~1"=="" goto after_parse
if "%~1"=="--refresh" set REFRESH=1
if "%~1"=="--no-dev" set NO_DEV=1
if "%~1"=="--help" goto usage
if "%~1"=="-h" goto usage
shift
goto parse

:usage
echo Usage: start.bat [--refresh] [--no-dev]
echo.
echo Options:
echo   --refresh   Reinstall dependencies even if already installed
echo   --no-dev    Install only runtime dependencies (skip dev extras)
exit /b 0

:after_parse
if not exist "%VENV_DIR%" (
  echo Creating venv...
  python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"

if not exist "%MARKER_FILE%" (
  set NEED_INSTALL=1
) else (
  set NEED_INSTALL=%REFRESH%
)

if "%NEED_INSTALL%"=="1" (
  echo Installing dependencies...
  python -m pip install --upgrade pip
  if "%NO_DEV%"=="1" (
    python -m pip install -e .
  ) else (
    python -m pip install -e .[dev]
  )
  echo.> "%MARKER_FILE%"
)

python main.py
