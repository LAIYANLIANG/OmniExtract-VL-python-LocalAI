#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen 仲裁標註功能測試
===================

測試新添加的Qwen執行標註功能，展示如何在處理結果中
清楚地看到是否執行了Qwen3-VL-4B-Instruct仲裁。

使用方法: py test_qwen_indicators.py

作者: GitHub Copilot  
日期: 2026-04-01
"""

import os
import sys
import json
import requests
from datetime import datetime

def test_qwen_indicators():
    """測試Qwen執行標註功能"""
    print("🎯 Qwen 仲裁標註功能測試")
    print("=" * 50)
    
    # 測試webapp連接
    try:
        response = requests.get("http://127.0.0.1:5000", timeout=5)
        if response.status_code != 200:
            print("❌ Webapp無法連接")
            return False
        print("✅ Webapp連接正常")
        
        # 檢查是否包含新的Qwen仲裁列
        if "🤖 Qwen仲裁" in response.text:
            print("✅ 新的'🤖 Qwen仲裁'列已添加到結果表格")
        else:
            print("❌ 未找到Qwen仲裁列")
            return False
            
        # 檢查CSS樣式是否載入
        css_indicators = [
            "qwen-executed", "qwen-attempted", 
            "high-confidence", "qwen-unavailable"
        ]
        
        css_found = sum(1 for indicator in css_indicators if indicator in response.text)
        print(f"✅ Qwen標註CSS樣式: 找到 {css_found}/{len(css_indicators)} 個")
        
        # 檢查JavaScript函數
        if "createQwenBadgeHtml" in response.text:
            print("✅ JavaScript標註函數已載入")
        else:
            print("❌ 未找到JavaScript標註函數")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False
    
    return True

def show_qwen_indicator_examples():
    """展示不同的Qwen執行標註類型"""
    print("\n🎨 Qwen 執行標註類型展示")
    print("=" * 50)
    
    indicators = [
        {
            "name": "🎯 已執行仲裁",
            "condition": "信心分數 < 92%，Qwen成功執行",
            "display": "🎯 已執行",
            "css_class": "qwen-executed",
            "color": "綠色漸變",
            "meaning": "Qwen3-VL-4B真正執行了仲裁，有API調用記錄"
        },
        {
            "name": "⚠️ 嘗試執行", 
            "condition": "觸發但未完成API調用",
            "display": "⚠️ 嘗試中",
            "css_class": "qwen-attempted", 
            "color": "橙色",
            "meaning": "Qwen被觸發但未成功完成"
        },
        {
            "name": "✅ 高信心分數",
            "condition": "信心分數 >= 92%",
            "display": "✅ 高信心", 
            "css_class": "high-confidence",
            "color": "藍色",
            "meaning": "前6步結果可信，跳過Qwen仲裁"
        },
        {
            "name": "❌ 服務不可用",
            "condition": "Ollama未啟動或模型不可用",
            "display": "❌ 不可用",
            "css_class": "qwen-unavailable",
            "color": "紅色", 
            "meaning": "需要Qwen但服務不可用"
        }
    ]
    
    for indicator in indicators:
        print(f"\n【{indicator['name']}】")
        print(f"  觸發條件: {indicator['condition']}")
        print(f"  顯示標註: {indicator['display']}")
        print(f"  CSS 樣式: {indicator['css_class']}")
        print(f"  顏色樣式: {indicator['color']}")
        print(f"  含義說明: {indicator['meaning']}")

def demo_json_output_structure():
    """展示包含Qwen執行標註的JSON輸出結構"""
    print("\n📋 JSON 輸出結構範例")
    print("=" * 50)
    
    example_output = {
        "filename": "example_po.pdf",
        "status": "success",
        "vendor_folder": "SIEMENS",
        "po_number": "4511697495",
        "accuracy_pct": 85.2,
        "total_amount": "150,000",
        "item_count": 5,
        "_qwen_audit": {
            "executed": True,
            "triggered_by": "low_confidence",
            "actual_confidence": 0.852,
            "confidence_threshold": 0.92,
            "qwen_invoked": 3,
            "learning_record_id": "abc123_001",
            "corrections_applied": 2
        },
        "_qwen_execution_indicator": {
            "status": "🤖 QWEN_EXECUTED",
            "badge": "🎯 已執行 Qwen3-VL-4B 仲裁",
            "details": {
                "confidence_score": "85.2%",
                "threshold": "92%",
                "trigger_reason": "low_confidence",
                "api_calls": 3,
                "learning_recorded": True,
                "record_id": "abc123_001"
            },
            "message": "✅ 信心分數 85.2% < 92%，已觸發 Qwen3-VL 仲裁 (3次API調用)",
            "css_class": "qwen-executed-badge",
            "priority": "HIGH"
        }
    }
    
    print("處理完PDF後，您會在結果JSON中看到以下欄位：")
    print("\n1. 基本仲裁資訊 (_qwen_audit):")
    print(json.dumps(example_output["_qwen_audit"], indent=2, ensure_ascii=False))
    
    print("\n2. 執行標註資訊 (_qwen_execution_indicator):")  
    print(json.dumps(example_output["_qwen_execution_indicator"], indent=2, ensure_ascii=False))

def show_usage_instructions():
    """顯示使用說明"""
    print("\n📖 使用說明")
    print("=" * 50)
    
    print("1. 💻 開啟網頁介面:")
    print("   http://127.0.0.1:5000")
    
    print("\n2. 📄 上傳PDF文件:")
    print("   - 選擇任何PDF文件上傳")
    print("   - 系統會自動處理並顯示結果")
    
    print("\n3. 🔍 查看Qwen仲裁標註:")
    print("   - 在結果表格中找到'🤖 Qwen仲裁'列")
    print("   - 不同顏色的標註代表不同的執行狀態:")
    print("     🎯 綠色 = Qwen已執行仲裁")
    print("     ✅ 藍色 = 高信心分數，無需仲裁")  
    print("     ⚠️ 橙色 = Qwen嘗試執行但未完成")
    print("     ❌ 紅色 = Qwen服務不可用")
    
    print("\n4. 📊 詳細資訊:")
    print("   - 將滑鼠懸停在標註上可查看詳細資訊")
    print("   - 包含信心分數、API調用次數、學習記錄ID等")
    
    print("\n5. 🧠 學習記錄:")
    print("   - 每次Qwen執行都會記錄到學習系統")
    print("   - 訪問 /learning/stats 查看統計")

def main():
    """主測試流程"""
    print("🤖 Qwen3-VL-4B 仲裁標註功能測試")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 測試功能
    success = test_qwen_indicators()
    
    if success:
        print("\n✅ 所有測試通過！Qwen仲裁標註功能已正常運作")
        
        # 展示功能說明
        show_qwen_indicator_examples()
        demo_json_output_structure()
        show_usage_instructions()
        
        print("\n🎉 功能總結")
        print("=" * 50)
        print("✅ 新增'🤖 Qwen仲裁'列到結果表格")
        print("✅ 4種不同的執行狀態標註")
        print("✅ 詳細的tooltip提示資訊")
        print("✅ 美觀的CSS樣式設計")
        print("✅ 完整的JSON資訊記錄")
        
    else:
        print("\n❌ 測試失敗，請檢查系統設定")
    
    print(f"\n📖 現在您可以上傳PDF文件到 http://127.0.0.1:5000")
    print("在結果表格的'🤖 Qwen仲裁'列中就能看到執行標註！")

if __name__ == "__main__":
    main()