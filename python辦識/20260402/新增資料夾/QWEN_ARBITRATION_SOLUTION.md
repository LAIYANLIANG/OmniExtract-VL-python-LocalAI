# Qwen 仲裁 "資訊不明" 問題解決方案

## 📋 問題診斷

### 問題描述
用戶在 webapp 中看到 Qwen 仲裁欄位顯示 **"資訊不明"** 狀態。

### 根本原因分析
經過詳細診斷發現問題源自：

1. **舊數據結構** - 現有的結果文件（`results/` 文件夾中的 JSON 文件）是在 Qwen 仲裁系統實施之前處理的
2. **缺失字段** - 舊結果文件缺少：
   - `_qwen_audit` 字段（Qwen 執行記錄）
   - `accuracy_pct` 字段（信心分數）
   - `_qwen_execution_indicator` 字段（執行標註）
3. **條件判斷邏輯** - 當 `create_qwen_execution_indicator` 函數處理這些舊數據時：
   - `confidence_score` 默認為 0
   - `qwen_audit_data` 為空字典 `{}`
   - 觸發最後的 `else` 分支，返回 `❌ QWEN_UNAVAILABLE` 狀態
   - 在前端顯示為 "❌ 不可用" 或 "資訊不明"

## ✅ 解決方案

### 1. 修改 `create_qwen_execution_indicator` 函數

**文件**: `po_extractor/webapp.py`

**修改內容**:
```python
def create_qwen_execution_indicator(qwen_audit_data: Dict[str, Any], qwen_triggered: bool, confidence_score: float) -> Dict[str, Any]:
    # 新增舊數據識別邏輯
    is_legacy_data = (
        confidence_score == 0 and (
            not qwen_audit_data or
            (not any(v for v in qwen_audit_data.values() if v is not None and v != 0 and v != False))
        )
    )
    
    if is_legacy_data:
        return {
            "status": "📜 LEGACY_DATA",
            "badge": "📜 舊數據 - 重新處理可獲得Qwen仲裁",
            "details": {
                "reason": "legacy_result_file",
                "note": "此結果由舊版系統生成，不包含Qwen仲裁功能"
            },
            "message": "📜 此為舊版本處理結果，重新上傳PDF可獲得Qwen仲裁功能",
            "css_class": "legacy-data-badge",
            "priority": "INFO"
        }
    # ... 其餘邏輯保持不變
```

### 2. 添加 CSS 樣式

**文件**: `po_extractor/templates/index.html`

**新增樣式**:
```css
.legacy-data-badge { 
  background: linear-gradient(135deg, #6b7280, #4b5563);
  color: white;
  padding: 3px 8px; 
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  cursor: help;
  opacity: 0.8;
}
```

### 3. 更新 JavaScript 處理

**文件**: `po_extractor/templates/index.html`

**修改 `createQwenBadgeHtml` 函數**:
```javascript
function createQwenBadgeHtml(indicator) {
  // ... 現有邏輯 ...
  
  // 新增舊數據處理
  else if (status === '📜 LEGACY_DATA') {
    return `<span class="legacy-data-badge" title="${tooltipText}">📜 舊數據</span>`;
  }
  
  // ... 其餘邏輯保持不變 ...
}
```

## 🎯 解決效果

### 修復前 (問題狀態)
- 舊數據顯示：**"❌ 不可用"** 或 **"❓ 資訊不明"**
- 用戶困惑為什麼 Qwen 仲裁不工作

### 修復後 (期望狀態)
- 舊數據顯示：**"📜 舊數據"**
- 清楚提示：*"重新處理可獲得Qwen仲裁"*
- 滑鼠懸停顯示：*"此結果由舊版系統生成，不包含Qwen仲裁功能"*

## 📊 不同情況下的標註對照表

| 數據類型 | 信心分數 | Qwen 狀態 | 顯示標註 | 含義 |
|---------|----------|-----------|----------|------|
| 舊數據 | 0 (默認) | 無數據 | 📜 舊數據 | 需重新處理獲得仲裁功能 |
| 新數據 | ≥ 92% | 未觸發 | ✅ 高信心 | 原始結果可信，無需仲裁 |
| 新數據 | < 92% | 已執行 | 🎯 已執行 | Qwen已介入並改進結果 |
| 新數據 | < 92% | 嘗試失敗 | ⚠️ 嘗試中 | 觸發但API調用失敗 |
| 新數據 | < 92% | 服務不可用 | ❌ 不可用 | Ollama未啟動或模型缺失 |

## 🚀 測試驗證

### 測試步驟
```bash
# 1. 測試修復後的函數
py -c "
from po_extractor.webapp import create_qwen_execution_indicator

# 测试舊數據
result = create_qwen_execution_indicator({}, False, 0)
print('舊數據:', result['status'], '-', result['badge'])

# 测试新數據（高信心）
result = create_qwen_execution_indicator({}, False, 0.95) 
print('高信心:', result['status'], '-', result['badge'])
"
```

### 預期輸出
```
舊數據: 📜 LEGACY_DATA - 📜 舊數據 - 重新處理可獲得Qwen仲裁
高信心: ✅ HIGH_CONFIDENCE - ✅ 高信心分數 - 無需仲裁
```

## 🎊 用戶指南

### 看到 "📜 舊數據" 時該怎麼辦？

1. **理解含義**: 此結果是由舊版系統處理的，不包含 Qwen 仲裁功能
2. **獲得仲裁**: 重新上傳相同的 PDF 文件
3. **新結果**: 新處理的結果會包含完整的 Qwen 仲裁標註
4. **對比改進**: 可以比較舊結果與新結果的差異

### 各種標註的含義

- **🎯 已執行** = Qwen 真正執行了仲裁，結果已改進
- **✅ 高信心** = 原始結果可信度高，無需 Qwen 介入  
- **⚠️ 嘗試中** = Qwen 被觸發但執行未完成
- **❌ 不可用** = 需要檢查 Ollama 服務或模型狀態
- **📜 舊數據** = 重新處理可獲得仲裁功能

## 📝 技術實現細節

### 舊數據識別邏輯
```python
is_legacy_data = (
    confidence_score == 0 and (
        not qwen_audit_data or
        (not any(v for v in qwen_audit_data.values() 
                if v is not None and v != 0 and v != False))
    )
)
```

### 關鍵判斷條件
1. `confidence_score == 0` - 默認值，表示沒有計算過信心分數
2. `not qwen_audit_data` - 完全沒有 Qwen 審核數據
3. 或者只有默認值（None, 0, False）

### 優先級處理
修復確保了正確的條件判斷優先級：
1. 首先檢查是否為舊數據
2. 然後檢查 Qwen 是否真正執行
3. 接著檢查是否為高信心分數
4. 最後處理其他異常情況

## ✅ 總結

**問題**: Qwen 仲裁顯示 "資訊不明"  
**原因**: 舊數據缺少 Qwen 相關字段  
**解決**: 添加舊數據識別和友善提示  
**效果**: 清楚標註 "📜 舊數據" 並提示重新處理  

**狀態**: ✅ 已完全解決，webapp 正常運行