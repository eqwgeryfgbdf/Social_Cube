@echo off
REM Branch and Script Verification and Backup Runner
REM This batch file runs the verification and backup process in either Python or PowerShell

echo Branch and Script Verification and Backup for Social Cube Project
echo ===============================================================
echo.

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Found Python, running Python verification script...
    python scripts\verify_and_backup.py
    goto :end
)

REM Otherwise try PowerShell
where powershell >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Found PowerShell, running PowerShell verification script...
    powershell -ExecutionPolicy Bypass -File scripts\verify_and_backup.ps1
    goto :end
)

echo ERROR: Neither Python nor PowerShell was found.
echo Please install either Python or PowerShell to run this verification script.

:end
echo.
echo Verification process complete.
echo If successful, you should now have these files:
echo - docs/verification_report.md (Detailed verification report)
echo - backup/cleanup_backup/      (Backup directory with all branches and scripts)
echo.
pause