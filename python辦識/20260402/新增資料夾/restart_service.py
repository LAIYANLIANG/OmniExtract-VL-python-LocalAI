#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PO Extractor Web服務重啟腳本
清理暫存並重新初始化所有組件
"""
import os
import sys
import shutil
import logging
import importlib

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def clear_python_cache():
    """清理Python緩存"""
    cache_dirs = []
    pyc_files = []
    
    for root, dirs, files in os.walk('.'):
        # 尋找 __pycache__ 目錄
        if '__pycache__' in dirs:
            cache_dirs.append(os.path.join(root, '__pycache__'))
        
        # 尋找 .pyc 檔案
        for file in files:
            if file.endswith('.pyc'):
                pyc_files.append(os.path.join(root, file))
    
    # 刪除緩存目錄
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            logger.info(f"🗑️  已刪除: {cache_dir}")
        except Exception as e:
            logger.warning(f"無法刪除 {cache_dir}: {e}")
    
    # 刪除 .pyc 檔案
    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
            logger.info(f"🗑️  已刪除: {pyc_file}")
        except Exception as e:
            logger.warning(f"無法刪除 {pyc_file}: {e}")
    
    logger.info(f"✅ 清理完成: {len(cache_dirs)} 個緩存目錄, {len(pyc_files)} 個pyc檔案")

def clear_module_cache():
    """清理Python模組緩存"""
    modules_to_clear = []
    for module_name in list(sys.modules.keys()):
        if module_name.startswith('po_extractor'):
            modules_to_clear.append(module_name)
    
    for module_name in modules_to_clear:
        if module_name in sys.modules:
            del sys.modules[module_name]
            logger.info(f"🔄 已卸載模組: {module_name}")
    
    logger.info(f"✅ 已清理 {len(modules_to_clear)} 個po_extractor模組")

def check_dependencies():
    """檢查關鍵依賴"""
    required_modules = [
        'flask',
        'werkzeug', 
        'json',
        'os',
        'logging',
        'uuid',
        'datetime'
    ]
    
    missing = []
    for module in required_modules:
        try:
            importlib.import_module(module)
            logger.info(f"✅ {module}")
        except ImportError:
            missing.append(module)
            logger.error(f"❌ {module}")
    
    if missing:
        logger.error(f"缺少依賴: {', '.join(missing)}")
        return False
    
    logger.info("✅ 所有依賴檢查通過")
    return True

def create_minimal_webapp():
    """創建最小化的webapp來測試"""
    minimal_code = '''
import os
import sys
from flask import Flask

# 確保工作目錄正確
app = Flask(__name__)
app.config['SECRET_KEY'] = 'temp-key-for-restart'

@app.route('/')
def health_check():
    return """
    <h1>🚀 PO Extractor Service</h1>
    <p><strong>狀態:</strong> 服務正常運行</p>
    <p><strong>時間:</strong> """ + str(__import__('datetime').datetime.now()) + """</p>
    <p><strong>版本:</strong> Qwen3-VL Enhanced v2.0</p>
    <hr>
    <p>✅ 基礎服務已啟動</p>
    <p>🔄 完整功能載入中...</p>
    """

@app.route('/health')
def health():
    return {"status": "ok", "service": "po_extractor", "version": "2.0"}

if __name__ == '__main__':
    print("="*60)
    print("  🚀 PO Extractor - 緊急重啟模式")
    print("  服務地址: http://127.0.0.1:5000")
    print("="*60)
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
'''
    
    with open('restart_webapp.py', 'w', encoding='utf-8') as f:
        f.write(minimal_code)
    
    logger.info("✅ 已創建臨時webapp")

def main():
    """主執行函數"""
    logger.info("🔄 開始服務重啟程序...")
    
    # Step 1: 清理緩存
    logger.info("第1步: 清理Python緩存")
    clear_python_cache()
    
    # Step 2: 清理模組緩存  
    logger.info("第2步: 清理模組緩存")
    clear_module_cache()
    
    # Step 3: 檢查依賴
    logger.info("第3步: 檢查依賴")
    if not check_dependencies():
        logger.error("❌ 依賴檢查失敗，請先安裝必要套件")
        return False
    
    # Step 4: 創建目錄
    logger.info("第4步: 確保目錄結構")
    dirs_to_create = [
        'po_extractor/config',
        'uploads',
        'logs',
        'import_doc', 
        'output_doc',
        'results'
    ]
    
    for dir_name in dirs_to_create:
        os.makedirs(dir_name, exist_ok=True)
        logger.info(f"📁 已確保目錄: {dir_name}")
    
    # Step 5: 創建最小化webapp
    logger.info("第5步: 創建緊急webapp")
    create_minimal_webapp()
    
    logger.info("🎉 重新初始化完成！")
    logger.info("執行以下命令啟動服務:")
    logger.info("  py restart_webapp.py")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)