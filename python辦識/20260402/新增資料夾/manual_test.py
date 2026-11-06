#!/usr/bin/env python3
"""
手動功能測試 - 驗證所有實現的功能
"""

import requests
import json
import os

BASE_URL = "http://127.0.0.1:5001"

def test_comprehensive():
    """綜合測試所有功能"""
    print("🎯 綜合功能測試")
    print("="*50)
    
    # 1. 測試首頁
    print("1️⃣ 測試首頁訪問...")
    response = requests.get(BASE_URL)
    if response.status_code == 200:
        print("   ✅ 首頁正常 (200)")
    else:
        print(f"   ❌ 首頁錯誤 ({response.status_code})")
    
    # 2. 測試PDF處理（包含page_info）
    print("\n2️⃣ 測試PDF處理...")
    test_pdf = 'import_doc/finish/DESAY_SV/6300002706.pdf'
    if os.path.exists(test_pdf):
        with open(test_pdf, 'rb') as f:
            files = {'files': (os.path.basename(test_pdf), f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/upload", files=files)
        
        if response.status_code == 200:
            result = response.json()
            if result['results'] and result['results'][0]['status'] != 'error':
                print(f"   ✅ PDF處理成功 - 準確率: {result['results'][0].get('accuracy_pct', 'N/A')}%")
                json_path = result['results'][0].get('json_path')
                
                # 檢查_page_info是否存在
                if json_path:
                    with open(f'output_doc/{json_path}', 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if '_page_info' in data:
                        print(f"   ✅ 頁面資訊已生成 - 共{data['_page_info']['total_pages']}頁")
                    else:
                        print("   ❌ 沒有頁面資訊")
            else:
                print(f"   ❌ PDF處理失敗: {result['results'][0].get('message', 'Unknown error')}")
        else:
            print(f"   ❌ 上傳失敗 ({response.status_code})")
    else:
        print(f"   ❌ 測試文件不存在: {test_pdf}")
    
    # 3. 測試PDF分頁API  
    print("\n3️⃣ 測試PDF分頁API...")
    response = requests.get(f"{BASE_URL}/pdf-pages/DESAY_SV/6300002706.json")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 分頁API正常 - 共{result.get('total_pages', 0)}頁")
        if result.get('pages'):
            print(f"   ✅ 頁面內容獲取成功 - 首頁字符數: {len(result['pages'][0].get('text', ''))}")
    else:
        print(f"   ❌ 分頁API錯誤 ({response.status_code})")
    
    # 4. 測試預訓練API
    print("\n4️⃣ 測試預訓練API...")
    test_pdf = 'samples/sample_order.pdf'
    if os.path.exists(test_pdf):
        with open(test_pdf, 'rb') as f:
            files = {'pdf': (os.path.basename(test_pdf), f, 'application/pdf')}
            data = {
                'vendor_id': 'Vendor_A',
                'fields': json.dumps({
                    'company.name': 'Sample Tech Corp',
                    'po.number': 'PO-998877',
                    'contact.person': 'Test Person'
                })
            }
            response = requests.post(f"{BASE_URL}/pretrain", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 預訓練成功 - 學習了{result.get('patterns_learned', 0)}個模式")
        else:
            print(f"   ❌ 預訓練失敗 ({response.status_code}): {response.text[:100]}")
    else:
        print(f"   ❌ 測試文件不存在: {test_pdf}")
    
    print("\n" + "="*50)
    print("🎉 綜合測試完成！")

if __name__ == "__main__":
    test_comprehensive()