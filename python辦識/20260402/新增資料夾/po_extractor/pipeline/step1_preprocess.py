"""Step 1: OpenCV 影像診斷與手術（強化版）."""
import json
import logging
import os
from typing import Dict, Any, Optional, Tuple
import numpy as np


def load_processing_params(vendor_id: Optional[str] = None) -> Dict[str, Any]:
    """載入影像處理參數（支援供應商特定設定）"""
    params_path = "po_extractor/config/image_processing_params.json"
    
    try:
        with open(params_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 起始參數
        params = config["default"].copy()
        
        # 套用供應商特定參數
        if vendor_id and vendor_id in config.get("vendor_overrides", {}):
            params.update(config["vendor_overrides"][vendor_id])
            
        return params
        
    except Exception as e:
        logging.warning(f"Failed to load processing params: {e}")
        return {
            "denoise_strength": 10,
            "binary_threshold": 127,
            "contrast_alpha": 1.0,
            "contrast_beta": 0,
            "deskew_enabled": True
        }


def load_vendor_feedback(vendor_id: Optional[str] = None) -> Dict[str, Any]:
    """載入供應商的 Qwen 回饋建議"""
    profiles_path = "po_extractor/config/vendor_image_profiles.json"
    
    try:
        with open(profiles_path, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
        
        if vendor_id and vendor_id in profiles:
            suggestions = profiles[vendor_id].get("qwen_suggestions", [])
            # 取得最新的建議
            if suggestions:
                latest = max(suggestions, key=lambda x: x.get("timestamp", ""))
                return latest
                
    except Exception as e:
        logging.warning(f"Failed to load vendor feedback: {e}")
    
    return {}


def preprocess_image(image_path: str, vendor_id: Optional[str] = None) -> str:
    """
    強化版影像前處理：去噪、二值化、傾斜校正、對比度調整
    
    Args:
        image_path: 輸入影像路徑
        vendor_id: 供應商ID（用於載入特定參數）
        
    Returns:
        處理後的影像路徑
    """
    try:
        import cv2
    except ImportError:
        logging.warning("OpenCV not installed. Run: pip install opencv-python")
        return image_path
    
    # 載入參數和回饋
    params = load_processing_params(vendor_id)
    feedback = load_vendor_feedback(vendor_id)
    
    # 套用 Qwen 回饋調整
    if feedback.get("action") == "increase_contrast":
        params["contrast_alpha"] = feedback.get("value", params["contrast_alpha"])
        logging.info(f"Applied Qwen feedback: contrast_alpha = {params['contrast_alpha']}")
    
    try:
        # 載入影像
        img = cv2.imread(image_path)
        if img is None:
            logging.error(f"Failed to load image: {image_path}")
            return image_path
        
        # Step 1: 轉灰階
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Step 2: 去噪
        if params.get("denoise_strength", 0) > 0:
            gray = cv2.fastNlMeansDenoising(gray, h=params["denoise_strength"])
        
        # Step 3: 對比度調整
        if params.get("contrast_alpha", 1.0) != 1.0 or params.get("contrast_beta", 0) != 0:
            gray = cv2.convertScaleAbs(gray, 
                                     alpha=params["contrast_alpha"], 
                                     beta=params["contrast_beta"])
        
        # Step 4: 傾斜校正（簡化版）
        if params.get("deskew_enabled", False):
            gray = deskew_image(gray)
        
        # Step 5: 二值化
        if params.get("binary_method") == "adaptive_gaussian":
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
        else:
            _, binary = cv2.threshold(gray, params["binary_threshold"], 255, cv2.THRESH_BINARY)
        
        # Step 6: 銳化（可選）
        if params.get("sharpen_enabled", False):
            kernel = np.array(params.get("sharpen_kernel", [[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]))
            binary = cv2.filter2D(binary, -1, kernel)
        
        # 儲存處理後的影像
        output_path = image_path.replace(".png", "_processed.png").replace(".jpg", "_processed.jpg")
        cv2.imwrite(output_path, binary)
        
        logging.info(f"Image preprocessing completed: {output_path}")
        return output_path
        
    except Exception as e:
        logging.error(f"Image preprocessing failed: {e}")
        return image_path


def deskew_image(image: np.ndarray) -> np.ndarray:
    """傾斜校正（簡化版）"""
    try:
        import cv2
        
        # 霍夫變換檢測線條
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None and len(lines) > 0:
            # 計算平均角度
            angles = []
            for rho, theta in lines[:10]:  # 只取前10條線
                angle = np.degrees(theta) - 90
                if abs(angle) < 45:  # 過濾極端角度
                    angles.append(angle)
            
            if angles:
                avg_angle = np.median(angles)
                
                # 旋轉校正
                if abs(avg_angle) > 0.5:  # 只在角度夠大時才校正
                    center = (image.shape[1] // 2, image.shape[0] // 2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
                    image = cv2.warpAffine(image, rotation_matrix, 
                                         (image.shape[1], image.shape[0]), 
                                         flags=cv2.INTER_CUBIC, 
                                         borderMode=cv2.BORDER_REPLICATE)
    
    except Exception as e:
        logging.warning(f"Deskew failed: {e}")
    
    return image


def update_processing_feedback(vendor_id: str, suggestions: list):
    """更新處理參數回饋（供第七步呼叫）"""
    profiles_path = "po_extractor/config/vendor_image_profiles.json"
    
    try:
        # 讀取現有配置
        if os.path.exists(profiles_path):
            with open(profiles_path, 'r', encoding='utf-8') as f:
                profiles = json.load(f)
        else:
            profiles = {}
        
        # 更新建議
        if vendor_id not in profiles:
            profiles[vendor_id] = {"qwen_suggestions": []}
        
        profiles[vendor_id]["qwen_suggestions"].extend(suggestions)
        profiles[vendor_id]["last_updated"] = str(np.datetime64('now'))
        
        # 儲存
        with open(profiles_path, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
            
        logging.info(f"Updated processing feedback for vendor {vendor_id}")
        
    except Exception as e:
        logging.error(f"Failed to update processing feedback: {e}")
