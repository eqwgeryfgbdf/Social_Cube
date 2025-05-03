@echo off
REM Branch and Script Analyzer Runner
REM This batch file runs the branch and script analyzer in either Python or PowerShell

echo Branch and Script Analyzer for Social Cube Project
echo ==================================================
echo.

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Found Python, running Python analyzer...
    python scripts\branch_script_analyzer.py
    goto :end
)

REM Otherwise try PowerShell
where powershell >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Found PowerShell, running PowerShell analyzer...
    powershell -ExecutionPolicy Bypass -File scripts\branch_script_analyzer.ps1
    goto :end
)

echo ERROR: Neither Python nor PowerShell was found.
echo Please install either Python or PowerShell to run this analyzer.

:end
echo.
echo Analysis process complete.
echo If successful, you should now have these files in the project root:
echo - branch_inventory.csv
echo - script_inventory.csv
echo - cleanup_inventory.md
echo.
pause