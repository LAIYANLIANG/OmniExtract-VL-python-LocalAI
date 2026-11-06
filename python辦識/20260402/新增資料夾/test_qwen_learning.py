#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen學習系統測試腳本
==================

測試以下功能：
1. Qwen2-VL:7B 連接測試
2. 92%信心分數閾值觸發
3. 學習記錄系統
4. 改進模式應用

使用方法: py test_qwen_learning.py

作者: GitHub Copilot  
日期: 2026-04-01
"""

import os
import sys
import json
import requests
from datetime import datetime

# 確保正確的工作目錄
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

def test_ollama_connection():
    """測試Ollama服務連接"""
    print("🔧 測試 1: Ollama 服務連接")
    try:
        response = requests.get("http://localhost:11434", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama 服務正常運行")
            return True
        else:
            print(f"❌ Ollama 回應異常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama 連接失敗: {e}")
        return False

def test_qwen_model():
    """測試Qwen2-VL模型可用性"""
    print("\n🔧 測試 2: Qwen2-VL 模型")
    try:
        # 獲取模型列表
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            # 檢查qwen模型  
            qwen_models = [name for name in model_names if "qwen" in name.lower()]
            if qwen_models:
                print(f"✅ 找到Qwen模型: {qwen_models}")
                return qwen_models[0]
            else:
                print(f"❌ 未找到Qwen模型")
                print(f"   可用模型: {model_names}")
                return None
        else:
            print(f"❌ 模型列表獲取失敗: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 模型檢查失敗: {e}")
        return None

def test_qwen_inference(model_name):
    """測試Qwen推論功能"""
    print(f"\n🔧 測試 3: Qwen 推論 ({model_name})")
    try:
        payload = {
            "model": model_name,
            "prompt": "請回覆 'OK' 一個字",
            "stream": False
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate", 
            json=payload, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("response", "").strip()
            print(f"✅ Qwen 推論成功")
            print(f"   問題: {payload['prompt']}")
            print(f"   回答: {answer}")
            return True
        else:
            print(f"❌ Qwen推論失敗: {response.status_code}")
            print(f"   回應: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Qwen推論異常: {e}")
        return False

def test_learning_system():
    """測試學習系統"""
    print(f"\n🔧 測試 4: Qwen 學習系統")
    try:
        from po_extractor.pipeline.qwen_learning_system import QwenLearningSystem
        
        learning_system = QwenLearningSystem()
        
        # 測試記錄觸發事件
        record_id = learning_system.record_qwen_trigger(
            pdf_path="/test/dummy.pdf",
            raw_text="Test PO document content",
            confidence_score=0.85,  # 低於92%閾值
            low_confidence_fields=["po_number", "vendor_name"],
            vendor_type="TEST_VENDOR",
            original_extraction={"po_number": "1234567890", "vendor_name": "Test Corp"},
            trigger_reason="low_confidence"
        )
        
        print(f"✅ 學習記錄建立成功")
        print(f"   記錄ID: {record_id}")
        
        # 測試記錄Qwen修正
        qwen_corrections = {
            "po_number": {
                "old_value": "1234567890", 
                "new_value": "PO1234567890",
                "confidence": 0.95
            }
        }
        learning_system.update_qwen_corrections(record_id, qwen_corrections)
        print(f"✅ Qwen修正記錄成功")
        
        # 測試人工修正
        manual_corrections = {
            "vendor_name": "Corrected Test Corp"
        }
        final_extraction = {
            "po_number": "PO1234567890",
            "vendor_name": "Corrected Test Corp"
        }
        learning_system.record_manual_corrections(record_id, manual_corrections, final_extraction)
        print(f"✅ 人工修正記錄成功")
        
        # 獲取統計
        stats = learning_system.get_usage_statistics()
        print(f"✅ 統計資料:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 學習系統測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_webapp_integration():
    """測試Webapp整合"""
    print(f"\n🔧 測試 5: Webapp 整合")
    try:
        # 檢查webapp是否運行
        response = requests.get("http://127.0.0.1:5000", timeout=5)
        if response.status_code == 200:
            print("✅ Flask Webapp 正常運行")
            
            # 測試學習統計API
            stats_response = requests.get("http://127.0.0.1:5000/learning/stats", timeout=5)
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                print(f"✅ 學習統計API正常")
                print(f"   閾值設定: {stats_data.get('threshold_config', {}).get('confidence_threshold')*100:.0f}%")
            else:
                print(f"⚠️ 學習統計API異常: {stats_response.status_code}")
            
            return True
        else:
            print(f"❌ Webapp無回應: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException:
        print("❌ Webapp未運行 (這是正常的，請先啟動webapp)")
        return False
    except Exception as e:
        print(f"❌ Webapp整合測試失敗: {e}")
        return False

def test_configuration():
    """測試配置檔案"""
    print(f"\n🔧 測試 6: 配置檔案")
    
    config_path = "po_extractor/config/qwen_config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        model_id = config.get("runtime", {}).get("model_id")
        confidence_threshold = config.get("learning", {}).get("confidence_threshold")
        
        print(f"✅ 配置檔案載入成功")  
        print(f"   模型ID: {model_id}")
        print(f"   信心閾值: {confidence_threshold*100:.0f}%")
        
        if "qwen2-vl" in model_id.lower():
            print(f"✅ 模型配置正確")
        else:
            print(f"⚠️ 模型配置可能需要調整")
            
        if confidence_threshold == 0.92:
            print(f"✅ 92%閾值設定正確")
        else:
            print(f"⚠️ 閾值設定: {confidence_threshold*100:.0f}% (預期:92%)")
            
        return True
        
    except Exception as e:
        print(f"❌ 配置檔案測試失敗: {e}")
        return False

def main():
    """主測試流程"""
    print("=" * 60)
    print("  Qwen2-VL 學習系統整合測試")
    print("  2026-04-01")
    print("=" * 60)
    
    test_results = []
    
    # 執行測試
    test_results.append(("Ollama連接", test_ollama_connection()))
    
    # 測試模型
    model_name = test_qwen_model()
    if model_name:
        test_results.append(("Qwen模型", True))
        test_results.append(("Qwen推論", test_qwen_inference(model_name)))
    else:
        test_results.append(("Qwen模型", False))
        test_results.append(("Qwen推論", False))
    
    test_results.append(("學習系統", test_learning_system()))
    test_results.append(("Webapp整合", test_webapp_integration()))
    test_results.append(("配置檔案", test_configuration()))
    
    # 結果總結
    print("\n" + "=" * 60)
    print("  測試結果總結")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name:<12} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n  總計: {passed} 通過, {failed} 失敗")
    
    if failed == 0:
        print("\n🎉 所有測試通過！系統已準備就緒")
    else:
        print(f"\n⚠️ {failed} 項測試失敗，請檢查系統設定")
    
    print("\n" + "=" * 60)
    print("  使用指南")
    print("=" * 60)
    print("  1. 啟動Ollama: 從開始選單啟動或執行:")
    print('     "C:\\Users\\localadmin\\AppData\\Local\\Programs\\Ollama\\ollama.exe" serve')
    print("  2. 啟動Webapp: py -m po_extractor.webapp")
    print("  3. 開啟瀏覽器: http://127.0.0.1:5000")
    print("  4. 上傳PDF檔案進行測試")
    print("=" * 60)

if __name__ == "__main__":
    main()