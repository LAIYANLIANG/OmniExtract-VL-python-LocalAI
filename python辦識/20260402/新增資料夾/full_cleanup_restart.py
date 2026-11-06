#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整清理並重啟 webapp
==================

清除所有 Python 暫存、模組緩存、Flask 緩存，然後重新啟動

使用方法: py full_cleanup_restart.py

作者: GitHub Copilot
日期: 2026-04-01
"""

import os
import sys
import time
import shutil
import subprocess
import importlib
from pathlib import Path

def kill_python_processes():
    """強制終止所有Python進程"""
    print("🔥 強制終止所有 Python 進程...")
    try:
        # 使用 taskkill 強制終止
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                      capture_output=True, check=False)
        subprocess.run(['taskkill', '/F', '/IM', 'py.exe'], 
                      capture_output=True, check=False)
        subprocess.run(['taskkill', '/F', '/IM', 'python3.exe'], 
                      capture_output=True, check=False)
        print("✅ Python 進程已終止")
    except Exception as e:
        print(f"⚠️ 進程終止警告: {e}")
    
    time.sleep(3)

def clear_python_cache():
    """清除所有 Python 暫存檔案"""
    print("🧹 清除 Python __pycache__ 目錄...")
    
    cache_dirs = []
    for root, dirs, files in os.walk("."):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                cache_path = os.path.join(root, dir_name)
                cache_dirs.append(cache_path)
    
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"  🗑️ 已刪除: {cache_dir}")
        except Exception as e:
            print(f"  ⚠️ 無法刪除 {cache_dir}: {e}")
    
    # 清除 .pyc 檔案
    print("🧹 清除 .pyc 檔案...")
    pyc_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith('.pyc'):
                pyc_path = os.path.join(root, file)
                pyc_files.append(pyc_path)
    
    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
            print(f"  🗑️ 已刪除: {pyc_file}")
        except Exception as e:
            print(f"  ⚠️ 無法刪除 {pyc_file}: {e}")

def clear_system_modules():
    """從 sys.modules 中清除所有 po_extractor 相關模組"""
    print("🔄 清除已載入的模組快取...")
    
    modules_to_remove = []
    for module_name in sys.modules.keys():
        if any(keyword in module_name for keyword in ['po_extractor', 'webapp', 'flask']):
            modules_to_remove.append(module_name)
    
    for module_name in modules_to_remove:
        try:
            del sys.modules[module_name]
            print(f"  🗑️ 已清除模組: {module_name}")
        except Exception as e:
            print(f"  ⚠️ 無法清除模組 {module_name}: {e}")

def clear_temp_files():
    """清除臨時檔案"""
    print("🧹 清除臨時檔案...")
    
    temp_patterns = [
        "*.tmp",
        "*.log", 
        "flask_session*",
        "temp_*"
    ]
    
    for pattern in temp_patterns:
        import glob
        files = glob.glob(pattern)
        for file in files:
            try:
                if os.path.isfile(file):
                    os.remove(file)
                    print(f"  🗑️ 已刪除: {file}")
                elif os.path.isdir(file):
                    shutil.rmtree(file)
                    print(f"  🗑️ 已刪除目錄: {file}")
            except Exception as e:
                print(f"  ⚠️ 無法刪除 {file}: {e}")

def verify_webapp_files():
    """驗證 webapp 相關檔案是否存在"""
    print("📋 驗證 webapp 檔案...")
    
    required_files = [
        "po_extractor/webapp.py",
        "po_extractor/templates/index.html", 
        "po_extractor/config/qwen_config.json",
        "po_extractor/pipeline/qwen_learning_system.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ 缺少: {file_path}")
            all_exist = False
    
    return all_exist

def create_uploads_dir():
    """確保 uploads 目錄存在"""
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
        print("  📁 已創建 uploads 目錄")
    else:
        print("  📁 uploads 目錄已存在")

def test_import():
    """測試能否正常導入模組"""
    print("🧪 測試模組導入...")
    try:
        # 重新導入
        import importlib
        import po_extractor.webapp
        importlib.reload(po_extractor.webapp)
        print("  ✅ po_extractor.webapp 導入成功")
        return True
    except Exception as e:
        print(f"  ❌ 模組導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def start_webapp():
    """啟動 webapp"""
    print("🚀 啟動 webapp...")
    try:
        # 重新導入 webapp
        import importlib
        import po_extractor.webapp
        
        # 強制重新載入
        importlib.reload(po_extractor.webapp)
        
        app = po_extractor.webapp.app
        
        # 清除 Flask 暫存
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.config['EXPLAIN_TEMPLATE_LOADING'] = True
        
        print("✅ webapp 啟動配置完成")
        print("🌐 訪問網址: http://127.0.0.1:5000")
        print("📝 包含 Qwen 仲裁視覺化標註功能")
        print("🎯 修復了\"資訊不明\"問題，現顯示\"📜 舊數據\"")
        print("")
        print("🔧 除錯資訊:")
        print("   - 92% 信心門檻已設定")
        print("   - Qwen 學習系統已整合") 
        print("   - 舊數據友善標註已修復")
        print("   - 4 種視覺化狀態標註")
        print("")
        print("⚡ 正在啟動 Flask 伺服器...")
        
        # 啟動伺服器
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False, threaded=True)
        
    except Exception as e:
        print(f"❌ webapp 啟動失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主清理與重啟流程"""
    print("=" * 60)
    print("🔧 完整清理並重啟 Qwen 仲裁 webapp")
    print(f"🕐 開始時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 步驟 1: 終止進程
    kill_python_processes()
    
    # 步驟 2: 清除暫存
    clear_python_cache()
    
    # 步驟 3: 清除模組
    clear_system_modules()
    
    # 步驟 4: 清除臨時檔案
    clear_temp_files()
    
    # 步驟 5: 驗證檔案
    if not verify_webapp_files():
        print("❌ 關鍵檔案缺失，請檢查專案完整性")
        return False
    
    # 步驟 6: 創建必要目錄
    create_uploads_dir()
    
    # 步驟 7: 測試導入
    if not test_import():
        print("❌ 模組導入失敗，無法啟動 webapp")
        return False
    
    print("\n" + "=" * 60)
    print("✅ 清理完成，正在啟動 webapp...")
    print("=" * 60)
    
    # 步驟 8: 啟動 webapp
    start_webapp()

if __name__ == "__main__":
    main()