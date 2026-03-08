@echo off
title RSI Scanner
chcp 65001 >nul
echo ========================================
echo A 股市场 RSI 筛选工具
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo Starting RSI Scanner (Lite Version)...
echo.
echo 提示：
echo - 如需可视化功能，请先安装 matplotlib
echo - 运行：pip install matplotlib
echo.

python rsi_scanner_lite.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo Error occurred
    echo ========================================
    echo.
    echo Please run: python setup.py
    echo to install dependencies first
    echo.
    pause
)
