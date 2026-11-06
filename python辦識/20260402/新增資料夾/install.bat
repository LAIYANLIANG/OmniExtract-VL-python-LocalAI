@echo off
REM Qwen3-VL 七步管道自動安裝腳本
REM 作者：GitHub Copilot
REM 版本：1.0.0

echo "================================================="
echo " Qwen3-VL Seven-Step Pipeline Auto-Installer"
echo " 正在初始化環境..."
echo "================================================="

REM 檢查 Python 安裝
echo [1/7] 檢查 Python 安裝...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安裝，請從 https://python.org 下載安裝
    pause
    exit /b 1
)
echo ✅ Python 已安裝

REM 升級 pip
echo [2/7] 升級 pip...
py -m pip install --upgrade pip

REM 安裝核心依賴
echo [3/7] 安裝核心 Python 套件...
py -m pip install Flask==2.3.3 requests==2.31.0 opencv-python==4.8.1.78 Pillow==10.0.0 numpy pandas tqdm

REM 安裝 OCR 引擎
echo [4/7] 安裝 PaddleOCR (中文 OCR 引擎)...
py -m pip install paddleocr paddlepaddle-cpu

REM 創建 config 目錄結構
echo [5/7] 創建配置目錄...
if not exist "po_extractor\config" mkdir "po_extractor\config"
if not exist "logs" mkdir "logs"
if not exist "uploads" mkdir "uploads"

REM 檢查 Ollama
echo [6/7] 檢查 Ollama 安裝...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Ollama 未運行，請安裝並啟動 Ollama:
    echo    1. 前往 https://ollama.com/download/windows
    echo    2. 安裝 Ollama
    echo    3. 執行 'ollama serve'
    echo    4. 執行 'ollama pull qwen2-vl:7b'
) else (
    echo ✅ Ollama 服務正在運行
    
    REM 嘗試下載 Qwen 模型
    echo    正在檢查 Qwen2-VL 模型...
    ollama list | findstr qwen2-vl >nul 2>&1
    if %errorlevel% neq 0 (
        echo    📥 下載 Qwen2-VL 模型 (約 4.5GB)...
        ollama pull qwen2-vl:7b
    ) else (
        echo    ✅ Qwen2-VL 模型已存在
    )
)

REM 驗證安裝
echo [7/7] 驗證安裝...
echo 測試 Python 套件...
py -c "import cv2; print('✅ OpenCV OK')" 2>nul || echo "❌ OpenCV 安裝失敗"
py -c "import paddleocr; print('✅ PaddleOCR OK')" 2>nul || echo "❌ PaddleOCR 安裝失敗"
py -c "import flask; print('✅ Flask OK')" 2>nul || echo "❌ Flask 安裝失敗"

echo.
echo "================================================="
echo " 🎉 安裝完成！"
echo.
echo " 啟動系統："
echo "   py -m po_extractor.webapp"
echo.
echo " 然後開啟瀏覽器訪問："
echo "   http://127.0.0.1:5000"
echo.
echo " 配置檔案位置："
echo "   po_extractor/config/*.json"
echo "================================================="

pause