@echo off
chcp 65001 > nul
title PO提取系統啟動工具
color 0A

echo.
echo ==========================================
echo   PO 提取系統啟動工具
echo   Qwen3-VL 七步驟管線系統
echo ==========================================
echo.

REM 檢查 Python 是否安裝
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 找不到 Python，請先安裝 Python 3.8 以上版本
    echo 下載地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python 已安裝
echo.

REM 切換到正確的工作目錄
cd /d "%~dp0"

echo 📍 當前位置: %CD%
echo.

REM 檢查啟動檢查工具是否存在
if not exist "startup_checker.py" (
    echo ❌ 找不到 startup_checker.py
    echo 請確認檔案存在於當前目錄
    pause
    exit /b 1
)

echo 🚀 正在啟動系統檢查工具...
echo.

REM 運行啟動檢查工具
python startup_checker.py

echo.
echo ==========================================
if %errorlevel% equ 0 (
    echo ✅ 系統檢查完成
) else (
    echo ⚠️  系統檢查遇到問題
)
echo ==========================================
echo.

echo 按任意鍵結束...
pause > nul