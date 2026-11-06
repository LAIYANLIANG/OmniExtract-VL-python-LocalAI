"""
Qwen裁決學習系統
================

當信心分數低於92%觸發Qwen裁決時，記錄觸發原因、裁決結果和人工修正，
用於後續改進步驟1-6的準確率，降低Qwen裁決的頻率。

功能:
1. 記錄Qwen觸發事件 
2. 儲存人工修正記錄
3. 分析低信心分數的原因
4. 生成改進建議以提升前6步準確率
5. 自動學習模式模式更新

作者: GitHub Copilot
日期: 2026-04-01
"""

import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

# 學習記錄儲存路徑
QWEN_LEARNING_LOG_PATH = "qwen_learning_log.json"
ACCURACY_PATTERNS_PATH = "learned_accuracy_patterns.json"

@dataclass
class QwenTriggerRecord:
    """Qwen觸發記錄"""
    timestamp: str
    document_hash: str  # PDF檔案內容hash
    trigger_reason: str  # "low_confidence", "manual_request" 
    confidence_score: float  # 觸發前的信心分數
    low_confidence_fields: List[str]  # 低信心分數的欄位
    vendor_type: str
    original_extraction: Dict[str, Any]  # 原始提取結果 
    qwen_corrections: Dict[str, Any]  # Qwen建議的修正
    manual_corrections: Dict[str, Any]  # 人工最終修正
    final_extraction: Dict[str, Any]  # 最終正確結果
    improvement_applied: bool = False  # 是否已應用改進

@dataclass 
class AccuracyPattern:
    """準確率提升模式"""
    field_path: str  # 欄位路径，如 "vendor_info.name"
    vendor_types: List[str]  # 適用的廠商類型
    problem_pattern: str  # 問題模式描述
    text_indicators: List[str]  # 文字指標詞彙
    correction_rule: str  # 修正規則
    confidence_boost: float  # 信心分數提升值
    success_count: int = 0  # 成功應用次數
    created_date: str = ""
    last_used_date: str = ""

class QwenLearningSystem:
    def __init__(self):
        self.learning_log = self._load_learning_log()
        self.accuracy_patterns = self._load_accuracy_patterns()
        
    def _load_learning_log(self) -> List[QwenTriggerRecord]:
        """載入Qwen觸發學習記錄"""
        if not os.path.exists(QWEN_LEARNING_LOG_PATH):
            return []
        try:
            with open(QWEN_LEARNING_LOG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [QwenTriggerRecord(**record) for record in data]
        except Exception as e:
            logger.warning(f"無法載入Qwen學習記錄: {e}")
            return []
    
    def _load_accuracy_patterns(self) -> List[AccuracyPattern]:
        """載入準確率提升模式"""
        if not os.path.exists(ACCURACY_PATTERNS_PATH):
            return []
        try:
            with open(ACCURACY_PATTERNS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [AccuracyPattern(**pattern) for pattern in data]
        except Exception as e:
            logger.warning(f"無法載入準確率模式: {e}")
            return []
    
    def _save_learning_log(self):
        """儲存學習記錄"""
        try:
            with open(QWEN_LEARNING_LOG_PATH, 'w', encoding='utf-8') as f:
                json.dump([asdict(record) for record in self.learning_log], 
                         f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"儲存Qwen學習記錄失敗: {e}")
            
    def _save_accuracy_patterns(self):
        """儲存準確率模式"""
        try:
            with open(ACCURACY_PATTERNS_PATH, 'w', encoding='utf-8') as f:
                json.dump([asdict(pattern) for pattern in self.accuracy_patterns], 
                         f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"儲存準確率模式失敗: {e}")
    
    def record_qwen_trigger(self, 
                           pdf_path: str,
                           raw_text: str,
                           confidence_score: float,
                           low_confidence_fields: List[str],
                           vendor_type: str,
                           original_extraction: Dict[str, Any],
                           trigger_reason: str = "low_confidence") -> str:
        """
        記錄Qwen觸發事件
        
        Returns:
            record_id: 記錄ID，用於後續更新
        """
        # 生成文件hash
        document_hash = hashlib.md5(raw_text.encode('utf-8')).hexdigest()[:16]
        
        record = QwenTriggerRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            document_hash=document_hash,
            trigger_reason=trigger_reason,
            confidence_score=confidence_score,
            low_confidence_fields=low_confidence_fields,
            vendor_type=vendor_type,
            original_extraction=original_extraction,
            qwen_corrections={},
            manual_corrections={},
            final_extraction={}
        )
        
        self.learning_log.append(record)
        self._save_learning_log()
        
        logger.info(f"記錄Qwen觸發事件: {trigger_reason}, 信心分數: {confidence_score:.1%}, "
                   f"低信心欄位: {len(low_confidence_fields)}, 廠商: {vendor_type}")
        
        return f"{document_hash}_{len(self.learning_log)-1}"
    
    def update_qwen_corrections(self, record_id: str, qwen_corrections: Dict[str, Any]):
        """更新Qwen修正結果"""
        try:
            doc_hash, idx = record_id.split('_')
            idx = int(idx)
            if idx < len(self.learning_log) and self.learning_log[idx].document_hash == doc_hash:
                self.learning_log[idx].qwen_corrections = qwen_corrections
                self._save_learning_log()
                logger.info(f"更新Qwen修正結果: {len(qwen_corrections)} 個修正")
        except Exception as e:
            logger.error(f"更新Qwen修正失敗: {e}")
    
    def record_manual_corrections(self, record_id: str, manual_corrections: Dict[str, Any], final_extraction: Dict[str, Any]):
        """記錄人工修正和最終結果"""
        try:
            doc_hash, idx = record_id.split('_')
            idx = int(idx)
            if idx < len(self.learning_log) and self.learning_log[idx].document_hash == doc_hash:
                record = self.learning_log[idx]
                record.manual_corrections = manual_corrections
                record.final_extraction = final_extraction
                self._save_learning_log()
                
                # 自動生成改進模式
                self._generate_improvement_patterns(record)
                
                logger.info(f"記錄人工修正: {len(manual_corrections)} 個修正")
        except Exception as e:
            logger.error(f"記錄人工修正失敗: {e}")
    
    def _generate_improvement_patterns(self, record: QwenTriggerRecord):
        """根據修正記錄自動生成改進模式"""
        if not record.manual_corrections:
            return
            
        for field_path, corrected_value in record.manual_corrections.items():
            if field_path in record.low_confidence_fields:
                # 分析為什麼這個欄位信心分數低
                original_value = self._get_field_value(record.original_extraction, field_path)
                
                # 尋找文字中的指標
                text_indicators = self._find_text_indicators(record.original_extraction.get('full_text', ''), 
                                                           original_value, corrected_value)
                
                # 建立改進模式
                pattern = AccuracyPattern(
                    field_path=field_path,
                    vendor_types=[record.vendor_type] if record.vendor_type else [],
                    problem_pattern=f"原始值 '{original_value}' 被修正為 '{corrected_value}'",
                    text_indicators=text_indicators,
                    correction_rule=f"當找到 {text_indicators[:3]} 時，優先選擇 '{corrected_value}' 類型的值",
                    confidence_boost=20.0,  # 提升20分信心分數
                    created_date=datetime.now().isoformat(),
                    last_used_date=""
                )
                
                # 避免重複模式
                if not self._pattern_exists(pattern):
                    self.accuracy_patterns.append(pattern)
                    logger.info(f"生成新的改進模式: {field_path} for {record.vendor_type}")
        
        self._save_accuracy_patterns()
    
    def _get_field_value(self, data: Dict, field_path: str) -> Any:
        """根據field_path獲取值"""
        parts = field_path.split('.')
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                current = current[idx] if 0 <= idx < len(current) else None
            else:
                return None
            if current is None:
                break
        return current
    
    def _find_text_indicators(self, text: str, original_value: Any, corrected_value: Any) -> List[str]:
        """在文字中尋找與修正相關的指標詞彙"""
        indicators = []
        
        # 尋找corrected_value附近的詞彙
        if corrected_value and str(corrected_value) in text:
            import re
            pattern = fr'.{{0,20}}{re.escape(str(corrected_value))}.{{0,20}}'
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                words = re.findall(r'\w+', match)
                indicators.extend(words)
        
        # 常見指標詞彙
        common_indicators = ['PO:', 'Order:', 'Number:', 'Code:', 'Date:', 'Amount:', 'Total:']
        for indicator in common_indicators:
            if indicator.lower() in text.lower():
                indicators.append(indicator)
        
        return list(set(indicators))[:10]  # 最多10個指標
    
    def _pattern_exists(self, new_pattern: AccuracyPattern) -> bool:
        """檢查是否已存在類似模式"""
        for existing in self.accuracy_patterns:
            if (existing.field_path == new_pattern.field_path and 
                existing.vendor_types == new_pattern.vendor_types and
                existing.problem_pattern == new_pattern.problem_pattern):
                return True
        return False
    
    def apply_accuracy_patterns(self, extraction_result: Dict[str, Any], raw_text: str, vendor_type: str) -> Tuple[Dict[str, Any], int]:
        """
        應用準確率提升模式到提取結果
        
        Returns:
            (modified_extraction, patterns_applied_count)
        """
        patterns_applied = 0
        modified_result = extraction_result.copy()
        
        for pattern in self.accuracy_patterns:
            if vendor_type in pattern.vendor_types or not pattern.vendor_types:
                # 檢查文字指標是否存在
                indicators_found = sum(1 for indicator in pattern.text_indicators 
                                     if indicator.lower() in raw_text.lower())
                
                if indicators_found >= len(pattern.text_indicators) * 0.3:  # 30%的指標符合
                    # 應用改進模式 (這裡需要根據具體correction_rule實作)
                    if self._apply_pattern_rule(modified_result, pattern, raw_text):
                        patterns_applied += 1
                        pattern.success_count += 1
                        pattern.last_used_date = datetime.now().isoformat()
        
        if patterns_applied > 0:
            self._save_accuracy_patterns()
            logger.info(f"應用了 {patterns_applied} 個準確率提升模式")
        
        return modified_result, patterns_applied
    
    def _apply_pattern_rule(self, extraction_result: Dict[str, Any], pattern: AccuracyPattern, raw_text: str) -> bool:
        """應用具體的改進規則"""
        # 這裡實作具體的修正邏輯
        # 目前是簡化版本，後續可以根據需要擴展
        
        current_value = self._get_field_value(extraction_result, pattern.field_path)
        if current_value and len(str(current_value).strip()) > 0:
            # 提升該欄位的信心分數
            confidence_path = f"_confidence.{pattern.field_path}"
            confidence_data = self._get_field_value(extraction_result, confidence_path)
            if confidence_data and isinstance(confidence_data, dict):
                old_score = confidence_data.get('score', 0)  
                confidence_data['score'] = min(100, old_score + pattern.confidence_boost)
                confidence_data['pattern_applied'] = pattern.field_path
                return True
        
        return False
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """獲取使用統計"""
        total_triggers = len(self.learning_log)
        low_confidence_triggers = sum(1 for r in self.learning_log if r.trigger_reason == "low_confidence")
        manual_corrections_count = sum(1 for r in self.learning_log if r.manual_corrections)
        patterns_count = len(self.accuracy_patterns)
        successful_patterns = sum(1 for p in self.accuracy_patterns if p.success_count > 0)
        
        return {
            "total_qwen_triggers": total_triggers,
            "low_confidence_triggers": low_confidence_triggers,  
            "manual_corrections_recorded": manual_corrections_count,
            "accuracy_patterns_generated": patterns_count,
            "successful_patterns": successful_patterns,
            "avg_pattern_success": sum(p.success_count for p in self.accuracy_patterns) / max(patterns_count, 1)
        }

# 全局實例
qwen_learning_system = QwenLearningSystem()