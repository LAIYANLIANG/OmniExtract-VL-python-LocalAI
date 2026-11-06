"""Step 5: 邏輯判斷（表頭辨識、分類與分割）Enhanced Vendor Classification."""
import re
import logging
from typing import Tuple, List, Dict, Any
from .step3_clean import clean_text_for_matching
from ..features.feature_db import FEATURE_DB
from .pattern_applier import get_learned_keywords


def identify_document_headers(pages_text: List[str]) -> List[Dict[str, Any]]:
    """
    識別文件表頭（掃描每頁 Top 20% 區域）
    
    Args:
        pages_text: 各頁文字內容
        
    Returns:
        表頭識別結果列表
    """
    headers = []
    
    for page_num, page_text in enumerate(pages_text):
        if not page_text.strip():
            continue
            
        # 取得頁面頂部 20% 區域
        lines = page_text.split('\n')
        top_20_percent = int(len(lines) * 0.2) or 1
        header_text = '\n'.join(lines[:top_20_percent])
        
        # 在表頭區域中匹配供應商特徵
        vendor_id, confidence = match_vendor_in_text(header_text)
        
        if confidence > 0.3:  # 低閾值，因為是表頭區域
            headers.append({
                "page": page_num + 1,
                "vendor_id": vendor_id,
                "confidence": confidence,
                "header_text": header_text[:200],  # 只保存前200字元
                "detected_keywords": _extract_matched_keywords(header_text, vendor_id)
            })
    
    return headers


def split_document_by_headers(pages_text: List[str], 
                             headers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    根據表頭分割文件
    
    Args:
        pages_text: 各頁文字內容
        headers: 表頭識別結果
        
    Returns:
        分割後的文件列表
    """
    if not headers:
        # 沒有表頭，當作單一文件
        return [{
            "document_id": 1,
            "pages": list(range(1, len(pages_text) + 1)),
            "vendor_id": "unknown",
            "confidence": 0.0,
            "text": '\n'.join(pages_text)
        }]
    
    documents = []
    current_doc_start = 0
    
    for i, header in enumerate(headers):
        header_page = header["page"] - 1  # 轉換為 0-based
        
        # 如果不是第一個表頭，將前一段結束
        if i > 0:
            doc_pages = list(range(current_doc_start + 1, header_page + 1))
            doc_text = '\n'.join(pages_text[current_doc_start:header_page])
            
            if doc_text.strip():
                documents.append({
                    "document_id": len(documents) + 1,
                    "pages": doc_pages,
                    "vendor_id": headers[i-1]["vendor_id"],
                    "confidence": headers[i-1]["confidence"],
                    "text": doc_text
                })
        
        current_doc_start = header_page
    
    # 處理最後一段
    if current_doc_start < len(pages_text):
        doc_pages = list(range(current_doc_start + 1, len(pages_text) + 1))
        doc_text = '\n'.join(pages_text[current_doc_start:])
        
        if doc_text.strip():
            documents.append({
                "document_id": len(documents) + 1,
                "pages": doc_pages,
                "vendor_id": headers[-1]["vendor_id"],
                "confidence": headers[-1]["confidence"],
                "text": doc_text
            })
    
    return documents


def match_vendor_in_text(text: str) -> Tuple[str, float]:
    """
    在文字中匹配供應商
    
    這是強化版的 classify_vendor 函數
    """
    return classify_vendor_with_confidence(text)


def classify_vendor_with_confidence(raw_text: str) -> Tuple[str, float]:
    """
    Classify the vendor with confidence score (Enhanced Version).
    
    Args:
        raw_text: Raw text from document
        
    Returns:
        Tuple of (vendor_id, confidence_score)
    """
    if not raw_text:
        return "unknown", 0.0
    
    cleaned = clean_text_for_matching(raw_text)
    text_lower = raw_text.lower()
    best_match = ("unknown", 0.0)
    
    # 檢查既有特徵資料庫
    for vendor_info in FEATURE_DB:
        vendor_id = vendor_info["vendor_id"]
        keywords = vendor_info["keywords"]
        priority = vendor_info.get("priority", 5)
        
        # 計算匹配度
        matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        if matches > 0:
            # 信心值 = 匹配數 / 總關鍵字數 * 優先級權重
            confidence = (matches / len(keywords)) * (priority / 10)
            
            if confidence > best_match[1]:
                best_match = (vendor_id, confidence)
    
    # 檢查學習得到的關鍵字（優先級 5）
    try:
        learned_keywords_db = get_learned_keywords()
        for vendor_id, keywords in learned_keywords_db.items():
            if not keywords:
                continue
                
            matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
            if matches > 0:
                confidence = (matches / len(keywords)) * 0.5  # 學習關鍵字信心值略低
                
                if confidence > best_match[1]:
                    best_match = (vendor_id, confidence)
                    
    except Exception as e:
        logging.debug(f"Failed to load learned keywords: {e}")
    
    return best_match


def classify_vendor(raw_text: str) -> str:
    """
    Classify which vendor a PO belongs to by matching keywords.
    Uses both built-in feature_db AND learned keywords from corrections.

    Returns:
        vendor_id (str) e.g. 'byd', 'kaifa', 'siemens', 'desay_sv'
        Returns 'unknown' if no match found.
    """
    # 向後相容：呼叫新的帶信心值版本
    vendor_id, confidence = classify_vendor_with_confidence(raw_text)
    logging.debug(f"Classified vendor: {vendor_id} (confidence: {confidence:.2f})")
    return vendor_id


def _extract_matched_keywords(text: str, vendor_id: str) -> List[str]:
    """提取在文字中匹配到的關鍵字"""
    matched = []
    text_lower = text.lower()
    
    # 檢查既有特徵
    for vendor_info in FEATURE_DB:
        if vendor_info["vendor_id"] == vendor_id:
            for keyword in vendor_info["keywords"]:
                if keyword.lower() in text_lower:
                    matched.append(keyword)
    
    # 檢查學習關鍵字
    try:
        learned_keywords_db = get_learned_keywords()
        if vendor_id in learned_keywords_db:
            for keyword in learned_keywords_db[vendor_id]:
                if keyword.lower() in text_lower:
                    matched.append(f"{keyword} (學習)")
    except Exception:
        pass
    
    return matched


def enhanced_classify_document(pages_text: List[str]) -> Dict[str, Any]:
    """
    強化版文件分類（主要入口函數）
    
    Args:
        pages_text: 各頁文字內容
        
    Returns:
        分類結果
    """
    # Step 1: 識別表頭
    headers = identify_document_headers(pages_text)
    
    # Step 2: 分割文件
    documents = split_document_by_headers(pages_text, headers)
    
    # Step 3: 對整個文件進行分類（向後相容）
    full_text = '\n'.join(pages_text)
    overall_vendor, overall_confidence = classify_vendor_with_confidence(full_text)
    
    return {
        "overall_classification": {
            "vendor_id": overall_vendor,
            "confidence": overall_confidence
        },
        "headers_detected": headers,
        "documents_split": documents,
        "total_documents": len(documents) if documents else 1,
        "processing_method": "multi_document" if len(documents) > 1 else "single_document"
    }
