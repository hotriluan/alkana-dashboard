@echo off
REM Alkana Dashboard - One-Click Deployment for Windows
REM This batch script guides you through the deployment process

echo.
echo ==========================================
echo   Alkana Dashboard - Windows Deployment
echo ==========================================
echo.
echo This script will guide you through deployment.
echo.
echo OPTION 1 (Recommended): Use Git Bash
echo   1. Right-click in this folder
echo   2. Select "Git Bash Here"
echo   3. Run: bash deployment/one-click-deploy-windows.sh
echo.
echo OPTION 2: Manual PowerShell Guide
echo   Run: powershell -ExecutionPolicy Bypass -File deployment\one-click-deploy.ps1
echo.
echo OPTION 3: Continue with this batch script
echo.
set /p choice="Choose option (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo Opening Git Bash...
    start "" "C:\Program Files\Git\git-bash.exe" --cd="%CD%"
    echo.
    echo Run this command in Git Bash:
    echo   bash deployment/one-click-deploy-windows.sh
    echo.
    pause
    exit /b 0
)

if "%choice%"=="2" (
    echo.
    echo Starting PowerShell guide...
    powershell -ExecutionPolicy Bypass -File "%~dp0one-click-deploy.ps1"
    exit /b 0
)

if "%choice%"=="3" (
    echo.
    echo ==========================================
    echo Step 1: Test SSH Connection
    echo ==========================================
    echo.
    echo Run this command:
    echo   ssh alkana@192.168.68.166
    echo.
    echo Password: alkana123
    echo.
    echo If it works, type 'exit' to disconnect and continue.
    echo.
    pause
    
    echo.
    echo ==========================================  
    echo Step 2: Upload Files to Server
    echo ==========================================
    echo.
    echo Run this command:
    echo   scp -r . alkana@192.168.68.166:~/alkana-dashboard/
    echo.
    pause
    
    echo.
    echo For full deployment steps, see: deployment\WINDOWS-USERS.md
    echo.
    pause
    exit /b 0
)

echo.
echo Invalid choice. Exiting.
pause
