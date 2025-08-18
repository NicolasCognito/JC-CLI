@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Quick blast session: alice joins, sends 100x "raise 4", then bob joins
REM Usage: double-click or run from repo root

REM Generate a random session name if not provided
if "%~1"=="" (
  set SESSION=blast-%RANDOM%%RANDOM%
) else (
  set SESSION=%~1
)
echo Starting blast session: %SESSION%

REM Start the session (spawns server in a new terminal)
python -u jc-cli.py start-session %SESSION% default
if errorlevel 1 (
  echo Failed to start session %SESSION%.
  exit /b 1
)

REM Give the server a moment to come up
timeout /t 1 /nobreak >nul 2>nul

REM Join as alice first (new terminal)
python -u jc-cli.py join-session %SESSION% alice

REM Wait for alice's command queue file to appear
set QUEUE=var\clients\%SESSION%\alice\data\command_queue.txt
set /a _tries=0
:wait_queue
if exist "%QUEUE%" goto have_queue
set /a _tries+=1
if %_tries% GEQ 50 goto no_queue
timeout /t 1 /nobreak >nul 2>nul
goto wait_queue

:have_queue
echo Queue found: %QUEUE%

REM Append 10 raise commands quickly
for /L %%I in (1,1,10) do (
  >>"%QUEUE%" echo raise 4
)
echo Queued 10 commands for alice.

REM Small delay to let sequencer start chewing
timeout /t 2 /nobreak >nul 2>nul

REM Now join as bob
python -u jc-cli.py join-session %SESSION% bob

echo.
echo Launched server and clients for session: %SESSION%
echo Alice queued 10x "raise 4". Bob connected after.
exit /b 0

:no_queue
echo Timed out waiting for alice's command queue: %QUEUE%
echo You can run the commands manually once the file appears.
exit /b 1

