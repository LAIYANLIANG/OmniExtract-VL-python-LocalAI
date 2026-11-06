#!/usr/bin/env python3  
# -*- coding: utf-8 -*-
"""
安全的 PO Extractor Web 服務啟動腳本
分階段載入功能，確保服務穩定運行
"""
import os
import sys
import logging
import importlib

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('webapp_startup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def safe_import(module_path, description, required=True):
    """安全導入模組"""
    try:
        module = importlib.import_module(module_path)
        logger.info(f"✅ {description}")
        return module
    except Exception as e:
        if required:
            logger.error(f"❌ {description}: {e}")
            raise
        else:
            logger.warning(f"⚠️  {description}: {e} (已跳過)")
            return None

def create_enhanced_webapp():
    """創建增強版webapp"""
    webapp_code = '''
import os
import sys
import json
import logging
import uuid
from datetime import datetime

from flask import (
    Flask, render_template, request, jsonify,
    send_from_directory, redirect, url_for
)
from werkzeug.utils import secure_filename

# 確保工作目錄正確
_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_DIR = os.path.dirname(_PACKAGE_DIR)
if _WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, _WORKSPACE_DIR)

# 基本導入
from po_extractor.pipeline.step2_extract import extract_text_from_pdf
from po_extractor.pipeline.step3_clean import clean_text_preserve_structure  
from po_extractor.pipeline.step4_classify import classify_vendor
from po_extractor.extractors.registry import ExtractorRegistry
import po_extractor.extractors  # noqa: F401 - trigger registration
from po_extractor.config import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR, DEFAULT_FINISH_DIR, VENDOR_FOLDER_MAP
from po_extractor.config import DEFAULT_CORRECTED_DIR, LEARNED_PATTERNS_PATH

# 可選導入 (新功能)
enhanced_features = {}
try:
    from po_extractor.pipeline.pipeline_orchestrator import process_po_document, get_orchestrator_instance
    enhanced_features['orchestrator'] = True
    logging.info("✅ 七步管道功能已載入")
except Exception as e:
    enhanced_features['orchestrator'] = False
    logging.warning(f"⚠️  七步管道功能未載入: {e}")

try:
    from po_extractor.pipeline.step7_qwen_audit import QwenClient
    from po_extractor.pipeline.feedback_engine import FeedbackEngine
    enhanced_features['qwen'] = True
    logging.info("✅ Qwen增強功能已載入")
except Exception as e:
    enhanced_features['qwen'] = False
    logging.warning(f"⚠️  Qwen增強功能未載入: {e}")

# 其他必要導入
import shutil
from po_extractor.pipeline.confidence_scorer import score_purchase_order
from po_extractor.pipeline.learning_advisor import suggest_learning_opportunities, apply_learning_suggestions
from po_extractor.pipeline.knowledge_base import KnowledgeBase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    template_folder=os.path.join(_PACKAGE_DIR, 'templates'),
    static_folder=os.path.join(_PACKAGE_DIR, 'static'),
)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

ALLOWED_EXTENSIONS = {'.pdf'}
IMPORT_DIR = DEFAULT_INPUT_DIR
OUTPUT_DIR = DEFAULT_OUTPUT_DIR
FINISH_DIR = DEFAULT_FINISH_DIR
CORRECTED_DIR = DEFAULT_CORRECTED_DIR

# 確保目錄存在
os.makedirs(IMPORT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True) 
os.makedirs(CORRECTED_DIR, exist_ok=True)

# 全局變量（用於可選功能）
qwen_client = None
feedback_engine = None


@app.route('/')
def index():
    """主頁"""
    return render_template('index.html', 
                         enhanced_features=enhanced_features,
                         version="v2.0-Qwen Enhanced",
                         vendors=ExtractorRegistry.list_vendors())


@app.route('/health')
def health():
    """健康檢查"""
    return {
        "status": "ok", 
        "service": "po_extractor", 
        "version": "2.0",
        "enhanced_features": enhanced_features
    }


# === Qwen增強功能端點 (條件載入) ===
if enhanced_features.get('qwen') and enhanced_features.get('orchestrator'):
    
    @app.route('/qwen/process', methods=['POST'])
    def qwen_enhanced_process():
        """使用完整七步管道處理PDF"""
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '' or not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Please select a PDF file"}), 400
        
        # 儲存檔案
        safe_name = secure_filename(file.filename) or f"{uuid.uuid4().hex[:8]}.pdf"
        temp_path = os.path.join(IMPORT_DIR, safe_name)
        file.save(temp_path)
        
        try:
            # 使用七步管道處理
            result = process_po_document(
                temp_path,
                enable_qwen_audit=request.form.get('enable_qwen_audit', 'false').lower() == 'true',
                enable_layoutlm=request.form.get('enable_layoutlm', 'false').lower() == 'true'
            )
            
            return jsonify({
                "status": "success",
                "filename": safe_name,
                "processing_time": result['pipeline_stats']['total_time'],
                "steps_executed": result['pipeline_stats']['steps_executed'],
                "qwen_used": not result['steps_results'].get('step7', {}).get('skipped', True),
                "result": result['final_extraction']
            })
            
        except Exception as e:
            logger.error(f"Qwen processing failed: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            try:
                os.remove(temp_path)
            except:
                pass
    
    @app.route('/qwen/status')
    def qwen_status():
        """Qwen系統狀態"""
        try:
            orchestrator = get_orchestrator_instance()
            health = orchestrator.get_pipeline_health()
            return jsonify({
                "qwen_available": health.get('qwen_status', False),
                "pipeline_health": health,
                "enhanced_features": enhanced_features
            })
        except Exception as e:
            return jsonify({"error": str(e), "qwen_available": False}), 500


# === 傳統功能端點 (向後相容) ===
@app.route('/upload', methods=['POST'])
def upload_files():
    """上傳並處理PDF檔案 (傳統模式)"""
    if 'files' not in request.files:
        return jsonify({"error": "No files uploaded"}), 400

    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({"error": "No files selected"}), 400

    results = []
    for file in files:
        if not file.filename:
            continue

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": f"不支援的檔案類型: {ext}",
            })
            continue

        # 儲存檔案
        safe_name = secure_filename(file.filename)
        if not safe_name:
            safe_name = f"{uuid.uuid4().hex[:8]}.pdf"
        temp_path = os.path.join(IMPORT_DIR, safe_name) 
        file.save(temp_path)

        # 處理檔案
        try:
            # 使用增強處理或傳統處理
            if enhanced_features.get('orchestrator'):
                result = process_po_document(temp_path, enable_qwen_audit=False)
                extraction = result['final_extraction']
            else:
                # 傳統處理流程
                from po_extractor.main import process_single_pdf
                from po_extractor.config import DEFAULT_OUTPUT_DIR, DEFAULT_FINISH_DIR
                extraction = process_single_pdf(temp_path, DEFAULT_OUTPUT_DIR, DEFAULT_FINISH_DIR)
            
            results.append({
                "filename": file.filename,
                "status": "success", 
                "extraction": extraction
            })
            
        except Exception as e:
            logger.error(f"Processing failed for {safe_name}: {e}")
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e),
            })

    return jsonify({"results": results})


if __name__ == '__main__':
    print("=" * 60)
    print("  🚀 PO PDF Feature Extractor - Enhanced Web Interface")
    print(f"  Input:     {os.path.abspath(IMPORT_DIR)}")
    print(f"  Output:    {os.path.abspath(OUTPUT_DIR)}")
    print(f"  Corrected: {os.path.abspath(CORRECTED_DIR)}")
    print(f"  Vendors:   {', '.join(ExtractorRegistry.list_vendors())}")
    print("  ╭─────────────────────────────")
    print(f"  │ 七步管道: {'✅ 已啟用' if enhanced_features.get('orchestrator') else '❌ 未載入'}")
    print(f"  │ Qwen功能: {'✅ 已啟用' if enhanced_features.get('qwen') else '❌ 未載入'}")
    print("  ╰─────────────────────────────")
    print("=" * 60)
    print("  開啟瀏覽器訪問: http://127.0.0.1:5000")
    print("=" * 60)
    
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
'''
    
    with open('webapp_safe.py', 'w', encoding='utf-8') as f:
        f.write(webapp_code)
    
    logger.info("✅ 已創建安全版webapp")

def main():
    """主啟動程序"""
    logger.info("🚀 啟動安全版 PO Extractor Web 服務...")
    
    # 檢查基本環境
    logger.info("階段1: 檢查基本環境")
    safe_import('flask', 'Flask Web框架', required=True)
    safe_import('werkzeug', 'Werkzeug WSGI工具包', required=True)
    
    # 檢查po_extractor基本功能
    logger.info("階段2: 檢查po_extractor基本功能")
    safe_import('po_extractor.config', 'po_extractor配置', required=True)
    safe_import('po_extractor.pipeline.step2_extract', '文字提取模組', required=True)
    safe_import('po_extractor.pipeline.step4_classify', '供應商分類模組', required=True)
    
    # 檢查增強功能 (可選)
    logger.info("階段3: 檢查增強功能")
    safe_import('po_extractor.pipeline.pipeline_orchestrator', '七步管道協調器', required=False)
    safe_import('po_extractor.pipeline.step7_qwen_audit', 'Qwen審核模組', required=False)
    
    # 創建安全webapp
    logger.info("階段4: 創建安全版webapp")
    create_enhanced_webapp()
    
    logger.info("🎉 安全版webapp已準備就緒!")
    logger.info("執行: py webapp_safe.py")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)