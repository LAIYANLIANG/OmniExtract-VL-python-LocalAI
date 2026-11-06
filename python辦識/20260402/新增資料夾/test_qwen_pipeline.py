"""
Qwen3-VL 七步管道端對端測試腳本

Usage:
    python test_qwen_pipeline.py [--skip-models] [--test-file PATH]
"""
import os
import sys
import json
import time
import logging
import argparse
from typing import Dict, Any

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('pipeline_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_imports():
    """測試所有必要模組的導入"""
    logger.info("🔍 測試 Python 模組導入...")
    
    modules = [
        ('cv2', 'OpenCV'),
        ('paddleocr', 'PaddleOCR'),
        ('flask', 'Flask'),
        ('PIL', 'Pillow'),
        ('numpy', 'NumPy'),
        ('requests', 'Requests')
    ]
    
    failed = []
    for module, name in modules:
        try:
            __import__(module)
            logger.info(f"  ✅ {name}")
        except ImportError as e:
            logger.error(f"  ❌ {name}: {e}")
            failed.append(name)
    
    if failed:
        logger.error(f"模組導入失敗: {', '.join(failed)}")
        return False
    
    logger.info("✅ 所有 Python 模組導入成功")
    return True

def test_config_files():
    """測試配置檔案"""
    logger.info("🔍 測試配置檔案...")
    
    config_files = [
        'po_extractor/config/qwen_config.json',
        'po_extractor/config/image_processing_params.json',
        'po_extractor/config/vendor_image_profiles.json',
        'po_extractor/config/regex_rules.json',
        'po_extractor/config/learning_journal.json'
    ]
    
    missing = []
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                logger.info(f"  ✅ {config_file}")
            except json.JSONDecodeError as e:
                logger.error(f"  ❌ {config_file}: JSON 格式錯誤 - {e}")
                missing.append(config_file)
        else:
            logger.error(f"  ❌ {config_file}: 檔案不存在")
            missing.append(config_file)
    
    if missing:
        logger.error(f"配置檔案問題: {', '.join(missing)}")
        return False
    
    logger.info("✅ 所有配置檔案有效")
    return True

def test_ollama_connection():
    """測試 Ollama 連接"""
    logger.info("🔍 測試 Ollama 服務...")
    
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json()
            logger.info(f"  ✅ Ollama 服務運行中，已安裝 {len(models.get('models', []))} 個模型")
            
            # 檢查 Qwen 模型
            qwen_models = [m for m in models.get('models', []) if 'qwen' in m.get('name', '').lower()]
            if qwen_models:
                logger.info(f"  ✅ 找到 Qwen 模型: {[m['name'] for m in qwen_models]}")
                return True
            else:
                logger.warning("  ⚠️  未找到 Qwen 模型")
                return False
        else:
            logger.error(f"  ❌ Ollama API 回應錯誤: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"  ❌ 無法連接到 Ollama: {e}")
        logger.info("  💡 請確保 Ollama 已運行: ollama serve")
        return False

def test_pipeline_components():
    """測試管道組件"""
    logger.info("🔍 測試管道組件...")
    
    try:
        # 測試配置載入
        from po_extractor.pipeline.step1_preprocess import load_processing_params
        params = load_processing_params()
        logger.info("  ✅ Step1 OpenCV 預處理")
        
        # 測試清潔規則
        from po_extractor.pipeline.step3_clean import load_cleaning_rules
        rules = load_cleaning_rules()
        logger.info(f"  ✅ Step4 清潔規則 ({len(rules['rules'])} 條)")
        
        # 測試投票系統
        from po_extractor.pipeline.voting_system import VotingSystem
        voting = VotingSystem()
        logger.info("  ✅ 投票系統")
        
        # 測試反饋引擎
        from po_extractor.pipeline.feedback_engine import FeedbackEngine
        feedback = FeedbackEngine()
        logger.info("  ✅ 反饋引擎")
        
        # 測試協調器
        from po_extractor.pipeline.pipeline_orchestrator import get_orchestrator_instance
        orchestrator = get_orchestrator_instance()
        health = orchestrator.get_pipeline_health()
        logger.info(f"  ✅ 管道協調器 (健康狀態: {health.get('config_loaded', False)})")
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ 管道組件測試失敗: {e}")
        return False

def test_ocr_functionality():
    """測試 OCR 功能"""
    logger.info("🔍 測試 OCR 功能...")
    
    try:
        from paddleocr import PaddleOCR
        
        # 初始化 OCR（使用 CPU）
        logger.info("  初始化 PaddleOCR...")
        ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False, show_log=False)
        
        # 創建測試圖片
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        
        # 創建簡單的測試圖片
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # 嘗試使用默認字體
        try:
            # Windows 系統字體
            font = ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", 24)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
        
        draw.text((10, 30), "Test PO Number: PO123456", fill='black', font=font)
        
        # 轉換為 numpy array
        test_img = np.array(img)
        
        # 執行 OCR
        result = ocr.ocr(test_img, cls=True)
        
        if result and result[0]:
            extracted_text = ' '.join([item[1][0] for item in result[0] if item[1][1] > 0.5])
            logger.info(f"  ✅ OCR 測試成功: '{extracted_text}'")
            return True
        else:
            logger.warning("  ⚠️  OCR 未提取到文字")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ OCR 測試失敗: {e}")
        return False

def test_opencv_processing():
    """測試 OpenCV 圖片處理"""
    logger.info("🔍 測試 OpenCV 圖片處理...")
    
    try:
        import cv2
        import numpy as np
        
        # 創建測試圖片
        test_img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        cv2.putText(test_img, 'Test Image', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # 測試預處理操作
        from po_extractor.pipeline.step1_preprocess import load_processing_params
        params = load_processing_params()
        
        # 去噪
        denoised = cv2.bilateralFilter(test_img, 9, 75, 75)
        
        # 轉為灰度
        gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
        
        # 對比度調整
        enhanced = cv2.convertScaleAbs(gray, alpha=1.2, beta=10)
        
        logger.info("  ✅ OpenCV 基本操作成功")
        return True
        
    except Exception as e:
        logger.error(f"  ❌ OpenCV 測試失敗: {e}")
        return False

def test_full_pipeline(test_file_path: str = None):
    """測試完整管道"""
    logger.info("🔍 測試完整七步管道...")
    
    if not test_file_path:
        logger.warning("  ⚠️  未提供測試 PDF 檔案，跳過完整管道測試")
        return True
    
    if not os.path.exists(test_file_path):
        logger.error(f"  ❌ 測試檔案不存在: {test_file_path}")
        return False
    
    try:
        from po_extractor.pipeline.pipeline_orchestrator import process_po_document
        
        logger.info(f"  執行七步管道處理: {test_file_path}")
        start_time = time.time()
        
        result = process_po_document(
            test_file_path,
            enable_qwen_audit=False,  # 可能 Ollama 未準備好
            enable_layoutlm=False     # 避免需要額外模型
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if result.get('final_extraction'):
            logger.info(f"  ✅ 管道處理成功 ({processing_time:.2f}s)")
            logger.info(f"     步驟執行: {result['pipeline_stats']['steps_executed']}")
            logger.info(f"     步驟跳過: {result['pipeline_stats']['steps_skipped']}")
            return True
        else:
            logger.error("  ❌ 管道處理失敗，無提取結果")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ 完整管道測試失敗: {e}")
        return False

def run_all_tests(skip_models: bool = False, test_file: str = None):
    """執行所有測試"""
    logger.info("🚀 開始 Qwen3-VL 七步管道測試")
    logger.info("="*50)
    
    tests = [
        ("Python 模組導入", test_imports),
        ("配置檔案", test_config_files),
        ("管道組件", test_pipeline_components),
        ("OpenCV 處理", test_opencv_processing),
    ]
    
    if not skip_models:
        tests.extend([
            ("Ollama 連接", test_ollama_connection),
            ("OCR 功能", test_ocr_functionality),
        ])
        
        if test_file:
            tests.append(("完整管道", lambda: test_full_pipeline(test_file)))
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"測試異常: {e}")
            failed += 1
    
    logger.info("\n" + "="*50)
    logger.info(f"📊 測試結果: {passed} 通過, {failed} 失敗")
    
    if failed == 0:
        logger.info("🎉 所有測試通過！系統已準備就緒。")
        return True
    else:
        logger.warning(f"⚠️  {failed} 個測試失敗，請檢查安裝。")
        return False

def main():
    parser = argparse.ArgumentParser(description='Qwen3-VL Pipeline Test Suite')
    parser.add_argument('--skip-models', action='store_true', 
                       help='跳過需要模型的測試（Ollama、OCR）')
    parser.add_argument('--test-file', type=str, 
                       help='用於完整管道測試的 PDF 檔案路徑')
    
    args = parser.parse_args()
    
    success = run_all_tests(skip_models=args.skip_models, test_file=args.test_file)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()