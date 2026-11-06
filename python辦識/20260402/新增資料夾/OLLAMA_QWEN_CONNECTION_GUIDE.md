# Ollama + Qwen3-VL-4B-Instruct 連線指南

## 📋 當前配置總覽

### 🔧 模型資訊
- **模型名稱**: Qwen3-VL-4B-Instruct
- **量化版本**: Q4_K_M  
- **Ollama 模型 ID**: `adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M`
- **檔案大小**: 3.3 GB
- **狀態**: ✅ 已下載並安裝

### 🌐 連線資訊
- **Ollama 服務**: `http://localhost:11434`
- **API 端點**: `http://localhost:11434/api/generate`
- **服務狀態**: ✅ 正在運行
- **連接逾時**: 60 秒

## 🚀 啟動步驟

### 步驟1: 確保 Ollama 服務運行
```powershell
# 檢查 Ollama 服務狀態
& "C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe" ps

# 如果沒有運行，啟動服務
& "C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe" serve
```

### 步驟2: 預載模型（可選，加快首次回應）
```powershell
& "C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe" run adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M
```

### 步驟3: 測試模型連線
```powershell
py -c "
import requests, json
payload = {
    'model': 'adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M',
    'prompt': '請回答 OK',
    'stream': False
}
response = requests.post('http://localhost:11434/api/generate', json=payload, timeout=120)
print('狀態:', response.status_code)
if response.status_code == 200:
    print('回應:', response.json().get('response', ''))
"
```

## ⚙️ WebApp 中的 Qwen 配置

### 配置檔案位置
- `po_extractor/config/qwen_config.json`

### 關鍵設定
```json
{
  "runtime": {
    "backend": "ollama",
    "api_endpoint": "http://localhost:11434/api/generate",
    "model_id": "adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M",
    "max_tokens": 2048,
    "temperature": 0.3,
    "timeout_seconds": 60
  },
  "learning": {
    "confidence_threshold": 0.92
  }
}
```

### 觸發條件
- **信心分數 < 92%** → 自動調用 Qwen3-VL 進行仲裁
- **高信心分數 ≥ 92%** → 跳過 Qwen，直接使用原始結果

## 🔧 WebApp 中的 Qwen 客戶端

### 核心組件位置
- **Qwen 客戶端**: `po_extractor/pipeline/step7_qwen_audit.py`
- **學習系統**: `po_extractor/pipeline/qwen_learning_system.py`  
- **WebApp 整合**: `po_extractor/webapp.py`

### 連線流程
1. **WebApp 處理 PDF** → 計算信心分數
2. **低信心觸發** → 調用 `get_qwen_client()`  
3. **Qwen 客戶端** → 發送 HTTP POST 到 `localhost:11434`
4. **Ollama 服務** → 載入並執行 Qwen3-VL-4B
5. **模型回應** → 返回仲裁結果
6. **學習記錄** → 記錄到 `qwen_learning_log.json`

## 📊 連線測試指令

### 快速狀態檢查
```powershell
# 檢查 Ollama 服務
py -c "import requests; print('Ollama:', requests.get('http://localhost:11434/api/tags').status_code)"

# 檢查已載入模型  
& "C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe" ps

# 檢查可用模型
& "C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe" list
```

### 完整功能測試
```powershell
py -c "
# 測試完整的 Qwen 仲裁流程
from po_extractor.webapp import get_qwen_client
import json

print('測試 Qwen 客戶端連線...')
try:
    client = get_qwen_client()
    if client:
        print('✅ Qwen 客戶端初始化成功')
        print('📡 API 端點:', client.config.get('runtime', {}).get('api_endpoint'))
        print('🤖 模型 ID:', client.config.get('runtime', {}).get('model_id'))
    else:
        print('❌ Qwen 客戶端初始化失敗')
except Exception as e:
    print('❌ 錯誤:', e)
"
```

## 🎯 實際使用場景

### 在 WebApp 中觸發 Qwen
1. **上傳 PDF** 到 http://127.0.0.1:5000
2. **信心分數 < 92%** → 自動觸發 Qwen 仲裁
3. **查看結果** → "🤖 Qwen仲裁" 欄位顯示執行狀態
4. **學習記錄** → 系統自動記錄改進模式

### 手動測試 API
```python
import requests
import json

# 直接調用 Ollama API
payload = {
    "model": "adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M",
    "prompt": "分析以下採購單資料的準確性...",
    "stream": False,
    "options": {
        "temperature": 0.3,
        "max_tokens": 2048
    }
}

response = requests.post(
    "http://localhost:11434/api/generate", 
    json=payload, 
    timeout=60
)

if response.status_code == 200:
    result = response.json()
    print("Qwen 回應:", result["response"])
```

## ⚡ 性能優化建議

### 首次載入優化
```powershell
# 預載模型到記憶體（加快後續回應）
& "C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe" run adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M
```

### 連線參數調整
- **timeout_seconds**: 60-120 秒（首次載入較慢）
- **temperature**: 0.3（平衡創造性與準確性）
- **max_tokens**: 2048（足夠詳細回應）

## 🔍 故障排除

### 常見問題

1. **模型回應超時**
   - 首次載入需要時間，等待 2-3 分鐘
   - 調整 `timeout_seconds` 至 120
   
2. **Ollama 服務無回應**
   ```powershell
   # 重新啟動 Ollama 服務
   Get-Process -Name "ollama" | Stop-Process -Force
   & "C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe" serve
   ```

3. **模型未載入**
   ```powershell
   # 檢查並重新載入
   & "C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe" ps
   & "C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe" run adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M
   ```

### 日誌檢查
- **Ollama 日誌**: 在啟動 `ollama serve` 的終端中查看
- **WebApp 日誌**: 上傳 PDF 時在 webapp 終端中查看
- **學習日誌**: `qwen_learning_log.json` 文件

## ✅ 成功連線確認清單

- [ ] ✅ Ollama 服務運行 (`ollama ps` 有回應)
- [ ] ✅ 模型已安裝 (`ollama list` 看到 Qwen3-VL) 
- [ ] ✅ API 端點可達 (`curl http://localhost:11434/api/tags`)
- [ ] ✅ 模型可回應 (測試 API 調用成功)
- [ ] ✅ WebApp 整合 (上傳 PDF 看到 Qwen 標註)
- [ ] ✅ 學習記錄 (檢查 `qwen_learning_log.json`)

**🎊 當所有項目都勾選時，您的 Qwen3-VL-4B 仲裁系統就完全運作正常了！**