#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen 仲裁執行驗證工具
===================

檢查 Qwen3-VL-4B 是否真的執行了仲裁，包括：
1. 信心分數是否低於92%觸發閾值
2. Qwen API是否真的被調用
3. 仲裁結果是否被記錄
4. 學習系統是否記錄了觸發事件

使用方法: py check_qwen_execution.py

作者: GitHub Copilot  
日期: 2026-04-01
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

def check_qwen_execution_in_result(result_json):
    """檢查提取結果中的Qwen執行狀態"""
    print("\n🔍 檢查 1: 提取結果中的 Qwen 執行狀態")
    print("-" * 50)
    
    if "_qwen_audit" not in result_json:
        print("❌ 結果中沒有 _qwen_audit 欄位")
        return False
    
    qwen_audit = result_json["_qwen_audit"]
    
    # 檢查基本執行狀態
    executed = qwen_audit.get("executed", False)
    print(f"執行狀態: {'✅ 已執行' if executed else '❌ 未執行'}")
    
    if not executed:
        reason = qwen_audit.get("reason", "unknown")
        print(f"未執行原因: {reason}")
        
        if reason == "high_confidence":
            confidence = qwen_audit.get("actual_confidence", 0)
            threshold = qwen_audit.get("confidence_threshold", 0.92)
            print(f"信心分數: {confidence:.1%} >= 閾值 {threshold:.0%}")
            print("✅ 這是正常的！信心分數夠高，無需Qwen仲裁")
            return True
        return False
    
    # 檢查詳細執行信息
    print(f"觸發原因: {qwen_audit.get('triggered_by', 'unknown')}")
    print(f"信心分數: {qwen_audit.get('actual_confidence', 0):.1%}")
    print(f"閾值設定: {qwen_audit.get('confidence_threshold', 0.92):.0%}")
    print(f"審核欄位數: {qwen_audit.get('fields_audited', 0)}")
    print(f"Qwen調用次數: {qwen_audit.get('qwen_invoked', 0)}")
    print(f"修正應用數: {qwen_audit.get('corrections_applied', 0)}")
    
    learning_record_id = qwen_audit.get('learning_record_id')
    if learning_record_id:
        print(f"學習記錄ID: {learning_record_id}")
    
    return True

def check_learning_system_records():
    """檢查學習系統記錄"""
    print("\n🔍 檢查 2: 學習系統觸發記錄")
    print("-" * 50)
    
    try:
        response = requests.get("http://127.0.0.1:5000/learning/stats", timeout=5)
        if response.status_code != 200:
            print(f"❌ 學習統計API異常: {response.status_code}")
            return False
        
        stats = response.json()
        learning_stats = stats.get("stats", {})
        
        print(f"總觸發次數: {learning_stats.get('total_qwen_triggers', 0)}")
        print(f"低信心觸發: {learning_stats.get('low_confidence_triggers', 0)}")
        print(f"人工修正記錄: {learning_stats.get('manual_corrections_recorded', 0)}")
        print(f"生成改進模式: {learning_stats.get('accuracy_patterns_generated', 0)}")
        
        threshold_config = stats.get("threshold_config", {})
        print(f"設定閾值: {threshold_config.get('confidence_threshold', 0)*100:.0f}%")
        
        total_triggers = learning_stats.get('total_qwen_triggers', 0)
        if total_triggers > 0:
            print(f"✅ 學習系統已記錄 {total_triggers} 次觸發事件")
            return True
        else:
            print("⚠️ 學習系統中沒有觸發記錄")
            return False
            
    except Exception as e:
        print(f"❌ 檢查學習系統失敗: {e}")
        return False

def check_qwen_log_files():
    """檢查Qwen學習記錄檔案"""
    print("\n🔍 檢查 3: 學習記錄檔案")
    print("-" * 50)
    
    log_files = [
        "qwen_learning_log.json",
        "learned_accuracy_patterns.json"
    ]
    
    records_found = False
    
    for file_path in log_files:
        if os.path.exists(file_path):
            print(f"✅ 找到記錄檔: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if file_path == "qwen_learning_log.json":
                    record_count = len(data) if isinstance(data, list) else 0
                    print(f"   觸發記錄數: {record_count}")
                    if record_count > 0:
                        latest = data[-1] if data else {}
                        print(f"   最新觸發: {latest.get('timestamp', 'N/A')}")
                        print(f"   觸發原因: {latest.get('trigger_reason', 'N/A')}")
                        print(f"   信心分數: {latest.get('confidence_score', 0):.1%}")
                        records_found = True
                        
                elif file_path == "learned_accuracy_patterns.json":
                    pattern_count = len(data) if isinstance(data, list) else 0
                    print(f"   改進模式數: {pattern_count}")
                    
            except Exception as e:
                print(f"   ❌ 讀取失敗: {e}")
        else:
            print(f"❌ 未找到: {file_path}")
    
    return records_found

def check_ollama_connection():
    """檢查Ollama連接和模型狀態"""
    print("\n🔍 檢查 4: Ollama 服務與模型狀態")
    print("-" * 50)
    
    try:
        # 檢查Ollama服務
        response = requests.get("http://localhost:11434", timeout=5)
        if response.status_code != 200:
            print("❌ Ollama服務無回應")
            return False
        print("✅ Ollama服務正常")
        
        # 檢查模型列表
        models_response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if models_response.status_code == 200:
            models = models_response.json().get("models", [])
            qwen_models = [m.get("name", "") for m in models if "qwen" in m.get("name", "").lower()]
            
            if qwen_models:
                print(f"✅ Qwen模型可用: {qwen_models[0]}")
                
                # 測試模型推理  
                test_payload = {
                    "model": qwen_models[0],
                    "prompt": "Test",
                    "stream": False
                }
                
                try:
                    test_response = requests.post(
                        "http://localhost:11434/api/generate", 
                        json=test_payload, 
                        timeout=20
                    )
                    if test_response.status_code == 200:
                        print("✅ 模型推論測試成功")
                        return True
                    else:
                        print(f"⚠️ 模型推論測試失敗: {test_response.status_code}")
                        return False
                except Exception as e:
                    print(f"⚠️ 模型推論測試超時: {str(e)[:100]}")
                    return False
            else:
                print("❌ 沒有找到Qwen模型")
                return False
        else:
            print("❌ 無法獲取模型列表")
            return False
            
    except Exception as e:
        print(f"❌ Ollama連接失敗: {e}")
        return False

def simulate_low_confidence_trigger():
    """模擬一個低信心分數的場景來測試觸發"""
    print("\n🔍 檢查 5: 模擬低信心分數觸發測試")
    print("-" * 50)
    
    try:
        from po_extractor.pipeline.qwen_learning_system import qwen_learning_system
        
        # 模擬一個低信心分數的觸發
        record_id = qwen_learning_system.record_qwen_trigger(
            pdf_path="/test/simulate_trigger.pdf",
            raw_text="Simulated test document for trigger verification",
            confidence_score=0.85,  # 低於92%閾值
            low_confidence_fields=["po_number", "total_amount"],
            vendor_type="TEST_SIMULATION",
            original_extraction={"po_number": "TEST123", "total_amount": "1000"},
            trigger_reason="simulation_test"
        )
        
        print(f"✅ 模擬觸發成功，記錄ID: {record_id}")
        print("✅ Qwen學習系統運作正常")
        return True
        
    except Exception as e:
        print(f"❌ 模擬測試失敗: {e}")
        return False

def main():
    """主檢查流程"""
    print("=" * 60)
    print("  Qwen 仲裁執行驗證工具")
    print(f"  檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    print("\n📋 如何判斷Qwen是否真的執行了仲裁：")
    print("1. 信心分數 < 92% → 觸發Qwen")  
    print("2. _qwen_audit.executed = true")
    print("3. qwen_invoked > 0")
    print("4. 學習系統有觸發記錄")
    print("5. Ollama API確實被調用")
    
    # 執行檢查
    check_results = []
    
    # 檢查學習系統記錄 (這個最重要)
    check_results.append(("學習系統記錄", check_learning_system_records()))
    
    # 檢查記錄檔案
    check_results.append(("學習記錄檔案", check_qwen_log_files()))
    
    # 檢查Ollama狀態
    check_results.append(("Ollama與模型", check_ollama_connection()))
    
    # 模擬觸發測試
    check_results.append(("模擬觸發測試", simulate_low_confidence_trigger()))
    
    # 結果總結
    print("\n" + "=" * 60)
    print("  檢查結果總結")
    print("=" * 60)
    
    passed = sum(1 for _, result in check_results if result)
    failed = len(check_results) - passed
    
    for test_name, result in check_results:
        status = "✅ 正常" if result else "❌ 異常"
        print(f"  {test_name:<12} {status}")
    
    print(f"\n總計: {passed} 項正常, {failed} 項異常")
    
    # 給出判斷建議
    print("\n" + "=" * 60)
    print("  如何在實際使用中驗證 Qwen 執行")
    print("=" * 60)
    
    print("方法1: 檢查網頁結果中的 '_qwen_audit' 欄位")
    print("  - executed: true/false")
    print("  - triggered_by: 'low_confidence'/'manual'") 
    print("  - qwen_invoked: > 0 表示真的調用API")
    print("  - learning_record_id: 有值表示記錄到學習系統")
    
    print("\n方法2: 查看學習統計API")
    print("  訪問: http://127.0.0.1:5000/learning/stats")
    print("  檢查: total_qwen_triggers 是否增加")
    
    print("\n方法3: 上傳一個複雜PDF測試")
    print("  選擇字跡模糊或格式不規整的PDF")
    print("  這類文件更容易觸發 < 92% 信心分數")
    
    print("\n方法4: 人工降低信心分數")
    print("  修改po_extractor/pipeline/confidence_scorer.py")
    print("  暫時降低評分標準來強制觸發")
    
    if failed == 0:
        print(f"\n🎉 系統檢查全部通過！Qwen仲裁機制已準備就緒")
    else:
        print(f"\n⚠️ 發現 {failed} 項問題，建議先修復再測試")

if __name__ == "__main__":
    main()