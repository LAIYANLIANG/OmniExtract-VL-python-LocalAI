#!/usr/bin/env python3
"""
PO Extractor 新功能演示
展示頁面分組審核和預訓練功能

使用方法:
1. 首先啟動 Flask 應用: py -m po_extractor.webapp  
2. 打開瀏覽器訪問: http://127.0.0.1:5000
3. 體驗新功能:
   - 上傳PDF後查看按頁分組的審核面板
   - 使用預訓練功能提供學習數據

新功能亮點:
✅ 頁面分組顯示: 不同頁面用不同顏色標示，方便查看
✅ 欄位來源追蹤: 每個欄位顯示來自哪一頁
✅ 動態欄位管理: 可新增、刪除、重命名欄位
✅ 預訓練學習: 直接上傳PDF+正確數據讓系統學習
"""

import os
import sys
import subprocess
import webbrowser
import time
import requests

def check_dependencies():
    """檢查必要依賴"""
    missing = []
    try:
        import flask
    except ImportError:
        missing.append('flask')
    
    try:
        import pdfplumber  
    except ImportError:
        missing.append('pdfplumber')
        
    try:
        import requests
    except ImportError:
        missing.append('requests')
    
    if missing:
        print(f"❌ 缺少依賴包: {', '.join(missing)}")
        print(f"請執行: py -m pip install {' '.join(missing)}")
        return False
    return True

def start_flask_app():
    """啟動 Flask 應用"""
    print("🚀 正在啟動 PO Extractor...")
    
    try:
        # 檢查是否已有服務在運行
        try:
            response = requests.get('http://127.0.0.1:5000', timeout=2)
            if response.status_code == 200:
                print("✅ 服務已在運行中")
                return True
        except:
            pass
            
        # 啟動新的服務
        process = subprocess.Popen([
            sys.executable, '-m', 'po_extractor.webapp'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服務啟動
        print("⏳ 等待服務啟動...")
        for i in range(10):
            time.sleep(1)
            try:
                response = requests.get('http://127.0.0.1:5000', timeout=2)
                if response.status_code == 200:
                    print("✅ Flask 應用啟動成功")
                    return True
            except:
                continue
                
        print("❌ 服務啟動失敗")
        return False
        
    except Exception as e:
        print(f"❌ 啟動錯誤: {e}")
        return False

def show_demo_instructions():
    """顯示演示說明"""
    print("\n" + "="*60)
    print("🎯 PO Extractor 新功能演示")
    print("="*60)
    print()
    print("📋 演示步驟:")
    print("1. 上傳PDF檔案進行處理")
    print("2. 點擊 '審核/校正' 查看新的頁面分組顯示")
    print("3. 觀察不同頁面用不同顏色區分") 
    print("4. 點擊頁面標題展開查看原始文本")
    print("5. 嘗試新增、刪除、重命名欄位")
    print("6. 在首頁使用 '預訓練' 功能提供學習數據")
    print()
    print("🌟 主要新功能:")
    print("• 📄 頁面分組: 按PDF頁面組織欄位，顏色編碼")
    print("• 🎯 欄位追蹤: 顯示每個欄位來自哪一頁")  
    print("• ✏️  欄位管理: 動態新增/刪除/重命名欄位")
    print("• 🧠 預訓練: 上傳PDF+正確數據進行學習")
    print("• 📊 視覺優化: 更直觀的審核介面設計")
    print()
    print("💡 建議測試檔案:")
    for pdf_file in [
        "samples/sample_order_a.pdf",
        "samples/sample_order_b.pdf",
        "samples/sample_order_c.pdf"
    ]:
        if os.path.exists(pdf_file):
            print(f"   ✅ {os.path.basename(pdf_file)}")
        else:
            print(f"   ❌ {os.path.basename(pdf_file)} (不存在)")
    print()
    print("="*60)

def main():
    """主程式"""
    print("PO Extractor 新功能演示啟動器")
    print("作者: GitHub Copilot AI Assistant")
    print("版本: 2.0 (包含頁面分組和預訓練功能)")
    print()

    # 檢查依賴
    if not check_dependencies():
        return
    
    # 檢查是否在正確目錄
    if not os.path.exists('po_extractor'):
        print("❌ 請在專案根目錄執行此腳本")
        print("   當前目錄應包含 po_extractor 資料夾")
        return
    
    # 啟動服務
    if not start_flask_app():
        print("無法啟動服務，請手動執行: py -m po_extractor.webapp")
        return
    
    # 顯示說明
    show_demo_instructions()
    
    # 打開瀏覽器
    print("🌐 正在打開瀏覽器...")
    try:
        webbrowser.open('http://127.0.0.1:5000')
        print("✅ 瀏覽器已打開")
    except Exception as e:
        print(f"❌ 無法自動打開瀏覽器: {e}")
        print("   請手動開啟: http://127.0.0.1:5000")
    
    print("\n🎉 演示準備完成！請在瀏覽器中體驗新功能")
    print("按 Ctrl+C 停止服務")
    
    try:
        input("\n按 Enter 鍵退出...")
    except KeyboardInterrupt:
        print("\n👋 演示結束")

if __name__ == "__main__":
    main()