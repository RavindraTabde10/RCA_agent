@echo off
REM ========================================
REM Test RCA with GitHub PR Creation
REM ========================================
REM This test demonstrates the complete
REM workflow: RCA Analysis + Code Fix + PR

REM Change to the directory where this batch file is located
cd /d "%~dp0"

REM Activate virtual environment (if exists)
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo.
echo ============================================================
echo   RCA ENGINE TEST WITH GITHUB PR CREATION
echo ============================================================
echo.
echo This will:
echo   1. Analyze a defect using RCA
echo   2. Generate a code fix based on root cause
echo   3. Create a GitHub Pull Request with the fix
echo   4. Show live updates in dashboard
echo.
echo Dashboard: http://localhost:5050
echo.

REM Run the test
python test_rca_with_pr.py %*

pause
