@echo off
REM ========================================
REM RCA Scheduler - Windows Batch File
REM ========================================
REM This script runs the RCA scheduler
REM Schedule this with Windows Task Scheduler

cd /d C:\Users\40020358\Downloads\RCA_agent-main\RCA_agent-main

REM Activate virtual environment (if exists)
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the scheduler
python rca_scheduler.py

REM Log completion
echo [%date% %time%] RCA Scheduler completed >> logs\scheduler_runs.log
