"""Learning Advisor - 智能學習建議系統

分析低信心分數欄位，主動建議學習改進方案。
將4種驗證方法的結果轉化為具體的學習行動。

Usage:
    from po_extractor.pipeline.learning_advisor import suggest_learning_opportunities
    suggestions = suggest_learning_opportunities(json_result, raw_text)
"""
import json
import os
import re
from typing import Dict, List, Tuple, Any
from datetime import datetime

from po_extractor.config import LEARNED_PATTERNS_PATH, DEFAULT_OUTPUT_DIR

# 為了保持代碼兼容性，建立別名
OUTPUT_DIR = DEFAULT_OUTPUT_DIR


class LearningOpportunity:
    """學習機會記錄"""
    def __init__(self, field_path: str, current_value: str, confidence_info: Dict, 
                 suggestion_type: str, details: str, priority: int = 1):
        self.field_path = field_path
        self.current_value = current_value  
        self.confidence_info = confidence_info
        self.suggestion_type = suggestion_type  # 'pattern', 'validation', 'extraction'
        self.details = details
        self.priority = priority  # 1=高, 2=中, 3=低
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def suggest_learning_opportunities(po_result: Dict[str, Any], raw_text: str, 
                                   vendor_id: str) -> List[LearningOpportunity]:
    """分析PO抽取結果，生成學習建議。
    
    Args:
        po_result: JSON格式的抽取結果（包含_confidence等欄位）
        raw_text: 原始PDF文字  
        vendor_id: 供應商ID
        
    Returns:
        建議的學習機會清單，按優先級排序
    """
    opportunities = []
    confidence = po_result.get('_confidence', {})
    
    # 分析每個有信心分數的欄位
    for field_path, conf_info in confidence.items():
        score = conf_info.get('score', 100)
        reason = conf_info.get('reason', '')
        
        # 取得當前欄位值
        current_value = _get_nested_value(po_result, field_path)
        
        if score < 75:  # 低信心分數欄位
            opportunity = _analyze_low_confidence_field(
                field_path, current_value, conf_info, raw_text, vendor_id
            )
            if opportunity:
                opportunities.append(opportunity)
        
        elif score == 100 and current_value:  # 高信心欄位，可進一步強化
            opportunity = _analyze_reinforcement_opportunity(
                field_path, current_value, raw_text, vendor_id
            )
            if opportunity:
                opportunities.append(opportunity)
    
    # 分析空值欄位（可能是抽取遺漏）
    empty_fields = _find_empty_critical_fields(po_result)
    for field_path in empty_fields:
        opportunity = _analyze_missing_field(field_path, raw_text, vendor_id)
        if opportunity:
            opportunities.append(opportunity)
    
    # 按優先級排序
    opportunities.sort(key=lambda x: x.priority)
    return opportunities


def _analyze_low_confidence_field(field_path: str, current_value: str,
                                  conf_info: Dict, raw_text: str, 
                                  vendor_id: str) -> LearningOpportunity:
    """分析低信心分數欄位，建議學習方案"""
    score = conf_info.get('score', 0)
    reason = conf_info.get('reason', '')
    
    # 檢查是否在raw_text中能找到更好的值
    potential_values = _find_potential_values_in_text(field_path, raw_text)
    
    if score <= 50:
        if not current_value:
            # 完全空值，嘗試從文字中抽取
            if potential_values:
                return LearningOpportunity(
                    field_path=field_path,
                    current_value=current_value,
                    confidence_info=conf_info,
                    suggestion_type='pattern',
                    details=f"在PDF中發現可能的取值：{potential_values[:3]}。建議建立抽取Pattern。",
                    priority=1
                )
        else:
            # 有值但信心低，可能是格式問題或抽取錯誤
            return LearningOpportunity(
                field_path=field_path,
                current_value=current_value,
                confidence_info=conf_info,
                suggestion_type='validation',
                details=f"抽取值'{current_value}'信心分數僅{score}分。原因：{reason}。建議檢查格式驗證規則。",
                priority=1
            )
    
    elif score == 75:
        # 4種驗證中3種同意，找出不同意的方法
        return LearningOpportunity(
            field_path=field_path,
            current_value=current_value,
            confidence_info=conf_info,
            suggestion_type='validation',
            details=f"有1個驗證方法不同意。建議檢查{reason}部分的邏輯。",
            priority=2
        )
    
    return None


def _analyze_reinforcement_opportunity(field_path: str, current_value: str,
                                       raw_text: str, vendor_id: str) -> LearningOpportunity:
    """分析高信心欄位，尋找可強化的Pattern"""
    # 檢查當前是否已有learned pattern
    patterns = _load_learned_patterns()
    vendor_patterns = patterns.get(vendor_id, {})
    
    if field_path not in vendor_patterns:
        # 沒有learned pattern，可以從成功的抽取中學習
        context = _extract_context_around_value(current_value, raw_text)
        if context:
            return LearningOpportunity(
                field_path=field_path,
                current_value=current_value,
                confidence_info={'score': 100},
                suggestion_type='pattern', 
                details=f"成功抽取值'{current_value}'，可建立Pattern加強未來抽取：{context}",
                priority=3
            )
    
    return None


def _analyze_missing_field(field_path: str, raw_text: str, 
                          vendor_id: str) -> LearningOpportunity:
    """分析完全空值的重要欄位"""
    critical_fields = [
        'purchase_info.po_number', 'purchase_info.date', 'purchase_info.total_amount',
        'vendor_info.name', 'vendor_info.vendor_code'
    ]
    
    if field_path in critical_fields:
        potential_values = _find_potential_values_in_text(field_path, raw_text)
        if potential_values:
            return LearningOpportunity(
                field_path=field_path,
                current_value='',
                confidence_info={'score': 0, 'reason': '關鍵欄位缺失'},
                suggestion_type='extraction',
                details=f"關鍵欄位{field_path}為空，但PDF中可能包含：{potential_values[:2]}",
                priority=1
            )
    
    return None


def _find_potential_values_in_text(field_path: str, raw_text: str) -> List[str]:
    """在raw_text中尋找特定欄位的可能取值"""
    field_name = field_path.split('.')[-1]
    
    # 根據欄位類型定義搜尋策略
    search_patterns = {
        'po_number': [
            r'P\.?O\.?\s*(?:Number|No\.?)[\s:：]*(\d{8,12})',
            r'(?:Purchase|订单)\s*(?:Order|号)[\s:：]*(\d{8,12})',
            r'(\d{10,12})'  # Fallback: 10-12位數字
        ],
        'date': [
            r'(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{4})',
            r'(\d{4}[/.\-]\d{1,2}[/.\-]\d{1,2})'
        ],
        'total_amount': [
            r'(?:Total|总计|合计)[\s:：]*([0-9,.]+)',
            r'([0-9,]+\.[0-9]{2})'
        ],
        'vendor_code': [
            r'(?:Vendor|供应商)\s*(?:Code|代码)[\s:：]*(\d{5,10})',
            r'(\d{8,10})'
        ],
        'contact': [
            r'(?:Contact|联系人)[\s:：]*([A-Za-z\s\u4e00-\u9fff]+)',
            r'([A-Za-z]{2,}\s+[A-Za-z]{2,})'  # 姓名格式
        ]
    }
    
    patterns = search_patterns.get(field_name, [])
    found_values = []
    
    for pattern in patterns:
        matches = re.findall(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
        found_values.extend([m.strip() for m in matches if m.strip()])
    
    # 去重並過濾
    return list(set([v for v in found_values if len(v) > 0]))[:5]


def _extract_context_around_value(value: str, raw_text: str, context_length: int = 30) -> str:
    """提取數值周圍的上下文，用於生成Pattern"""
    escaped_value = re.escape(value)
    pattern = rf'(.{{{context_length}}}{escaped_value}.{{{context_length}}})'
    
    match = re.search(pattern, raw_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ''


def _get_nested_value(obj: Dict, path: str) -> Any:
    """取得巢狀字典中的值"""
    keys = path.split('.')
    current = obj
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return ''
    return current


def _find_empty_critical_fields(po_result: Dict) -> List[str]:
    """找出空值的關鍵欄位"""
    critical_fields = [
        'purchase_info.po_number',
        'purchase_info.date', 
        'purchase_info.total_amount',
        'vendor_info.name',
        'vendor_info.vendor_code',
        'purchase_info.contact'
    ]
    
    empty_fields = []
    for field_path in critical_fields:
        value = _get_nested_value(po_result, field_path)
        if not value or str(value).strip() == '':
            empty_fields.append(field_path)
    
    return empty_fields


def _load_learned_patterns() -> Dict:
    """載入學習模式"""
    try:
        with open(LEARNED_PATTERNS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# ═══════════════════════════════════════════════════════════════════════
# 學習建議應用介面
# ═══════════════════════════════════════════════════════════════════════

def apply_learning_suggestions(opportunities: List[LearningOpportunity]) -> Dict:
    """應用學習建議，自動改進系統
    
    Returns:
        改進統計資訊
    """
    stats = {
        'suggestions_total': len(opportunities),
        'patterns_generated': 0,
        'validations_updated': 0,
        'recommendations': []
    }
    
    for opp in opportunities:
        if opp.suggestion_type == 'pattern' and opp.priority <= 2:
            # 高優先級的Pattern建議，嘗試自動生成
            pattern_generated = _auto_generate_pattern_from_suggestion(opp)
            if pattern_generated:
                stats['patterns_generated'] += 1
        
        # 收集人工審查建議
        stats['recommendations'].append({
            'field': opp.field_path,
            'type': opp.suggestion_type,
            'details': opp.details,
            'priority': opp.priority,
            'timestamp': opp.timestamp
        })
    
    return stats


def _auto_generate_pattern_from_suggestion(opportunity: LearningOpportunity) -> bool:
    """從建議中自動生成Pattern（簡化版本）"""
    # 這裡可以整合更複雜的自動Pattern生成邏輯
    # 目前只做記錄，實際生成仍需人工驗證
    return False