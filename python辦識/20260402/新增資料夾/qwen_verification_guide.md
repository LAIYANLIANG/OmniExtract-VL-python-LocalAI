# Qwen 仲裁執行判斷指南

## 上傳PDF後如何確認Qwen是否執行仲裁

### 1. 查看網頁UI結果 ⭐ (最直接)

處理完PDF後，在結果中查看：
```json
{
  "_qwen_audit": {
    "executed": true,                    // ✅ true=已執行, false=未執行
    "triggered_by": "low_confidence",    // ✅ 觸發原因
    "actual_confidence": 0.764,          // ✅ 實際信心分數 76.4%
    "confidence_threshold": 0.92,        // ✅ 閾值設定 92%
    "qwen_invoked": 3,                   // ✅ >0 表示真的調用了Qwen API
    "learning_record_id": "xxx_123",     // ✅ 有值表示已記錄到學習系統
    "fields_audited": 15,                // 審核的欄位數量
    "corrections_applied": 2             // 應用的修正數量
  }
}
```

**判斷標準：**
- `executed: true` + `qwen_invoked > 0` = **✅ Qwen確實執行了仲裁**
- `executed: false` + `reason: "high_confidence"` = **✅ 信心分數夠高，正常跳過**

### 2. 查看學習統計 (即時監控)

訪問：http://127.0.0.1:5000/learning/stats
```json
{
  "stats": {
    "total_qwen_triggers": 3,      // 總觸發次數
    "low_confidence_triggers": 3,  // 低信心觸發次數
    "manual_corrections_recorded": 1
  },
  "threshold_config": {
    "confidence_threshold": 0.92   // 92%閾值確認
  }
}
```

**每次處理PDF後，總觸發次數會增加（如果信心分數<92%）**

### 3. 強制觸發測試

如果想確保Qwen真的會被調用，可以：

#### A. 上傳複雜PDF
- 選擇字跡模糊、掃描品質差的PDF
- 多語言混合或格式不規整的文件
- 這些更容易產生 < 92% 信心分數

#### B. 臨時降低閾值測試
```python
# 修改 webapp.py 中的閾值 (僅測試用)
CONFIDENCE_THRESHOLD = 0.99  # 改為99%，幾乎肯定觸發

# 測試完記得改回
CONFIDENCE_THRESHOLD = 0.92  # 恢復92%
```

## 實際使用建議

### 正常情況下的觸發頻率
- **高品質PDF**: 很少觸發 (信心分數通常 > 95%)
- **一般品質PDF**: 偶爾觸發 (信心分數 90-95%)  
- **低品質PDF**: 經常觸發 (信心分數 < 90%)

### 長期觀察指標
1. **觸發頻率逐漸降低** = 學習系統生效
2. **改進模式增加** = 系統持續學習
3. **人工修正記錄增加** = 提升準確率

## 當前系統狀態 ✅

✅ Qwen仲裁系統: 已啟用，92%閾值  
✅ 學習記錄: 3次觸發，1次人工修正  
✅ 改進模式: 已生成1個  
⚠️ 模型推論: 可用但首次調用較慢  

**系統已準備就緒，可以正常使用！**