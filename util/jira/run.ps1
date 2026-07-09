# PowerShell script to run Python scripts with virtual environment
# Usage: .\run.ps1 script_name.py

$venvPath = "e:\ltts_hackathon_work\venv\Scripts"
$pythonExe = Join-Path $venvPath "python.exe"

if ($args.Count -eq 0) {
    Write-Host "Virtual Environment Python: $pythonExe" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage examples:" -ForegroundColor Yellow
    Write-Host "  .\run.ps1 setup_check.py"
    Write-Host "  .\run.ps1 jira_automation.py"
    Write-Host "  .\run.ps1 jira_operations.py"
    Write-Host ""
    Write-Host "Installed packages:" -ForegroundColor Cyan
    & $pythonExe -m pip list
} else {
    & $pythonExe $args
}
