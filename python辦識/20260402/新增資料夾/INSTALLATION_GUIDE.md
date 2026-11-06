# Qwen3-VL 七步管道安裝指南

## 系統需求
- Windows 10/11
- Python 3.8+ 
- 16GB+ RAM (推薦 Qwen3-VL-7B Q4_K_M量化版本)
- 5GB+ 儲存空間

## 安裝步驟

### 1. 安裝 Python
如果尚未安裝 Python，請從官網下載：https://www.python.org/downloads/

### 2. 安裝 Python 相依套件
```bash
# 切換到專案目錄
cd "C:\Users\localadmin\Desktop\新增資料夾"

# 安裝核心套件
py -m pip install -r requirements.txt

# 安裝 PaddleOCR (中文OCR引擎)
py -m pip install paddleocr paddlepaddle-cpu

# 如果有顯卡，可安裝 GPU 版本
# py -m pip install paddlepaddle-gpu
```

### 3. 安裝 Ollama (用於部署 Qwen3-VL)
1. 下載 Ollama: https://ollama.com/download/windows
2. 安裝並啟動 Ollama 服務
3. 下載 Qwen3-VL 模型：
```bash
ollama pull qwen2-vl:7b
```

### 4. 驗證安裝
```bash
# 測試 PaddleOCR
python -c "import paddleocr; print('PaddleOCR OK')"

# 測試 OpenCV  
python -c "import cv2; print('OpenCV OK')"

# 測試 Ollama 連接
curl http://localhost:11434/api/tags
```

### 5. 啟動系統
```bash
py -m po_extractor.webapp
```

然後開啟瀏覽器訪問：http://127.0.0.1:5000

## 配置說明

所有配置檔案位於 `po_extractor/config/` 目錄：

- `qwen_config.json` - Qwen3-VL 模型配置
- `image_processing_params.json` - OpenCV 圖片處理參數
- `vendor_image_profiles.json` - 供應商圖片設定檔
- `regex_rules.json` - 文字清理規則
- `learning_journal.json` - 機器學習記錄

## 功能特寫

### 七步驟管道
1. **OpenCV 預處理**: 圖片清理、去噪、傾斜校正
2. **文件分類**: PDF 類型分類與頁面分析
3. **PaddleOCR**: 中英文字辨識
4. **資料清洗**: 文字正規化與雜訊移除
5. **邏輯判斷**: 供應商識別與表頭分析
6. **LayoutLM**: 深度結構化擷取（按需觸發）
7. **Qwen3-VL**: 視覺語言模型最終審核

### Web API 端點
- `POST /qwen/process` - 完整七步管道處理
- `POST /qwen/audit` - Qwen 審核現有結果
- `POST /qwen/feedback` - 提交用戶修正反饋
- `GET /qwen/status` - 系統狀態檢查

## 疑難排解

### 常見問題

**Q: PaddleOCR 安裝失敗**
A: 嘗試使用清華映像源：
```bash
py -m pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**Q: Ollama 無法連接**
A: 確保 Ollama 服務正在運行：
```bash
ollama serve
```

**Q: 記憶體不足**
A: 在 `qwen_config.json` 中調整：
```json
{
  "model": {
    "max_memory": "8GB",
    "quantization": "Q4_K_M"
  }
}
```

**Q: OpenCV 錯誤**
A: 安裝完整版本：
```bash
py -m pip install opencv-python-headless
```

## 模型效能

| 模型 | 量化 | 大小 | RAM 需求 | 速度 |
|------|------|------|----------|------|  
| Qwen3-VL-7B | Q4_K_M | ~4.5GB | 8GB | 中等 |
| Qwen3-VL-7B | Q6_K | ~6.2GB | 12GB | 快速 |
| Qwen3-VL-7B | F16 | ~14GB | 20GB | 最快 |

推薦 16GB RAM 系統使用 Q4_K_M 量化版本。

## 聯繫支援

如遇技術問題，請提供：
1. 錯誤訊息
2. `pip list` 輸出
3. `ollama list` 輸出
4. 系統資訊（RAM、Python版本）