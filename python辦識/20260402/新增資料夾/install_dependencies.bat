@echo off
chcp 65001 > nul
title PO系統相依套件安裝工具
color 0B

echo.
echo ==========================================
echo   PO 提取系統相依套件安裝工具
echo ==========================================
echo.

REM 檢查 Python 和 pip
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 找不到 Python
    pause
    exit /b 1
)

pip --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 找不到 pip
    pause
    exit /b 1
)

echo ✅ Python 和 pip 已準備就緒
echo.

REM 切換到腳本目錄
cd /d "%~dp0"

REM 檢查 requirements.txt 是否存在
if not exist "requirements.txt" (
    echo ❌ 找不到 requirements.txt
    pause
    exit /b 1
)

echo 📦 正在安裝相依套件...
echo.

REM 升級 pip 到最新版本
python -m pip install --upgrade pip

echo.
echo 📋 安裝套件清單...

REM 安裝套件
python -m pip install -r requirements.txt

echo.
if %errorlevel% equ 0 (
    echo ✅ 所有套件安裝完成！
    echo.
    echo 📝 已安裝的主要套件:
    echo    - Flask ^(Web 框架^)
    echo    - OpenCV ^(圖像處理^)
    echo    - PaddleOCR ^(文字識別^)
    echo    - PyTorch ^(深度學習^)
    echo    - Transformers ^(自然語言處理^)
    echo.
    echo 🎯 現在可以運行 start_system.bat 啟動系統
) else (
    echo ❌ 部分套件安裝失敗
    echo 請檢查網路連線或套件版本相容性
)

echo.
echo 按任意鍵結束...
pause > nul