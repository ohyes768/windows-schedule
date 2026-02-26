@echo off
REM Python Task Scheduler Service Installation Script

echo ========================================
echo Python Task Scheduler Service Setup
echo ========================================
echo.

REM Check NSSM
where nssm >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: NSSM not found
    echo Please download NSSM and add to PATH
    echo Download: https://nssm.cc/download
    pause
    exit /b 1
)

REM Get script directory and resolve project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%~dp0..

REM Convert to absolute path
pushd "%PROJECT_ROOT%"
set PROJECT_ROOT=%CD%
popd

REM Create logs directory
if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"

REM Use global Python
set PYTHON_EXE=C:\python314\python.exe

REM Install service - Application and Parameters separately
echo Installing service...
nssm install PyTaskSched %PYTHON_EXE%
nssm set PyTaskSched AppParameters "-m src.scheduler"
nssm set PyTaskSched AppDirectory "%PROJECT_ROOT%"
nssm set PyTaskSched Description "Python Task Scheduler Service"
nssm set PyTaskSched Start SERVICE_AUTO_START

REM Configure logs
nssm set PyTaskSched AppStdout "%PROJECT_ROOT%\logs\scheduler_stdout.log"
nssm set PyTaskSched AppStderr "%PROJECT_ROOT%\logs\scheduler_stderr.log"

REM Configure restart policy
nssm set PyTaskSched AppExit Default Restart
nssm set PyTaskSched AppRestartDelay 10000

echo.
echo ========================================
echo Service installed successfully!
echo ========================================
echo.
echo Management commands:
echo   Start:   nssm start PyTaskSched
echo   Stop:    nssm stop PyTaskSched
echo   Restart: nssm restart PyTaskSched
echo   Status:  nssm status PyTaskSched
echo   Edit:    nssm edit PyTaskSched
echo   Remove:  nssm remove PyTaskSched confirm
echo.

pause
