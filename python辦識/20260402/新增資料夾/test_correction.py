#!/usr/bin/env python3
"""
測試審核修正和自動學習功能
"""

import requests
import json
import os
import time

BASE_URL = "http://127.0.0.1:5000"

def test_correction_and_learning():
    """測試修正保存和自動學習功能"""
    print("🧪 測試審核修正和自動學習功能")
    print("="*50)
    
    # 1. 檢查是否有現有的結果檔案可以測試
    try:
        response = requests.get(f"{BASE_URL}/results")
        if response.status_code == 200:
            results = response.json()
            if results and len(results) > 0:
                test_file = results[0]  # 使用第一個結果檔案
                print(f"✅ 找到測試檔案: {test_file['filename']}")
                
                # 2. 模擬一個修正請求
                test_correction_data = {
                    "filepath": f"{test_file['vendor_folder']}/{test_file['filename'].replace('.pdf', '.json')}",
                    "data": {
                        "vendor_id": test_file['vendor_id'],
                        "purchase_info": {
                            "po_number": test_file['po_number'],
                            "date": test_file['date'],
                            "buyer": "測試修正買家",  # 修正的欄位
                            "total_amount": test_file['total_amount']
                        },
                        "vendor_info": {
                            "name": "測試修正供應商名稱",  # 修正的欄位
                            "contact": "測試聯絡人"
                        }
                    }
                }
                
                print(f"📝 提交修正數據...")
                response = requests.post(f"{BASE_URL}/save-correction", 
                                       json=test_correction_data,
                                       headers={'Content-Type': 'application/json'})
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ 修正保存成功")
                    print(f"   狀態: {result.get('status')}")
                    print(f"   路徑: {result.get('path')}")
                    
                    # 檢查學習結果
                    if 'learning_stats' in result:
                        stats = result['learning_stats']
                        print("🧠 自動學習結果:")
                        print(f"   處理檔案: {stats.get('files_processed', 0)}")
                        print(f"   學習欄位: {stats.get('fields_learned', 0)}")
                        print(f"   生成模式: {stats.get('patterns_generated', 0)}")
                        
                        if stats.get('patterns_generated', 0) > 0:
                            print("✅ 成功生成學習模式！")
                        else:
                            print("⚠️ 未生成新的學習模式")
                    elif 'learning_error' in result:
                        print(f"❌ 自動學習失敗: {result['learning_error']}")
                    else:
                        print("⚠️ 未包含學習結果信息")
                        
                else:
                    print(f"❌ 修正保存失敗: {response.status_code}")
                    print(f"   響應: {response.text}")
                    
            else:
                print("❌ 沒有找到可用的結果檔案進行測試")
        else:
            print(f"❌ 無法獲取結果列表: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

def test_learning_application():
    """測試學習模式的應用"""
    print("\n🔄 測試學習模式應用...")
    
    # 檢查是否有學習到的模式檔案
    if os.path.exists('learned_patterns.json'):
        with open('learned_patterns.json', 'r', encoding='utf-8') as f:
            patterns = json.load(f)
        
        print(f"📁 現有學習模式檔案包含 {len(patterns)} 個供應商的模式")
        for vendor, fields in patterns.items():
            print(f"   {vendor}: {len(fields)} 個欄位模式")
        
        print("✅ 學習模式檔案存在，處理PDF時會自動應用這些模式")
    else:
        print("⚠️ 尚未有學習模式檔案，需要先進行一些修正才能生成")

if __name__ == "__main__":
    # 等待Flask啟動
    time.sleep(1)
    
    test_correction_and_learning()
    test_learning_application()
    
    print("\n" + "="*50)
    print("🎯 測試完成！")
    print("\n💡 使用方法:")
    print("1. 上傳PDF檔案進行處理")
    print("2. 點擊結果中的「審核/校正」")
    print("3. 修改欄位內容後點擊「💾 儲存校正」")
    print("4. 系統會自動保存並學習，下次處理相同供應商文檔時會應用學習結果")