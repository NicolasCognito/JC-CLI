@echo off
setlocal enableextensions

REM Change to repo root (this script lives in utils\)
pushd "%~dp0.." >NUL

REM Safety check: ensure we're in the project root by checking for jc-cli.py
if not exist "jc-cli.py" (
  echo This script must be run within the project. jc-cli.py not found.
  popd
  exit /b 1
)

echo Clearing var directory...
if exist "var" (
  rmdir /s /q "var"
)

mkdir "var" 2>NUL

echo Done. var is now empty.
popd >NUL
endlocal

