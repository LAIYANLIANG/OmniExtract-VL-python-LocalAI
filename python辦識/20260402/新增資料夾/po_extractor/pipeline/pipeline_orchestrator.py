"""Seven-Step Pipeline Orchestrator for Qwen3-VL Enhanced PO Extraction

整合七步管道，協調 OpenCV → 文件分類 → PaddleOCR → 清洗 → 識別 → LayoutLM → Qwen 審核
"""
import json
import logging
import time
from typing import Dict, Any, List, Optional
from ..models.po_model import PurchaseOrder

# Import seven pipeline steps
from .step1_preprocess import preprocess_images
from .step2_extract import classify_pdf_type
from .step3_ocr import extract_text_with_paddleocr
from .step3_clean import clean_text_for_matching, clean_text_preserve_structure, get_cleaning_statistics
from .step4_classify import enhanced_classify_document
from .step6_layoutlm import trigger_layoutlm_extraction, check_layoutlm_trigger
from .step7_qwen_audit import qwen_audit_vote_results, QwenClient
from .voting_system import VotingSystem
from .feedback_engine import FeedbackEngine


class SevenStepOrchestrator:
    """Qwen3-VL 七步管道協調器"""
    
    def __init__(self, config_path: str = "po_extractor/config/qwen_config.json"):
        """
        初始化協調器
        
        Args:
            config_path: Qwen 配置檔案路徑
        """
        self.config = self._load_config(config_path)
        self.voting_system = VotingSystem()
        self.feedback_engine = FeedbackEngine()
        self.qwen_client = QwenClient(self.config)
        
        # 步驟執行統計
        self.step_stats = {
            "step1_opencv": {"count": 0, "avg_time": 0.0, "errors": 0},
            "step2_classify": {"count": 0, "avg_time": 0.0, "errors": 0},
            "step3_ocr": {"count": 0, "avg_time": 0.0, "errors": 0},
            "step4_clean": {"count": 0, "avg_time": 0.0, "errors": 0},
            "step5_logic": {"count": 0, "avg_time": 0.0, "errors": 0},
            "step6_layoutlm": {"count": 0, "avg_time": 0.0, "errors": 0},
            "step7_qwen": {"count": 0, "avg_time": 0.0, "errors": 0}
        }
    
    def _load_config(self, config_path: str) -> dict:
        """載入配置檔案"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load config from {config_path}: {e}")
            return {"pipeline": {"enable_qwen_audit": False}}
    
    def process_document(self, pdf_path: str, 
                        enable_qwen_audit: bool = None,
                        enable_layoutlm: bool = None) -> Dict[str, Any]:
        """
        執行完整的七步管道流程
        
        Args:
            pdf_path: PDF 檔案路徑
            enable_qwen_audit: 是否啟用 Qwen 審核（覆蓋配置）
            enable_layoutlm: 是否強制啟用 LayoutLM（覆蓋自動檢測）
            
        Returns:
            完整處理結果
        """
        pipeline_start = time.time()
        results = {
            "pdf_path": pdf_path,
            "timestamp": time.time(),
            "steps_results": {},
            "final_extraction": {},
            "qwen_audit": {},
            "pipeline_stats": {},
            "errors": []
        }
        
        try:
            # === Step 1: OpenCV 圖片預處理 ===
            step1_result = self._execute_step(
                "step1_opencv",
                lambda: preprocess_images(pdf_path),
                "OpenCV 圖片預處理"
            )
            results["steps_results"]["step1"] = step1_result
            
            if not step1_result.get("success"):
                raise Exception("Step 1 (OpenCV) failed")
            
            # === Step 2: 文件類型分類 ===
            step2_result = self._execute_step(
                "step2_classify",
                lambda: classify_pdf_type(pdf_path),
                "PDF 文件分類"
            )
            results["steps_results"]["step2"] = step2_result
            
            # === Step 3: PaddleOCR 文字擷取 ===  
            step3_result = self._execute_step(
                "step3_ocr",
                lambda: extract_text_with_paddleocr(
                    step1_result["processed_images"], 
                    step2_result.get("pdf_type", "unknown")
                ),
                "PaddleOCR 文字擷取"
            )
            results["steps_results"]["step3"] = step3_result
            
            if not step3_result.get("success"):
                raise Exception("Step 3 (OCR) failed")
            
            # === Step 4: 資料清洗 ===
            pages_text = step3_result["pages_text"]
            step4_result = self._execute_step(
                "step4_clean",
                lambda: self._clean_extracted_text(pages_text),
                "資料清洗"
            )
            results["steps_results"]["step4"] = step4_result
            
            # === Step 5: 邏輯判斷（表頭識別、分類）===
            step5_result = self._execute_step(
                "step5_logic", 
                lambda: enhanced_classify_document(pages_text),
                "邏輯判斷與分類"
            )
            results["steps_results"]["step5"] = step5_result
            
            # === Step 6: LayoutLM 深度處理 ===
            should_use_layoutlm = enable_layoutlm or check_layoutlm_trigger(
                step3_result, 
                step5_result
            )
            
            if should_use_layoutlm:
                step6_result = self._execute_step(
                    "step6_layoutlm",
                    lambda: trigger_layoutlm_extraction(
                        step1_result["processed_images"], 
                        step3_result,
                        step5_result
                    ),
                    "LayoutLM 深度處理"
                )
                results["steps_results"]["step6"] = step6_result
            else:
                results["steps_results"]["step6"] = {
                    "success": True,
                    "skipped": True,
                    "reason": "LayoutLM trigger conditions not met"
                }
            
            # === 投票機制整合多個結果 ===
            vote_inputs = self._prepare_voting_inputs(results["steps_results"])
            vote_results = self.voting_system.vote_on_extraction(vote_inputs)
            results["vote_results"] = vote_results
            
            # === Step 7: Qwen3-VL 最終審核 ===
            should_audit = enable_qwen_audit if enable_qwen_audit is not None else self.config.get("pipeline", {}).get("enable_qwen_audit", False)
            
            if should_audit and self.qwen_client.is_available():
                step7_result = self._execute_step(
                    "step7_qwen",
                    lambda: qwen_audit_vote_results(
                        vote_results,
                        step1_result["processed_images"], 
                        original_pdf=pdf_path
                    ),
                    "Qwen3-VL 視覺審核"
                )
                results["steps_results"]["step7"] = step7_result
                results["qwen_audit"] = step7_result
                
                # 如果 Qwen 提供建議，套用它們
                if step7_result.get("parameter_suggestions"):
                    self.feedback_engine.apply_suggestions(
                        step7_result["parameter_suggestions"]
                    )
            else:
                results["steps_results"]["step7"] = {
                    "success": True,
                    "skipped": True,
                    "reason": "Qwen audit disabled or unavailable"
                }
            
            # === 最終結果整合 ===
            if "step7" in results["steps_results"] and not results["steps_results"]["step7"].get("skipped"):
                # 使用 Qwen 的最終決定
                results["final_extraction"] = results["steps_results"]["step7"]["final_extraction"]
            else:
                # 使用投票結果
                results["final_extraction"] = vote_results["final_decision"]
            
            # === 統計資訊 ===
            pipeline_end = time.time()
            results["pipeline_stats"] = {
                "total_time": pipeline_end - pipeline_start,
                "steps_executed": len([s for s in results["steps_results"].values() 
                                     if not s.get("skipped", False)]),
                "steps_skipped": len([s for s in results["steps_results"].values() 
                                    if s.get("skipped", False)]),
                "step_timings": self.step_stats,
                "cleaning_stats": get_cleaning_statistics()
            }
            
            logging.info(f"Pipeline completed in {results['pipeline_stats']['total_time']:.2f}s")
            return results
            
        except Exception as e:
            results["errors"].append({
                "stage": "pipeline_execution",
                "error": str(e),
                "timestamp": time.time()
            })
            logging.error(f"Pipeline failed: {e}")
            return results
    
    def _execute_step(self, step_name: str, step_func: callable, 
                     description: str) -> Dict[str, Any]:
        """執行單一步驟並記錄統計"""
        start_time = time.time()
        logging.info(f"Executing {description}...")
        
        try:
            result = step_func()
            execution_time = time.time() - start_time
            
            # 更新統計
            self._update_step_stats(step_name, execution_time, success=True)
            
            if isinstance(result, dict):
                result["execution_time"] = execution_time
                result["success"] = True
            else:
                result = {"data": result, "execution_time": execution_time, "success": True}
            
            logging.info(f"{description} completed in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_step_stats(step_name, execution_time, success=False)
            
            error_result = {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }
            
            logging.error(f"{description} failed: {e}")
            return error_result
    
    def _update_step_stats(self, step_name: str, execution_time: float, success: bool):
        """更新步驟統計資訊"""
        if step_name not in self.step_stats:
            return
            
        stats = self.step_stats[step_name]
        stats["count"] += 1
        
        # 計算移動平均
        if stats["avg_time"] == 0:
            stats["avg_time"] = execution_time
        else:
            stats["avg_time"] = (stats["avg_time"] + execution_time) / 2
            
        if not success:
            stats["errors"] += 1
    
    def _clean_extracted_text(self, pages_text: List[str]) -> Dict[str, Any]:
        """執行文字清洗步驟"""
        cleaned_pages = []
        structure_preserved_pages = []
        
        for page_text in pages_text:
            cleaned = clean_text_for_matching(page_text)
            structured = clean_text_preserve_structure(page_text)
            
            cleaned_pages.append(cleaned)
            structure_preserved_pages.append(structured)
        
        return {
            "cleaned_pages": cleaned_pages,
            "structure_preserved_pages": structure_preserved_pages,
            "cleaning_stats": get_cleaning_statistics()
        }
    
    def _prepare_voting_inputs(self, steps_results: Dict[str, Any]) -> Dict[str, Any]:
        """準備投票系統的輸入資料"""
        voting_inputs = {}
        
        # 步驟 2: PDF 分類
        if "step2" in steps_results and steps_results["step2"].get("success"):
            voting_inputs["pdf_classifier"] = steps_results["step2"]
        
        # 步驟 3: OCR 結果  
        if "step3" in steps_results and steps_results["step3"].get("success"):
            voting_inputs["ocr_extractor"] = steps_results["step3"]
        
        # 步驟 5: 邏輯判斷
        if "step5" in steps_results and steps_results["step5"].get("success"):
            voting_inputs["logic_classifier"] = steps_results["step5"]
            
        # 步驟 6: LayoutLM（如果有執行）
        if "step6" in steps_results and steps_results["step6"].get("success") and not steps_results["step6"].get("skipped"):
            voting_inputs["layoutlm_extractor"] = steps_results["step6"]
        
        return voting_inputs
    
    def get_pipeline_health(self) -> Dict[str, Any]:
        """取得管道健康狀態"""
        return {
            "step_statistics": self.step_stats,
            "qwen_status": self.qwen_client.is_available(),
            "voting_system_status": self.voting_system is not None,
            "feedback_engine_status": self.feedback_engine is not None,
            "config_loaded": bool(self.config)
        }
    
    def reset_statistics(self):
        """重置統計資訊"""
        for step_name in self.step_stats:
            self.step_stats[step_name] = {"count": 0, "avg_time": 0.0, "errors": 0}
        
        logging.info("Pipeline statistics reset")


# 便捷函數
def process_po_document(pdf_path: str, **kwargs) -> Dict[str, Any]:
    """
    處理 PO 文件的便捷函數
    
    Args:
        pdf_path: PDF 檔案路徑
        **kwargs: 傳遞給 SevenStepOrchestrator.process_document 的額外參數
        
    Returns:
        處理結果
    """
    orchestrator = SevenStepOrchestrator()
    return orchestrator.process_document(pdf_path, **kwargs)


def get_orchestrator_instance() -> SevenStepOrchestrator:
    """取得協調器實例（單例模式）"""
    if not hasattr(get_orchestrator_instance, "_instance"):
        get_orchestrator_instance._instance = SevenStepOrchestrator()
    return get_orchestrator_instance._instance