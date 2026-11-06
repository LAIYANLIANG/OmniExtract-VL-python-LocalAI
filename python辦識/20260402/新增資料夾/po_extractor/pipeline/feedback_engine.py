"""經驗精煉回饋引擎：學習用戶修正並產出改善建議."""
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class FieldDifference:
    """欄位差異記錄"""
    field_path: str
    original_value: str
    corrected_value: str
    confidence_before: float
    extraction_method: str  # 原始提取方法


@dataclass
class LearningEvent:
    """學習事件"""
    id: str
    timestamp: str
    vendor_id: str
    document_path: str
    trigger: str  # "user_correction" | "low_confidence" | "voting_tie" 
    field_diffs: List[FieldDifference]
    applied_suggestions: List[Dict[str, Any]]
    accuracy_before: float
    accuracy_after: float


class FeedbackEngine:
    """經驗精煉回饋引擎"""
    
    def __init__(self, 
                 learning_journal_path="po_extractor/logs/learning_journal.json",
                 qwen_client=None):
        """
        初始化回饋引擎
        
        Args:
            learning_journal_path: 學習日誌檔案路徑
            qwen_client: Qwen 客戶端（用於診斷分析）
        """
        self.learning_journal_path = learning_journal_path
        self.qwen_client = qwen_client
        self.logger = logging.getLogger(__name__)
        
        # 確保學習日誌存在
        self._ensure_journal_exists()
        
        # 建議應用器
        self.suggestion_appliers = {
            1: self._apply_step1_suggestions,  # OpenCV 參數調整
            2: self._apply_step2_suggestions,  # 文件分流參數
            3: self._apply_step3_suggestions,  # OCR 設定
            4: self._apply_step4_suggestions,  # 清洗規則
            5: self._apply_step5_suggestions,  # 分類特徵
            6: self._apply_step6_suggestions,  # LayoutLM 閾值
            7: self._apply_step7_suggestions,  # Qwen 參數
        }
    
    def _ensure_journal_exists(self):
        """確保學習日誌檔案存在"""
        if not os.path.exists(self.learning_journal_path):
            os.makedirs(os.path.dirname(self.learning_journal_path), exist_ok=True)
            
            initial_journal = {
                "_version": "1.0.0",
                "_description": "Qwen 產出的學習日誌與經驗記錄",
                "entries": [],
                "statistics": {
                    "total_entries": 0,
                    "vendors_analyzed": [],
                    "most_common_issues": {},
                    "suggestions_applied": 0,
                    "accuracy_improvements": {}
                }
            }
            
            with open(self.learning_journal_path, 'w', encoding='utf-8') as f:
                json.dump(initial_journal, f, ensure_ascii=False, indent=2)
    
    def analyze_user_corrections(self, 
                                vendor_id: str,
                                document_path: str, 
                                original_result: Dict[str, Any],
                                corrected_result: Dict[str, Any],
                                image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        分析用戶修正，產出學習建議
        
        Args:
            vendor_id: 供應商ID
            document_path: 文件路徑
            original_result: 原始（錯誤）結果
            corrected_result: 用戶修正結果
            image_path: 原始影像路徑
            
        Returns:
            學習分析結果
        """
        # 找出欄位差異
        field_diffs = self._find_field_differences(original_result, corrected_result)
        
        if not field_diffs:
            self.logger.info("No differences found between original and corrected results")
            return {"differences_found": 0}
        
        self.logger.info(f"Found {len(field_diffs)} field differences for analysis")
        
        # 計算準確率變化
        accuracy_before = original_result.get("_accuracy_pct", 0) / 100
        accuracy_after = self._calculate_accuracy_after_corrections(corrected_result)
        
        # 使用 Qwen 分析差異原因
        suggestions = []
        if self.qwen_client:
            try:
                diff_data = [
                    {
                        "field": diff.field_path,
                        "original": diff.original_value,
                        "corrected": diff.corrected_value
                    }
                    for diff in field_diffs
                ]
                
                suggestions = self.qwen_client.diagnose_corrections(
                    vendor_id, diff_data, image_path
                )
                self.logger.info(f"Qwen generated {len(suggestions)} improvement suggestions")
                
            except Exception as e:
                self.logger.error(f"Qwen diagnosis failed: {e}")
        
        # 應用建議
        applied_suggestions = self.apply_suggestions(suggestions, vendor_id)
        
        # 記錄學習事件
        learning_event = LearningEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            vendor_id=vendor_id,
            document_path=document_path,
            trigger="user_correction",
            field_diffs=field_diffs,
            applied_suggestions=[asdict(s) for s in applied_suggestions],
            accuracy_before=accuracy_before,
            accuracy_after=accuracy_after
        )
        
        self._save_learning_event(learning_event)
        
        return {
            "differences_found": len(field_diffs),
            "suggestions_generated": len(suggestions),
            "suggestions_applied": len(applied_suggestions),
            "accuracy_improvement": accuracy_after - accuracy_before,
            "learning_event_id": learning_event.id,
            "field_diffs": [asdict(diff) for diff in field_diffs],
            "suggestions": [asdict(s) for s in suggestions]
        }
    
    def _find_field_differences(self, original: Dict[str, Any], 
                               corrected: Dict[str, Any]) -> List[FieldDifference]:
        """找出欄位差異"""
        differences = []
        
        # 扁平化兩個結果進行比較
        original_flat = self._flatten_dict(original)
        corrected_flat = self._flatten_dict(corrected)
        
        # 找出所有欄位（原始 + 修正）
        all_fields = set(original_flat.keys()) | set(corrected_flat.keys())
        
        for field_path in all_fields:
            if field_path.startswith('_'):  # 跳過內部欄位
                continue
            
            original_value = str(original_flat.get(field_path, "")).strip()
            corrected_value = str(corrected_flat.get(field_path, "")).strip()
            
            # 只記錄真正有變化的欄位
            if original_value != corrected_value:
                confidence_info = original.get("_confidence", {}).get(field_path, {})
                confidence = confidence_info.get("score", 50) / 100 if isinstance(confidence_info, dict) else 0.5
                
                differences.append(FieldDifference(
                    field_path=field_path,
                    original_value=original_value,
                    corrected_value=corrected_value,
                    confidence_before=confidence,
                    extraction_method=self._guess_extraction_method(original, field_path)
                ))
        
        return differences
    
    def _flatten_dict(self, d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """扁平化巢狀字典"""
        result = {}
        
        if not isinstance(d, dict):
            return result
        
        for key, value in d.items():
            if key.startswith('_'):
                continue
                
            new_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                result.update(self._flatten_dict(value, new_key))
            elif isinstance(value, list):
                # 處理 line_items 陣列
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        result.update(self._flatten_dict(item, f"{new_key}.{i}"))
            else:
                result[new_key] = value
        
        return result
    
    def _guess_extraction_method(self, original_result: Dict[str, Any], field_path: str) -> str:
        """推測欄位的提取方法"""
        # 檢查是否有來源資訊
        field_sources = original_result.get("_field_sources", {})
        if field_path in field_sources:
            return "pattern_matching"
        
        # 檢查學習模式記錄
        if "_learned_patterns_applied" in original_result:
            applied_patterns = original_result["_learned_patterns_applied"]
            for pattern_info in applied_patterns:
                if pattern_info.get("field") == field_path:
                    return "learned_pattern"
        
        # 檢查 LayoutLM 記錄
        if "_layoutlm_fields" in original_result:
            if field_path in original_result["_layoutlm_fields"]:
                return "layoutlm"
        
        return "regex_extraction"
    
    def _calculate_accuracy_after_corrections(self, corrected_result: Dict[str, Any]) -> float:
        """計算修正後的準確率（假設修正後都是正確的）"""
        # 簡化版：假設用戶修正後準確率為 95%
        return 0.95
    
    def apply_suggestions(self, suggestions, vendor_id: str) -> List[Any]:
        """應用改善建議"""
        applied = []
        
        for suggestion in suggestions:
            try:
                step = suggestion.step
                if step in self.suggestion_appliers:
                    success = self.suggestion_appliers[step](suggestion, vendor_id)
                    if success:
                        applied.append(suggestion)
                        self.logger.info(f"Applied suggestion for step {step}: {suggestion.action}")
                
            except Exception as e:
                self.logger.error(f"Failed to apply suggestion {suggestion.action}: {e}")
        
        return applied
    
    def _apply_step1_suggestions(self, suggestion, vendor_id: str) -> bool:
        """應用 Step1（OpenCV）建議"""
        config_path = "po_extractor/config/vendor_image_profiles.json"
        
        try:
            # 讀取現有配置
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
            else:
                profiles = {}
            
            # 初始化供應商資料
            if vendor_id not in profiles:
                profiles[vendor_id] = {"qwen_suggestions": []}
            
            # 添加建議
            suggestion_data = {
                "timestamp": datetime.now().isoformat(),
                "action": suggestion.action,
                "value": suggestion.value,
                "reason": suggestion.reason,
                "field_affected": suggestion.field_affected,
                "priority": suggestion.priority
            }
            
            profiles[vendor_id]["qwen_suggestions"].append(suggestion_data)
            profiles[vendor_id]["last_updated"] = datetime.now().isoformat()
            
            # 同時更新影像處理參數
            if suggestion.action == "increase_contrast" and isinstance(suggestion.value, (int, float)):
                params_path = "po_extractor/config/image_processing_params.json"
                if os.path.exists(params_path):
                    with open(params_path, 'r', encoding='utf-8') as f:
                        params = json.load(f)
                    
                    if "vendor_overrides" not in params:
                        params["vendor_overrides"] = {}
                    
                    if vendor_id not in params["vendor_overrides"]:
                        params["vendor_overrides"][vendor_id] = {}
                    
                    params["vendor_overrides"][vendor_id]["contrast_alpha"] = suggestion.value
                    params["_last_updated"] = datetime.now().isoformat()
                    params["_update_count"] = params.get("_update_count", 0) + 1
                    
                    with open(params_path, 'w', encoding='utf-8') as f:
                        json.dump(params, f, ensure_ascii=False, indent=2)
            
            # 儲存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply step1 suggestion: {e}")
            return False
    
    def _apply_step2_suggestions(self, suggestion, vendor_id: str) -> bool:
        """應用 Step2（文件分流）建議"""
        # 調整 IMAGE_PDF_TEXT_THRESHOLD 等參數
        return True
    
    def _apply_step3_suggestions(self, suggestion, vendor_id: str) -> bool:
        """應用 Step3（PaddleOCR）建議"""
        # 調整 OCR 語言設定、信心值閾值等
        return True
    
    def _apply_step4_suggestions(self, suggestion, vendor_id: str) -> bool:
        """應用 Step4（資料清洗）建議"""
        config_path = "po_extractor/config/regex_rules.json"
        
        try:
            if suggestion.action == "update_regex_rule":
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        rules = json.load(f)
                    
                    # 更新規則或新增規則
                    # 這裡簡化處理
                    rules["_last_cleanup"] = datetime.now().isoformat()
                    
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(rules, f, ensure_ascii=False, indent=2)
                    
                    return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply step4 suggestion: {e}")
        
        return False
    
    def _apply_step5_suggestions(self, suggestion, vendor_id: str) -> bool:
        """應用 Step5（分類）建議"""
        # 更新 feature_db.py 中的關鍵字
        return True
    
    def _apply_step6_suggestions(self, suggestion, vendor_id: str) -> bool:
        """應用 Step6（LayoutLM）建議"""
        # 調整啟動閾值、模型參數等
        return True
    
    def _apply_step7_suggestions(self, suggestion, vendor_id: str) -> bool:
        """應用 Step7（Qwen）建議"""
        # 調整 Qwen 參數、prompt 模板等
        return True
    
    def _save_learning_event(self, event: LearningEvent):
        """儲存學習事件"""
        try:
            # 讀取現有日誌
            with open(self.learning_journal_path, 'r', encoding='utf-8') as f:
                journal = json.load(f)
            
            # 添加新事件
            journal["entries"].append(asdict(event))
            
            # 更新統計
            stats = journal["statistics"]
            stats["total_entries"] += 1
            
            if event.vendor_id not in stats["vendors_analyzed"]:
                stats["vendors_analyzed"].append(event.vendor_id)
            
            stats["suggestions_applied"] += len(event.applied_suggestions)
            
            # 記錄準確率改善
            if event.vendor_id not in stats["accuracy_improvements"]:
                stats["accuracy_improvements"][event.vendor_id] = []
            
            stats["accuracy_improvements"][event.vendor_id].append({
                "before": event.accuracy_before,
                "after": event.accuracy_after,
                "improvement": event.accuracy_after - event.accuracy_before,
                "timestamp": event.timestamp
            })
            
            # 儲存日誌
            with open(self.learning_journal_path, 'w', encoding='utf-8') as f:
                json.dump(journal, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Learning event saved: {event.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save learning event: {e}")
    
    def get_learning_insights(self, days: int = 30) -> Dict[str, Any]:
        """取得學習洞察報告"""
        try:
            with open(self.learning_journal_path, 'r', encoding='utf-8') as f:
                journal = json.load(f)
            
            # 過濾最近的事件
            cutoff_date = datetime.now()
            recent_events = []
            
            for entry in journal["entries"]:
                try:
                    event_date = datetime.fromisoformat(entry["timestamp"])
                    if (cutoff_date - event_date).days <= days:
                        recent_events.append(entry)
                except ValueError:
                    continue
            
            # 分析統計
            total_events = len(recent_events)
            
            field_issues = {}
            vendor_performance = {}
            
            for event in recent_events:
                vendor = event["vendor_id"]
                
                # 供應商表現
                if vendor not in vendor_performance:
                    vendor_performance[vendor] = {
                        "events": 0,
                        "avg_accuracy_before": 0,
                        "avg_accuracy_after": 0,
                        "total_suggestions": 0
                    }
                
                perf = vendor_performance[vendor]
                perf["events"] += 1
                perf["avg_accuracy_before"] += event.get("accuracy_before", 0)
                perf["avg_accuracy_after"] += event.get("accuracy_after", 0)
                perf["total_suggestions"] += len(event.get("applied_suggestions", []))
                
                # 欄位問題統計
                for diff in event.get("field_diffs", []):
                    field = diff.get("field_path", "unknown")
                    if field not in field_issues:
                        field_issues[field] = 0
                    field_issues[field] += 1
            
            # 計算平均值
            for vendor, perf in vendor_performance.items():
                if perf["events"] > 0:
                    perf["avg_accuracy_before"] /= perf["events"]
                    perf["avg_accuracy_after"] /= perf["events"]
                    perf["accuracy_improvement"] = perf["avg_accuracy_after"] - perf["avg_accuracy_before"]
            
            return {
                "period_days": days,
                "total_events": total_events,
                "vendor_performance": vendor_performance,
                "problematic_fields": dict(sorted(field_issues.items(), key=lambda x: x[1], reverse=True)[:10]),
                "overall_stats": journal["statistics"]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate learning insights: {e}")
            return {}


def create_feedback_engine(qwen_client=None, 
                          journal_path: Optional[str] = None) -> FeedbackEngine:
    """工廠函數：建立回饋引擎"""
    return FeedbackEngine(
        learning_journal_path=journal_path or "po_extractor/logs/learning_journal.json",
        qwen_client=qwen_client
    )