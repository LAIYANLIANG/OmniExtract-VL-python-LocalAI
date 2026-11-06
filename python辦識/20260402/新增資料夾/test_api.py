#!/usr/bin/env python3
"""
API測試腳本
測試新實現的功能：
1. PDF上傳和處理
2. PDF分頁內容獲取 
3. 預訓練功能
"""

import requests
import json
import os

BASE_URL = "http://127.0.0.1:5001"

def test_homepage():
    """測試首頁"""
    try:
        response = requests.get(BASE_URL)
        print(f"✅ 首頁測試 - 狀態碼: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 首頁測試失敗: {e}")
        return False

def test_pdf_processing():
    """測試PDF處理功能"""
    # 使用現有的PDF檔案進行測試
    test_pdf = "import_doc/finish/BYD/3100544305Integrated_silicon_solutionCaymon.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"❌ 測試PDF檔案不存在: {test_pdf}")
        return False
        
    try:
        with open(test_pdf, 'rb') as f:
            files = {'files': (os.path.basename(test_pdf), f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/upload", files=files)
            
        print(f"✅ PDF上傳測試 - 狀態碼: {response.status_code}")  
        
        if response.status_code == 200:
            result = response.json()
            if 'filename' in result:
                print(f"   檔案名稱: {result['filename']}")
                return True
            
    except Exception as e:
        print(f"❌ PDF處理測試失敗: {e}")
        return False
        
    return False

def test_pdf_pages_api():
    """測試PDF分頁API"""
    # 先檢查是否有處理過的結果檔案
    results_dir = "results"
    if not os.path.exists(results_dir):
        print(f"❌ 結果目錄不存在: {results_dir}")
        return False
        
    result_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
    if not result_files:
        print("❌ 沒有找到結果檔案")
        return False
        
    # 使用第一個結果檔案測試
    test_file = result_files[0]
    try:
        response = requests.get(f"{BASE_URL}/pdf-pages/{test_file}")
        print(f"✅ PDF分頁API測試 - 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'pages' in result:
                print(f"   分頁數量: {len(result['pages'])}")
                return True
                
    except Exception as e:
        print(f"❌ PDF分頁API測試失敗: {e}")
        return False
        
    return False

def test_pretrain_api():
    """測試預訓練API"""
    test_pdf = "import_doc/finish/BYD/3100544305Integrated_silicon_solutionCaymon.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"❌ 測試PDF檔案不存在: {test_pdf}")
        return False
        
    try:
        with open(test_pdf, 'rb') as f:
            files = {'file': (os.path.basename(test_pdf), f, 'application/pdf')}
            data = {
                'vendor': 'BYD',
                'fields': json.dumps({
                    'company.name': 'BYD Company Limited',
                    'po.number': '3100544305'
                })
            }
            response = requests.post(f"{BASE_URL}/pretrain", files=files, data=data)
            
        print(f"✅ 預訓練API測試 - 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'patterns_learned' in result:
                print(f"   學習模式數: {result['patterns_learned']}")
                return True
                
    except Exception as e:
        print(f"❌ 預訓練API測試失敗: {e}")
        return False
        
    return False

def main():
    """執行所有測試"""
    print("🚀 開始API功能測試\n")
    
    tests = [
        ("首頁訪問", test_homepage),
        ("PDF處理", test_pdf_processing),
        ("PDF分頁API", test_pdf_pages_api),
        ("預訓練API", test_pretrain_api)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 測試: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"   測試失敗")
            
    print(f"\n📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！系統運行正常")
    else:
        print("⚠️ 部分測試失敗，請檢查問題")

if __name__ == "__main__":
    main()