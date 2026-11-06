# PO 提取系統啟動指南

## 🚀 快速開始

當您下次要啟動系統時，請按照以下順序操作：

### 第一次安裝 (新環境)

1. **安裝相依套件**
   ```bash
   雙擊 install_dependencies.bat
   ```
   或手動執行：
   ```bash
   py -m pip install -r requirements.txt
   ```
   > ⚠️ 本機使用 `py` 指令，非 `python`

2. **安裝 Ollama 服務**
   - 下載並安裝 Ollama: https://ollama.ai/
   - 安裝完成後從開始選單啟動 Ollama
   - 安裝路徑: `C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe`
   - ⚠️ Ollama 未加入系統 PATH，需從開始選單啟動或使用完整路徑

3. **下載 Qwen3-VL-4B 模型**
   ```bash
   ollama pull adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M
   ```
   > 模型大小約 3.3 GB，請確保磁碟空間充足

### 日常啟動 (已安裝環境)

**⚠️ 關鍵：必須按照以下順序啟動，否則 Qwen 審核功能不可用**

#### 步驟 1: 啟動 Ollama 服務 (必須最先)
```
從 Windows 開始選單啟動 Ollama
```
或使用完整路徑：
```bash
"C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe" serve
```
等待約 5-10 秒讓服務就緒，驗證方式：
```bash
curl http://127.0.0.1:11434
```
應回傳 "Ollama is running"

#### 步驟 2: 確認模型已載入
```bash
ollama list
```
確認 `adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M` 出現在列表中

#### 步驟 3: 啟動 Flask Web 服務
```bash
cd "C:\Users\localadmin\Desktop\新增資料夾"
py -m po_extractor.webapp
```
> ⚠️ 使用 `py`，不是 `python`
> ⚠️ 使用 `-m po_extractor.webapp` 模組方式啟動，確保 import 路徑正確

#### 步驟 4: 驗證服務
- 瀏覽器開啟: http://127.0.0.1:5000
- 確認看到完整 UI 介面 (非簡易頁面)

### 啟動順序關係圖

```
Ollama 服務 (Port 11434) ← 必須最先啟動
       │
       ▼
Qwen3-VL-4B 模型 ← 被 Ollama 管理
       │
       ▼
webapp.py (Port 5000) ← 啟動時偵測 Ollama，決定 HAS_QWEN 狀態
       │
       ▼
使用者瀏覽器 ← http://127.0.0.1:5000
```

**如果順序錯誤：**
- 先啟 webapp 才啟 Ollama → HAS_QWEN=False，Qwen 審核不可用
- 解決方式：重啟 webapp (先 Ctrl+C 停止，再 `py -m po_extractor.webapp`)

### 替代啟動方式

**方式一: 使用批次檔**
```bash
雙擊 start_system.bat
```

**方式二: 使用 Python 檢查工具**
```bash
py startup_checker.py
```

**方式三: 使用備用啟動器 (簡易介面)**
```bash
py restart_final.py
```
> 注意：restart_final.py 提供簡易內建 HTML 介面，功能較完整 webapp.py 少

## 📋 系統檢查項目

啟動工具會自動檢查以下項目：

### ✅ 必要組件
- [ ] Python 3.8+ 版本 (使用 `py` 指令)
- [ ] Flask Web 框架
- [ ] OpenCV 圖像處理
- [ ] PaddleOCR 文字識別 
- [ ] PyTorch 深度學習框架
- [ ] numpy 數值計算
- [ ] Ollama 服務運行狀態 (Port 11434)
- [ ] Qwen3-VL-4B 模型可用性 (`adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M`)
- [ ] 工作區檔案完整性

### 🔧 自動修復功能
- 自動安裝缺失的 Python 套件
- 清理系統快取檔案
- 停止衝突的舊服務
- 健康檢查與狀態報告

## 🗂️ 檔案說明

| 檔案 | 用途 | 使用時機 |
|------|------|----------|
| `start_system.bat` | 一鍵啟動批次檔 | 每次啟動系統 |
| `startup_checker.py` | 完整系統檢查工具 | 診斷系統問題 |
| `install_dependencies.bat` | 安裝相依套件 | 初次設定或更新 |
| `requirements.txt` | Python 套件清單 | 套件管理參考 |
| `restart_final.py` | 備用啟動器 (簡易 HTML 介面) | webapp.py 無法啟動時使用 |
| `po_extractor/webapp.py` | **主要 Web 服務 (完整 UI)** | **正式啟動入口** |

## 🌐 服務訪問

系統啟動成功後，請訪問：
- **主要界面**: http://127.0.0.1:5000
- **系統狀態**: http://127.0.0.1:5000/health
- **Ollama 狀態**: http://127.0.0.1:11434

## ⚠️ 常見問題

### 1. Python 套件安裝失敗
```bash
# 升級 pip 到最新版本
py -m pip install --upgrade pip

# 使用國內鏡像加速
py -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ -r requirements.txt
```

### 2. Ollama 服務無法啟動
- 確認 Ollama 已正確安裝 (路徑: `C:\Users\localadmin\AppData\Local\Programs\Ollama\`)
- 檢查防火牆設定 (Port 11434)
- 從開始選單重新啟動 Ollama
- 或使用完整路徑: `"C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe" serve`

### 3. 端口 5000 被佔用
系統會自動嘗試停止舊服務，也可以手動檢查：
```bash
netstat -ano | findstr :5000
taskkill /F /PID <進程ID>
```

### 4. 模型下載緩慢
- 使用 VPN 或更換網路環境
- Qwen3-VL-4B 模型約 3.3 GB，請確保有足夠的硬碟空間和網路頻寬
- 模型名稱: `adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M`

### 5. Qwen 審核功能不可用 (HAS_QWEN=False)
- **原因**: webapp.py 啟動時 Ollama 尚未就緒
- **解決**: 先確認 Ollama 在執行 (`curl http://127.0.0.1:11434`)，再重啟 webapp
```bash
# Ctrl+C 停止 webapp，然後重新啟動
py -m po_extractor.webapp
```

### 6. 網頁顯示簡易介面而非完整 UI
- **原因**: 可能是 restart_final.py 佔用 Port 5000
- **解決**: 先終止 restart_final.py，再用正式入口啟動
```bash
netstat -ano | findstr :5000
taskkill /F /PID <進程ID>
py -m po_extractor.webapp
```

## 🔄 系統維護

### 定期清理
```bash
# 清理 Python 快取
py startup_checker.py
```

### 更新套件
```bash
py -m pip install --upgrade -r requirements.txt
```

### 備份重要檔案
建議定期備份以下目錄：
- `po_extractor/` (系統核心)
- `output_doc/` (輸出文件)
- `learned_patterns.json` (學習模式)

## 📞 技術支援

如果遇到問題，請：
1. 先執行 `startup_checker.py` 進行診斷
2. 查看系統狀態報告
3. 檢查終端錯誤訊息
4. 確認所有相依套件版本相容性

---

**最後更新**: 2026-03-31
**系統版本**: Qwen3-VL-4B 七步管線 v1.1
**Python 指令**: `py` (非 `python`)
**模型**: `adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M` (3.3 GB)