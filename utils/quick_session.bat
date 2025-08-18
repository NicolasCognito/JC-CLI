@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Quick session launcher: random session with white and black
REM Can be run from anywhere; it cds to repo root.

REM Change to repo root (this script lives in utils\)
pushd "%~dp0.." >NUL

REM Generate a random session name
set SESSION=qs-%RANDOM%%RANDOM%
echo Starting quick session: %SESSION%

REM Start the session (spawns server in a new terminal) with UTF-8 mode
python -X utf8 -u jc-cli.py start-session %SESSION% default
if errorlevel 1 (
  echo Failed to start session %SESSION%.
  popd >NUL
  exit /b 1
)

REM Give the server a moment to come up
timeout /t 1 /nobreak >nul 2>nul

REM Join as two clients: black then white (each in a new terminal)
python -X utf8 -u jc-cli.py join-session %SESSION% player_black
python -X utf8 -u jc-cli.py join-session %SESSION% player_white

echo.
echo Launched server and clients for session: %SESSION%
echo Check the new terminals for connection status.

popd >NUL
exit /b 0
