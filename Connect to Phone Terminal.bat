@echo off
title Filvora - Redmi Note 8 Pro Terminal Bridge
color 0A
cd /d "%~dp0"

:: =========================================================================
:: FILVORA MOBILE SERVER CREDENTIALS CONFIGURATION
:: Edit your Termux username and password below:
:: =========================================================================
set PHONE_IP=192.168.1.50
set SSH_PORT=8022
set SSH_USER=u0_a256
set SSH_PASS=1234
:: =========================================================================

:MENU
cls
echo.
echo  ====================================================================
echo              FILVORA MOBILE SERVER - REMOTE TERMINAL BRIDGE          
echo  ====================================================================
echo.
echo    [DEVICE]    : Xiaomi Redmi Note 8 Pro (MIUI 12.5.10 / Android 11)
echo    [SERVER IP] : %PHONE_IP%
echo    [SSH PORT]  : %SSH_PORT%
echo    [USERNAME]  : %SSH_USER%
echo    [PASSWORD]  : %SSH_PASS%
echo    [WEB APP]   : http://%PHONE_IP%:8000/
echo.
echo  ====================================================================
echo   CHOOSE AN ACTION:
echo  ====================================================================
echo.
echo   [1] Connect to Phone Terminal Shell (Interactive SSH)
echo   [2] Stream Live Filvora Logs (Real-time traffic & clicks)
echo   [3] Check Recent Errors & Crashes (grep error/500)
echo   [4] Open Filvora in Browser (http://%PHONE_IP%:8000/)
echo   [5] Edit Saved Credentials (Username / Password)
echo   [6] Exit
echo.
set /p opt=" Select Option (1-6) and press Enter: "

if "%opt%"=="1" goto SSH_SHELL
if "%opt%"=="2" goto STREAM_LOGS
if "%opt%"=="3" goto CHECK_ERRORS
if "%opt%"=="4" goto OPEN_BROWSER
if "%opt%"=="5" goto EDIT_CREDS
if "%opt%"=="6" exit /b 0

goto MENU

:SSH_SHELL
cls
echo.
echo  [*] Connecting to %SSH_USER%@%PHONE_IP% on port %SSH_PORT%...
echo  [*] Reminder - Your Password is: %SSH_PASS%
echo.
ssh -p %SSH_PORT% %SSH_USER%@%PHONE_IP%
pause
goto MENU

:STREAM_LOGS
cls
echo.
echo  [*] Streaming live Filvora logs from phone (Press Ctrl+C to stop)...
echo.
ssh -t -p %SSH_PORT% %SSH_USER%@%PHONE_IP% "tail -f ~/filvora.log"
pause
goto MENU

:CHECK_ERRORS
cls
echo.
echo  [*] Checking for errors in ~/filvora.log...
echo.
ssh -t -p %SSH_PORT% %SSH_USER%@%PHONE_IP% "grep -iE 'error|exception|traceback|500' ~/filvora.log || echo 'No errors found in filvora.log! All clean.'"
echo.
pause
goto MENU

:OPEN_BROWSER
start http://%PHONE_IP%:8000/
goto MENU

:EDIT_CREDS
cls
echo.
echo  ====================================================================
echo                    UPDATE SAVED PHONE CREDENTIALS                    
echo  ====================================================================
echo.
echo  On your phone in Termux, run 'whoami' to see your exact username.
echo.
set /p new_user=" Enter your Termux username (current: %SSH_USER%): "
if not "%new_user%"=="" set SSH_USER=%new_user%
set /p new_pass=" Enter your Termux password (current: %SSH_PASS%): "
if not "%new_pass%"=="" set SSH_PASS=%new_pass%
echo.
echo  [OK] Updated in this session.
timeout /t 2 >nul
goto MENU
