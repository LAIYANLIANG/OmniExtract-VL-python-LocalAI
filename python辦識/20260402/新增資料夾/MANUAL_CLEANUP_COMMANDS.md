# 手動清理暫存並重啟 webapp 指令

## 🔥 方法一：一鍵執行（推薦）

```powershell
# 執行完整清理重啟腳本
py full_cleanup_restart.py
```

## 🛠️ 方法二：手動分步驟執行

### 步驟 1: 強制終止所有 Python 進程
```powershell
Get-Process -Name "python","py","python3" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
Write-Host "✅ Python 進程已終止" -ForegroundColor Green
```

### 步驟 2: 清除 __pycache__ 目錄和 .pyc 檔案
```powershell
# 刪除所有 __pycache__ 目錄
Get-ChildItem -Path "." -Recurse -Directory -Name "__pycache__" | ForEach-Object { Remove-Item $_.FullName -Recurse -Force; Write-Host "🗑️ 已刪除: $($_.FullName)" }

# 刪除所有 .pyc 檔案  
Get-ChildItem -Path "." -Recurse -File -Filter "*.pyc" | ForEach-Object { Remove-Item $_.FullName -Force; Write-Host "🗑️ 已刪除: $($_.FullName)" }

Write-Host "✅ Python 暫存清理完成" -ForegroundColor Green
```

### 步驟 3: 清除系統模組暫存
```powershell
py -c "
import sys
# 清除已載入的 po_extractor 相關模組
modules_to_remove = [name for name in sys.modules.keys() if 'po_extractor' in name or 'webapp' in name]
for module in modules_to_remove:
    if module in sys.modules:
        del sys.modules[module]
        print(f'🗑️ 已清除模組: {module}')
print('✅ 模組暫存清理完成')
"
```

### 步驟 4: 手動清理臨時檔案（可選）
```powershell
# 清理可能的臨時檔案
Remove-Item "*.tmp" -ErrorAction SilentlyContinue
Remove-Item "*.log" -ErrorAction SilentlyContinue 
Remove-Item "flask_session*" -Recurse -ErrorAction SilentlyContinue
Write-Host "✅ 臨時檔案清理完成" -ForegroundColor Green
```

### 步驟 5: 確認重要檔案存在
```powershell
py -c "
import os
files = [
    'po_extractor/webapp.py',
    'po_extractor/templates/index.html', 
    'po_extractor/config/qwen_config.json',
    'po_extractor/pipeline/qwen_learning_system.py'
]
for f in files:
    status = '✅' if os.path.exists(f) else '❌'
    print(f'{status} {f}')
"
```

### 步驟 6: 重新導入並測試
```powershell
py -c "
import importlib
try:
    import po_extractor.webapp
    importlib.reload(po_extractor.webapp)
    print('✅ 模組重新導入成功')
    
    # 檢查關鍵功能
    from po_extractor.webapp import create_qwen_execution_indicator
    print('✅ Qwen 標註功能可用')
    
    print('🎯 準備啟動...')
except Exception as e:
    print(f'❌ 導入失敗: {e}')
"
```

### 步驟 7: 創建必要目錄
```powershell
if (-not (Test-Path "uploads")) { 
    New-Item -ItemType Directory -Path "uploads" | Out-Null
    Write-Host "📁 已創建 uploads 目錄" -ForegroundColor Green 
}
```

### 步驟 8: 啟動 webapp
```powershell
py -c "
import importlib
import po_extractor.webapp
importlib.reload(po_extractor.webapp)

app = po_extractor.webapp.app
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

print('🚀 啟動修復版 webapp...')
print('✅ 包含 Qwen 仲裁視覺化標註')  
print('✅ 修復舊數據\"資訊不明\"問題')
print('🌐 訪問: http://127.0.0.1:5000')
print('')

app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
"
```

## 🧪 驗證步驟

### 檢查 webapp 是否正常啟動
```powershell
Start-Sleep -Seconds 3
py -c "
import requests
try:
    r = requests.get('http://127.0.0.1:5000', timeout=5)
    print(f'✅ Webapp 狀態: {r.status_code}')
    print(f'📄 頁面大小: {len(r.text)} 字符')
    
    # 檢查修復功能
    if 'legacy-data-badge' in r.text:
        print('✅ 舊數據標註修復已載入')
    if 'LEGACY_DATA' in r.text:
        print('✅ JavaScript 舊數據處理已載入')  
    if 'Qwen仲裁' in r.text:
        print('✅ Qwen 仲裁欄位已添加')
    
    print('🎉 webapp 完全正常運作！')
except Exception as e:
    print(f'❌ 連接失敗: {e}')
"
```

## 🎯 快速故障排除

### 如果端口被占用
```powershell
netstat -ano | findstr ":5000"
# 找到 PID 然後終止: taskkill /PID <PID> /F
```

### 如果模組導入錯誤
```powershell
py -c "import sys; print('\\n'.join(sys.path))"
# 確認當前目錄在 Python 路徑中
```

### 如果還是看到舊頁面（瀏覽器快取）
```
Ctrl + F5 強制重新整理瀏覽器頁面
或開啟無痕模式重新訪問
```