"""Step 6: LayoutLM 結構化提取模組（深度學習保險機制）."""
import json
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class LayoutLMResult:
    """LayoutLM 提取結果"""
    field: str
    value: str
    confidence: float
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    page: int = 1


class LayoutLMExtractor:
    """LayoutLM 結構化提取器"""
    
    def __init__(self, model_name="microsoft/layoutlmv3-base"):
        """
        初始化 LayoutLM 提取器
        
        Args:
            model_name: Hugging Face 模型名稱
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.processor = None
        self.logger = logging.getLogger(__name__)
        
        # 關鍵欄位映射
        self.field_mappings = {
            "B-PO_NUMBER": "purchase_info.po_number",
            "B-TOTAL": "purchase_info.total_amount", 
            "B-DATE": "purchase_info.date",
            "B-VENDOR_NAME": "vendor_info.name",
            "B-VENDOR_CODE": "vendor_info.vendor_code",
            "B-UNIT_PRICE": "line_items.unit_price",
            "B-QUANTITY": "line_items.quantity",
            "B-ITEM_CODE": "line_items.product_code"
        }
        
        # 觸發條件閾值
        self.activation_thresholds = {
            "min_confidence": 0.75,
            "critical_fields": ["purchase_info.po_number", "purchase_info.total_amount"],
            "max_missing_fields": 3
        }
    
    def _lazy_load_model(self):
        """延遲載入 LayoutLM 模型"""
        if self.model is None:
            try:
                from transformers import LayoutLMv3ForTokenClassification, LayoutLMv3TokenizerFast, LayoutLMv3Processor
                from PIL import Image
                
                self.logger.info(f"Loading LayoutLM model: {self.model_name}")
                
                self.model = LayoutLMv3ForTokenClassification.from_pretrained(self.model_name)
                self.tokenizer = LayoutLMv3TokenizerFast.from_pretrained(self.model_name)
                self.processor = LayoutLMv3Processor.from_pretrained(self.model_name)
                
                self.logger.info("LayoutLM model loaded successfully")
                
            except ImportError as e:
                self.logger.error("LayoutLM dependencies not installed. Run: pip install transformers torch pillow")
                raise ImportError(f"LayoutLM not available: {e}")
            except Exception as e:
                self.logger.error(f"Failed to load LayoutLM model: {e}")
                raise
    
    def should_activate(self, confidence_scores: Dict[str, float], missing_fields: List[str]) -> bool:
        """
        判斷是否需要啟動 LayoutLM
        
        Args:
            confidence_scores: 各欄位信心值
            missing_fields: 缺失的欄位列表
            
        Returns:
            是否需要啟動 LayoutLM
        """
        # 計算平均信心值
        if confidence_scores:
            avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
        else:
            avg_confidence = 0
        
        # 檢查關鍵欄位是否缺失
        critical_missing = any(
            field in missing_fields 
            for field in self.activation_thresholds["critical_fields"]
        )
        
        # 判斷條件
        low_confidence = avg_confidence < self.activation_thresholds["min_confidence"]
        too_many_missing = len(missing_fields) > self.activation_thresholds["max_missing_fields"]
        
        should_activate = low_confidence or critical_missing or too_many_missing
        
        if should_activate:
            self.logger.info(
                f"LayoutLM activation triggered: "
                f"confidence={avg_confidence:.2f}, "
                f"critical_missing={critical_missing}, "
                f"missing_count={len(missing_fields)}"
            )
        
        return should_activate
    
    def extract_structured(self, image_path: str, ocr_results: List[Dict]) -> List[LayoutLMResult]:
        """
        執行 LayoutLM 結構化提取
        
        Args:
            image_path: 原始影像路徑
            ocr_results: OCR 結果（含 bbox 資訊）
            
        Returns:
            LayoutLM 提取結果列表
        """
        self._lazy_load_model()
        
        try:
            from PIL import Image
            import torch
            
            # 載入影像
            image = Image.open(image_path).convert("RGB")
            
            # 準備 OCR 資料格式
            words = [result.get("text", "") for result in ocr_results]
            boxes = [result.get("bbox", [0, 0, 0, 0]) for result in ocr_results]
            
            # 正規化邊界框座標（LayoutLM 需要整數座標）
            boxes = [[int(coord) for coord in bbox] for bbox in boxes]
            
            # 使用 processor 準備輸入
            encoding = self.processor(
                image, 
                words, 
                boxes=boxes, 
                return_tensors="pt",
                truncation=True,
                padding=True
            )
            
            # 模型推理
            with torch.no_grad():
                outputs = self.model(**encoding)
                predictions = outputs.logits.argmax(-1).squeeze().tolist()
            
            # 解析預測結果
            results = []
            tokens = self.tokenizer.convert_ids_to_tokens(encoding["input_ids"].squeeze().tolist())
            
            current_entity = None
            current_text = ""
            current_bbox = [0, 0, 0, 0]
            
            for token, pred_id, bbox in zip(tokens, predictions, boxes):
                if token in ["[CLS]", "[SEP]", "[PAD]"]:
                    continue
                
                label = self.model.config.id2label.get(pred_id, "O")
                
                if label.startswith("B-"):
                    # 開始新實體
                    if current_entity and current_text:
                        field_path = self.field_mappings.get(current_entity, current_entity)
                        results.append(LayoutLMResult(
                            field=field_path,
                            value=current_text.strip(),
                            confidence=0.8,  # 簡化版信心值
                            bbox=tuple(current_bbox)
                        ))
                    
                    current_entity = label
                    current_text = token.replace("##", "")
                    current_bbox = bbox
                    
                elif label.startswith("I-") and current_entity:
                    # 繼續當前實體
                    current_text += token.replace("##", "")
                    # 擴展 bbox
                    current_bbox[2] = max(current_bbox[2], bbox[2])
                    current_bbox[3] = max(current_bbox[3], bbox[3])
                
                else:
                    # 結束當前實體
                    if current_entity and current_text:
                        field_path = self.field_mappings.get(current_entity, current_entity)
                        results.append(LayoutLMResult(
                            field=field_path,
                            value=current_text.strip(),
                            confidence=0.8,
                            bbox=tuple(current_bbox)
                        ))
                    
                    current_entity = None
                    current_text = ""
            
            # 處理最後一個實體
            if current_entity and current_text:
                field_path = self.field_mappings.get(current_entity, current_entity)
                results.append(LayoutLMResult(
                    field=field_path,
                    value=current_text.strip(),
                    confidence=0.8,
                    bbox=tuple(current_bbox)
                ))
            
            self.logger.info(f"LayoutLM extracted {len(results)} structured fields")
            return results
            
        except Exception as e:
            self.logger.error(f"LayoutLM extraction failed: {e}")
            return []
    
    def merge_with_existing_results(self, existing_data: Dict[str, Any], 
                                   layoutlm_results: List[LayoutLMResult]) -> Dict[str, Any]:
        """
        將 LayoutLM 結果合併到現有資料中
        
        Args:
            existing_data: 現有提取結果
            layoutlm_results: LayoutLM 提取結果
            
        Returns:
            合併後的結果
        """
        merged_data = existing_data.copy()
        
        for result in layoutlm_results:
            field_parts = result.field.split(".")
            
            # 處理巢狀欄位
            current = merged_data
            for i, part in enumerate(field_parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # 設定值（僅在原值為空或信心值較低時覆蓋）
            final_key = field_parts[-1]
            existing_value = current.get(final_key, "")
            
            if not existing_value or len(existing_value.strip()) == 0:
                current[final_key] = result.value
                self.logger.info(f"LayoutLM filled missing field: {result.field} = {result.value}")
            
            # 記錄 LayoutLM 來源
            if "_layoutlm_fields" not in merged_data:
                merged_data["_layoutlm_fields"] = {}
            merged_data["_layoutlm_fields"][result.field] = {
                "value": result.value,
                "confidence": result.confidence,
                "bbox": result.bbox
            }
        
        return merged_data


def advanced_extract(pdf_path: str, raw_text: str, 
                    confidence_scores: Dict[str, float] = None,
                    missing_fields: List[str] = None,
                    ocr_results: List[Dict] = None) -> Dict[str, Any]:
    """
    LayoutLM 進階提取（主要入口函數）
    
    Args:
        pdf_path: PDF 路徑
        raw_text: 原始文字
        confidence_scores: 現有信心值
        missing_fields: 缺失欄位
        ocr_results: OCR 結果
        
    Returns:
        提取結果或空字典
    """
    extractor = LayoutLMExtractor()
    
    # 檢查是否需要啟動
    if not extractor.should_activate(confidence_scores or {}, missing_fields or []):
        return {}
    
    # 如果沒有 OCR 結果，嘗試生成
    if not ocr_results:
        try:
            from .step3_ocr import process_image_pdf
            ocr_output = process_image_pdf(pdf_path)
            ocr_results = ocr_output.get("segments", [])
        except Exception as e:
            logging.error(f"Failed to generate OCR results for LayoutLM: {e}")
            return {}
    
    # 執行 LayoutLM 提取
    try:
        # 轉換 PDF 第一頁為圖片
        import fitz
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        temp_img = "temp_layoutlm.png"
        pix.save(temp_img)
        doc.close()
        
        # LayoutLM 處理
        results = extractor.extract_structured(temp_img, ocr_results)
        
        # 清理臨時檔案
        if os.path.exists(temp_img):
            os.remove(temp_img)
        
        # 轉換為字典格式
        return {
            "layoutlm_results": [
                {
                    "field": r.field,
                    "value": r.value,
                    "confidence": r.confidence,
                    "bbox": r.bbox
                }
                for r in results
            ],
            "total_fields": len(results),
            "activation_reason": f"confidence_low or missing_fields={len(missing_fields or [])}"
        }
        
    except Exception as e:
        logging.error(f"LayoutLM processing failed: {e}")
        return {}