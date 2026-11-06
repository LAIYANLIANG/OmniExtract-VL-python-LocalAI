"""Step 2: 檔案分流（判斷「文字型」vs「影像型」）."""
import logging
import pdfplumber
from ..config import IMAGE_PDF_TEXT_THRESHOLD


def classify_pdf_type(pdf_path: str) -> dict:
    """
    分流邏輯：判斷 PDF 是文字型還是影像型
    
    Returns:
        dict with keys:
            - 'full_text': str, all pages concatenated
            - 'pages': list of str, text per page
            - 'is_image_pdf': bool, True if text too short (likely scanned)
            - 'classification': str, 'text_based' or 'image_based'
            - 'text_stats': dict, 文字統計資訊
    """
    logger = logging.getLogger(__name__)
    pages = []
    full_text_parts = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages.append(text)
                full_text_parts.append(text)
        
        full_text = "\n".join(full_text_parts)
        total_chars = len(full_text.strip())
        total_pages = len(pages)
        chars_per_page = total_chars / max(total_pages, 1)
        
        # 分類邏輯
        is_image_pdf = total_chars < IMAGE_PDF_TEXT_THRESHOLD
        classification = "image_based" if is_image_pdf else "text_based"
        
        # 統計資訊
        text_stats = {
            "total_characters": total_chars,
            "total_pages": total_pages,
            "chars_per_page": chars_per_page,
            "threshold_used": IMAGE_PDF_TEXT_THRESHOLD,
            "non_empty_pages": sum(1 for p in pages if len(p.strip()) > 0)
        }
        
        logger.info(
            f"PDF classification: {classification} "
            f"({total_chars} chars, {chars_per_page:.1f} chars/page)"
        )
        
        return {
            "full_text": full_text,
            "pages": pages,
            "is_image_pdf": is_image_pdf,
            "classification": classification,
            "text_stats": text_stats,
        }
        
    except Exception as e:
        logger.error(f"PDF classification failed: {e}")
        return {
            "full_text": "",
            "pages": [],
            "is_image_pdf": True,
            "classification": "image_based",
            "text_stats": {"error": str(e)},
        }


# 向後相容性
def extract_text_from_pdf(pdf_path: str) -> dict:
    """向後相容性函數"""
    result = classify_pdf_type(pdf_path)
    return {
        "full_text": result["full_text"],
        "pages": result["pages"],
        "is_image_pdf": result["is_image_pdf"]
    }
