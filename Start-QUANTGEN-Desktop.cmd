@echo off
setlocal
cd /d "%~dp0"
set "QG_DESKTOP_PY=%LOCALAPPDATA%\QUANTGEN\venv\Scripts\python.exe"
if exist "%~dp0.venv\Scripts\python.exe" set "QG_DESKTOP_PY=%~dp0.venv\Scripts\python.exe"
if not exist "%QG_DESKTOP_PY%" (
  echo QUANTGEN Python environment was not found.
  echo From this folder, create .venv and install the desktop extra:
  echo   py -m venv .venv
  echo   .venv\Scripts\python.exe -m pip install ".[desktop]"
  pause
  exit /b 1
)
"%QG_DESKTOP_PY%" -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
  echo Install the desktop extra in your existing QUANTGEN environment:
  echo   "%QG_DESKTOP_PY%" -m pip install ".[desktop]"
  pause
  exit /b 1
)
"%QG_DESKTOP_PY%" -m quantgen_desktop
if errorlevel 1 (
  echo QUANTGEN exited with an error. Keep the message above for diagnosis.
  pause
  exit /b 1
)
endlocal
