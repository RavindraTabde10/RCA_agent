@echo off
REM ========================================
REM RCA Scheduler - Windows Batch File
REM ========================================
REM This script runs the RCA scheduler
REM Schedule this with Windows Task Scheduler

REM Change to the directory where this batch file is located
cd /d "%~dp0"

REM Activate virtual environment (if exists)
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Create logs directory if not exists
if not exist "logs" mkdir logs

REM Run the scheduler
python rca_scheduler.py %*

REM Log completion
echo [%date% %time%] RCA Scheduler completed >> logs\scheduler_runs.log
