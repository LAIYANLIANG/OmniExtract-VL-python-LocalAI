"""Step 3: PaddleOCR 文字化處理模組."""
import json
import logging
import os
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass


@dataclass
class OCRResult:
    """OCR 識別結果"""
    text: str
    confidence: float
    bbox: List[Tuple[float, float]]  # 邊界框座標
    page_num: int = 0


class OCRProcessor:
    """PaddleOCR 處理器"""
    
    def __init__(self, lang=['ch', 'en'], use_gpu=False):
        """
        初始化 OCR 處理器
        
        Args:
            lang: 語言列表 (預設中英文)
            use_gpu: 是否使用 GPU 加速
        """
        self.lang = lang
        self.use_gpu = use_gpu
        self.ocr = None
        self.logger = logging.getLogger(__name__)
        
    def _lazy_load_ocr(self):
        """延遲載入 PaddleOCR（避免啟動時就載入）"""
        if self.ocr is None:
            try:
                from paddleocr import PaddleOCR
                self.ocr = PaddleOCR(
                    use_angle_cls=True, 
                    lang=self.lang,
                    use_gpu=self.use_gpu,
                    show_log=False
                )
                self.logger.info(f"PaddleOCR loaded with languages: {self.lang}")
            except ImportError:
                self.logger.error("PaddleOCR not installed. Run: pip install paddlepaddle paddleocr")
                raise ImportError("PaddleOCR not available. Install with: pip install paddlepaddle paddleocr")
    
    def extract_text_from_image(self, image_path: str) -> List[OCRResult]:
        """
        從圖片提取文字
        
        Args:
            image_path: 圖片檔案路徑
            
        Returns:
            OCR 結果列表
        """
        self._lazy_load_ocr()
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            result = self.ocr.ocr(image_path, cls=True)
            ocr_results = []
            
            if result and result[0]:
                for line in result[0]:
                    bbox, (text, confidence) = line
                    ocr_results.append(OCRResult(
                        text=text,
                        confidence=confidence,
                        bbox=bbox
                    ))
            
            self.logger.info(f"OCR extracted {len(ocr_results)} text segments from {image_path}")
            return ocr_results
            
        except Exception as e:
            self.logger.error(f"OCR processing failed for {image_path}: {e}")
            return []
    
    def extract_text_from_pdf_pages(self, pdf_path: str) -> Dict[int, List[OCRResult]]:
        """
        從 PDF 各頁提取文字（需要先轉換為圖片）
        
        Args:
            pdf_path: PDF 檔案路徑
            
        Returns:
            頁面編號 -> OCR 結果列表的字典
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            self.logger.error("PyMuPDF not installed. Run: pip install pymupdf")
            raise ImportError("PyMuPDF required for PDF processing")
        
        results = {}
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                
                # 儲存為臨時圖片
                temp_img_path = f"temp_page_{page_num}.png"
                pix.save(temp_img_path)
                
                # OCR 處理
                page_results = self.extract_text_from_image(temp_img_path)
                for result in page_results:
                    result.page_num = page_num + 1  # 1-based page numbering
                
                results[page_num + 1] = page_results
                
                # 清理臨時檔案
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
            
            doc.close()
            self.logger.info(f"OCR processed {len(results)} pages from {pdf_path}")
            
        except Exception as e:
            self.logger.error(f"PDF OCR processing failed for {pdf_path}: {e}")
        
        return results
    
    def merge_ocr_results(self, ocr_results: List[OCRResult]) -> str:
        """
        合併 OCR 結果為單一文字字符串
        
        Args:
            ocr_results: OCR 結果列表
            
        Returns:
            合併後的文字
        """
        # 按 Y 座標排序（從上到下）
        sorted_results = sorted(ocr_results, key=lambda x: x.bbox[0][1] if x.bbox else 0)
        
        return ' '.join(result.text for result in sorted_results if result.text)
    
    def get_structured_output(self, ocr_results: List[OCRResult]) -> Dict[str, Any]:
        """
        產出結構化的 OCR 結果
        
        Args:
            ocr_results: OCR 結果列表
            
        Returns:
            結構化輸出字典
        """
        return {
            "full_text": self.merge_ocr_results(ocr_results),
            "total_segments": len(ocr_results),
            "avg_confidence": sum(r.confidence for r in ocr_results) / max(len(ocr_results), 1),
            "segments": [
                {
                    "text": r.text,
                    "confidence": r.confidence,
                    "bbox": r.bbox,
                    "page": r.page_num
                }
                for r in ocr_results
            ]
        }


def process_image_pdf(pdf_path: str, lang=['ch', 'en']) -> Dict[str, Any]:
    """
    處理影像型 PDF（主要入口函數）
    
    Args:
        pdf_path: PDF 檔案路徑
        lang: OCR 語言設定
        
    Returns:
        OCR 處理結果
    """
    processor = OCRProcessor(lang=lang)
    
    # 從 PDF 各頁提取文字
    pages_results = processor.extract_text_from_pdf_pages(pdf_path)
    
    # 合併所有頁面的結果
    all_results = []
    for page_num, results in pages_results.items():
        all_results.extend(results)
    
    # 產出結構化結果
    structured_output = processor.get_structured_output(all_results)
    structured_output["pages"] = {
        str(page_num): processor.get_structured_output(results)
        for page_num, results in pages_results.items()
    }
    
    return structured_output


# 向後相容性介面
def extract_text_with_ocr(image_or_pdf_path: str) -> Dict[str, Any]:
    """向後相容性函數"""
    if image_or_pdf_path.lower().endswith('.pdf'):
        return process_image_pdf(image_or_pdf_path)
    else:
        processor = OCRProcessor()
        results = processor.extract_text_from_image(image_or_pdf_path)
        return processor.get_structured_output(results)