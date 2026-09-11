@echo off
title Filvora - Automated Master Test Runner
color 0B
cd /d "%~dp0"

cls
echo.
echo  ======================================================================
echo                 FILVORA MASTER AUTOMATED TEST RUNNER                 
echo  ======================================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo  [ERROR] Python virtual environment not found!
    echo  Expected: %~dp0venv\Scripts\python.exe
    echo.
    echo  Please ensure the virtual environment exists.
    echo.
    pause
    exit /b 1
)

echo  [*] Python Environment: OK
echo  [*] Launching Master Test Suite across 7 active subsystems (122 tests)...
echo.

venv\Scripts\python.exe run_all_tests.py %*

echo.
pause
