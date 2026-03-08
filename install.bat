@echo off
title RSI Scanner - Install
chcp 65001 >nul
echo ========================================
echo A 股市场 RSI 筛选工具 - Install
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo Installing dependencies...
echo.
python setup.py

echo.
echo ========================================
echo Done!
echo ========================================
echo.
echo Run 'run.bat' to start the program
echo.
pause
