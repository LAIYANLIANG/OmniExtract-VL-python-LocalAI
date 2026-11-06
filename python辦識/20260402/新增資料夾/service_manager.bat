@echo off
REM PO Extractor 服務管理腳本
REM 版本: v2.0 (Qwen Enhanced)

echo.
echo =============================================
echo   PO Extractor 服務管理中心
echo =============================================
echo.
echo 請選擇操作:
echo   [1] 啟動服務
echo   [2] 重新啟動服務 
echo   [3] 檢查服務狀態
echo   [4] 查看服務日誌
echo   [5] 清理暫存並重啟
echo   [6] 完全重新初始化
echo   [0] 退出
echo.

set /p choice="請輸入選項 (0-6): "

if "%choice%"=="1" goto start_service
if "%choice%"=="2" goto restart_service
if "%choice%"=="3" goto check_status
if "%choice%"=="4" goto view_logs
if "%choice%"=="5" goto clean_restart
if "%choice%"=="6" goto full_reinit
if "%choice%"=="0" goto exit

echo 無效選項，請重新選擇
pause
goto main

:start_service
echo.
echo [啟動服務]
echo 正在啟動 PO Extractor 服務...
start "PO Extractor Service" py restart_final.py
echo 服務已在背景啟動
echo 請開啟瀏覽器訪問: http://127.0.0.1:5000
pause
goto main

:restart_service
echo.
echo [重新啟動服務]
echo 正在終止現有服務...
taskkill /f /im python.exe /fi "WINDOWTITLE eq PO Extractor Service*" >nul 2>&1
timeout /t 2 >nul
echo 正在重新啟動服務...
start "PO Extractor Service" py restart_final.py
echo 服務已重新啟動
echo 請開啟瀏覽器訪問: http://127.0.0.1:5000
pause
goto main

:check_status
echo.
echo [檢查服務狀態]
py -c "
import requests
import json
try:
    response = requests.get('http://127.0.0.1:5000/health', timeout=3)
    if response.status_code == 200:
        data = response.json()
        print('✅ 服務運行正常')
        print(f'   版本: {data.get(\"version\")}')
        print(f'   狀態: {data.get(\"status\")}')
        print('   功能狀態:')
        features = data.get('features', {})
        for feature, available in features.items():
            status = '✅ 可用' if available else '❌ 不可用'
            print(f'     {feature}: {status}')
    else:
        print(f'❌ 服務異常，狀態碼: {response.status_code}')
except requests.exceptions.RequestException:
    print('❌ 服務未運行或無法連接')
except Exception as e:
    print(f'❌ 檢查失敗: {e}')
"
pause
goto main

:view_logs
echo.
echo [查看服務日誌]
if exist "webapp_startup.log" (
    echo === 服務啟動日誌 ===
    type webapp_startup.log | more
) else (
    echo 沒有找到日誌檔案
)
echo.
if exist "pipeline_test.log" (
    echo === 管道測試日誌 ===
    type pipeline_test.log | more
) else (
    echo 沒有找到測試日誌
)
pause
goto main

:clean_restart
echo.
echo [清理暫存並重啟]
echo 正在終止服務...
taskkill /f /im python.exe >nul 2>&1
echo 正在清理Python暫存...
py -c "
import os
import shutil

# 清理__pycache__
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        cache_path = os.path.join(root, '__pycache__')
        try:
            shutil.rmtree(cache_path)
            print(f'🗑️  已刪除: {cache_path}')
        except:
            pass

print('✅ 暫存清理完成')
"
timeout /t 2 >nul
echo 正在重新啟動服務...
start "PO Extractor Service" py restart_final.py
echo 服務已清理並重新啟動
pause
goto main

:full_reinit
echo.
echo [完全重新初始化]
echo ⚠️  這將清理所有暫存並重新設置系統
set /p confirm="確定要繼續嗎? (y/N): "
if not "%confirm%"=="y" if not "%confirm%"=="Y" goto main

echo 正在終止所有Python程序...
taskkill /f /im python.exe >nul 2>&1
echo 正在執行完全重新初始化...
py restart_service.py
echo 正在啟動新的服務實例...
start "PO Extractor Service" py restart_final.py
echo 完全重新初始化完成
pause
goto main

:exit
echo.
echo 感謝使用 PO Extractor 服務管理中心
echo 如需停止服務，請關閉服務視窗或使用工作管理員
exit /b 0

:main
cls
goto start