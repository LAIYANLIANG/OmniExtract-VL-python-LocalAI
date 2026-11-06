"""Knowledge Base Manager - 知識庫管理系統

類似TUNNIE的學習記錄系統，追蹤所有學習活動、Pattern演進和改善歷史。
提供學習分析、Pattern品質控制和知識萃取功能。

Usage:
    from po_extractor.pipeline.knowledge_base import KnowledgeBase
    kb = KnowledgeBase()
    kb.record_learning_event('siemens', 'contact', pattern_info, result)
"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

from po_extractor.config import WORKSPACE_DIR


@dataclass
class LearningEvent:
    """學習事件記錄"""
    timestamp: str
    vendor_id: str
    field_path: str
    event_type: str  # 'pattern_learned', 'correction_applied', 'validation_improved'
    before_value: str
    after_value: str
    confidence_before: float
    confidence_after: float
    source_file: str
    pattern_info: Optional[Dict] = None
    success_rate: Optional[float] = None
    notes: str = ''


@dataclass
class PatternQuality:
    """Pattern品質評估"""
    pattern: str
    vendor_id: str
    field_path: str
    total_applications: int
    successful_applications: int  
    success_rate: float
    last_used: str
    created_date: str
    source_files: List[str]
    confidence_scores: List[float]
    avg_confidence: float


class KnowledgeBase:
    """知識庫管理器"""
    
    def __init__(self):
        self.kb_dir = os.path.join(WORKSPACE_DIR, 'knowledge_base')
        self.events_file = os.path.join(self.kb_dir, 'learning_events.json')
        self.patterns_quality_file = os.path.join(self.kb_dir, 'patterns_quality.json')
        self.insights_file = os.path.join(self.kb_dir, 'learning_insights.json')
        
        # 確保目錄存在
        os.makedirs(self.kb_dir, exist_ok=True)
    
    def record_learning_event(self, vendor_id: str, field_path: str, 
                            event_type: str, before_value: str, after_value: str,
                            confidence_before: float, confidence_after: float,
                            source_file: str, pattern_info: Dict = None, 
                            notes: str = '') -> None:
        """記錄學習事件"""
        event = LearningEvent(
            timestamp=datetime.now().isoformat(),
            vendor_id=vendor_id,
            field_path=field_path,
            event_type=event_type,
            before_value=before_value,
            after_value=after_value,
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            source_file=source_file,
            pattern_info=pattern_info,
            notes=notes
        )
        
        self._append_event(event)
        
    def update_pattern_quality(self, vendor_id: str, field_path: str,
                             pattern: str, was_successful: bool, 
                             confidence_score: float, source_file: str) -> None:
        """更新Pattern品質評估"""
        quality_data = self._load_patterns_quality()
        pattern_key = f"{vendor_id}.{field_path}.{hash(pattern)}"
        
        if pattern_key not in quality_data:
            quality_data[pattern_key] = PatternQuality(
                pattern=pattern,
                vendor_id=vendor_id,
                field_path=field_path,
                total_applications=0,
                successful_applications=0,
                success_rate=0.0,
                last_used=datetime.now().isoformat(),
                created_date=datetime.now().isoformat(),
                source_files=[],
                confidence_scores=[],
                avg_confidence=0.0
            )
        
        quality = quality_data[pattern_key]
        quality.total_applications += 1
        if was_successful:
            quality.successful_applications += 1
        quality.success_rate = quality.successful_applications / quality.total_applications
        quality.last_used = datetime.now().isoformat()
        quality.confidence_scores.append(confidence_score)
        quality.avg_confidence = sum(quality.confidence_scores) / len(quality.confidence_scores)
        
        if source_file not in quality.source_files:
            quality.source_files.append(source_file)
        
        self._save_patterns_quality(quality_data)
    
    def get_learning_insights(self, days: int = 30) -> Dict:
        """取得學習洞察分析"""
        events = self._load_events()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_events = [
            e for e in events 
            if datetime.fromisoformat(e['timestamp']) >= cutoff_date
        ]
        
        insights = {
            'summary': {
                'total_events': len(recent_events),
                'unique_vendors': len(set(e['vendor_id'] for e in recent_events)),
                'unique_fields': len(set(e['field_path'] for e in recent_events)),
                'avg_confidence_improvement': self._calc_avg_confidence_improvement(recent_events)
            },
            'vendor_performance': self._analyze_vendor_performance(recent_events),
            'field_difficulty': self._analyze_field_difficulty(recent_events),
            'pattern_effectiveness': self._analyze_pattern_effectiveness(),
            'recommendations': self._generate_recommendations(recent_events)
        }
        
        # 儲存洞察
        self._save_insights(insights)
        return insights
    
    def get_problematic_patterns(self, min_applications: int = 3, 
                               max_success_rate: float = 0.6) -> List[Dict]:
        """找出有問題的Pattern"""
        quality_data = self._load_patterns_quality()
        problematic = []
        
        for pattern_key, quality in quality_data.items():
            if (quality.total_applications >= min_applications and 
                quality.success_rate <= max_success_rate):
                problematic.append({
                    'pattern': quality.pattern,
                    'vendor_id': quality.vendor_id,
                    'field_path': quality.field_path,
                    'success_rate': quality.success_rate,
                    'total_applications': quality.total_applications,
                    'avg_confidence': quality.avg_confidence,
                    'recommendation': '建議重新訓練或移除此Pattern'
                })
        
        return sorted(problematic, key=lambda x: x['success_rate'])
    
    def get_learning_summary_for_vendor(self, vendor_id: str) -> Dict:
        """取得特定供應商的學習摘要"""
        events = self._load_events()
        vendor_events = [e for e in events if e['vendor_id'] == vendor_id]
        
        if not vendor_events:
            return {'error': f'No learning data for vendor: {vendor_id}'}
        
        quality_data = self._load_patterns_quality()
        vendor_patterns = {
            k: v for k, v in quality_data.items() 
            if v.vendor_id == vendor_id
        }
        
        return {
            'vendor_id': vendor_id,
            'total_learning_events': len(vendor_events),
            'learning_timespan': {
                'first_event': min(e['timestamp'] for e in vendor_events),
                'last_event': max(e['timestamp'] for e in vendor_events)
            },
            'field_coverage': list(set(e['field_path'] for e in vendor_events)),
            'patterns_count': len(vendor_patterns),
            'avg_pattern_success_rate': sum(p.success_rate for p in vendor_patterns.values()) / len(vendor_patterns) if vendor_patterns else 0,
            'best_patterns': [
                {
                    'field_path': p.field_path,
                    'pattern': p.pattern[:50] + '...' if len(p.pattern) > 50 else p.pattern,
                    'success_rate': p.success_rate,
                    'applications': p.total_applications
                }
                for p in sorted(vendor_patterns.values(), 
                              key=lambda x: x.success_rate, reverse=True)[:5]
            ],
            'recent_improvements': [
                {
                    'field_path': e['field_path'],
                    'confidence_gain': e['confidence_after'] - e['confidence_before'],
                    'timestamp': e['timestamp']
                }
                for e in sorted(vendor_events, key=lambda x: x['timestamp'], reverse=True)[:10]
                if e['confidence_after'] > e['confidence_before']
            ]
        }
    
    def _append_event(self, event: LearningEvent) -> None:
        """添加學習事件到檔案"""
        events = self._load_events()
        events.append(asdict(event))
        
        with open(self.events_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
    
    def _load_events(self) -> List[Dict]:
        """載入學習事件"""
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _load_patterns_quality(self) -> Dict[str, PatternQuality]:
        """載入Pattern品質資料"""
        try:
            with open(self.patterns_quality_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: PatternQuality(**v) for k, v in data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_patterns_quality(self, quality_data: Dict[str, PatternQuality]) -> None:
        """儲存Pattern品質資料"""
        data = {k: asdict(v) for k, v in quality_data.items()}
        with open(self.patterns_quality_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_insights(self, insights: Dict) -> None:
        """儲存學習洞察"""
        insights['generated_at'] = datetime.now().isoformat()
        with open(self.insights_file, 'w', encoding='utf-8') as f:
            json.dump(insights, f, ensure_ascii=False, indent=2)
    
    def _calc_avg_confidence_improvement(self, events: List[Dict]) -> float:
        """計算平均信心分數改善"""
        improvements = [
            e['confidence_after'] - e['confidence_before'] 
            for e in events 
            if e['confidence_after'] > e['confidence_before']
        ]
        return sum(improvements) / len(improvements) if improvements else 0
    
    def _analyze_vendor_performance(self, events: List[Dict]) -> Dict:
        """分析供應商學習表現"""
        vendor_stats = defaultdict(lambda: {
            'events': 0, 
            'improvements': 0, 
            'avg_improvement': 0
        })
        
        for event in events:
            vendor = event['vendor_id']
            vendor_stats[vendor]['events'] += 1
            
            improvement = event['confidence_after'] - event['confidence_before']
            if improvement > 0:
                vendor_stats[vendor]['improvements'] += 1
                vendor_stats[vendor]['avg_improvement'] += improvement
        
        # 計算平均改善
        for vendor in vendor_stats:
            if vendor_stats[vendor]['improvements'] > 0:
                vendor_stats[vendor]['avg_improvement'] /= vendor_stats[vendor]['improvements']
        
        return dict(vendor_stats)
    
    def _analyze_field_difficulty(self, events: List[Dict]) -> Dict:
        """分析欄位學習難度"""
        field_stats = defaultdict(lambda: {
            'total_events': 0,
            'successful_improvements': 0,
            'difficulty_score': 0
        })
        
        for event in events:
            field = event['field_path']
            field_stats[field]['total_events'] += 1
            
            if event['confidence_after'] > event['confidence_before']:
                field_stats[field]['successful_improvements'] += 1
        
        # 計算難度分數（成功率越低，難度越高）
        for field in field_stats:
            stats = field_stats[field]
            if stats['total_events'] > 0:
                success_rate = stats['successful_improvements'] / stats['total_events']
                stats['difficulty_score'] = 1 - success_rate  # 0=容易, 1=困難
        
        return dict(field_stats)
    
    def _analyze_pattern_effectiveness(self) -> Dict:
        """分析Pattern效果"""
        quality_data = self._load_patterns_quality()
        
        if not quality_data:
            return {'no_data': True}
        
        total_patterns = len(quality_data)
        effective_patterns = sum(1 for q in quality_data.values() if q.success_rate >= 0.8)
        
        return {
            'total_patterns': total_patterns,
            'effective_patterns': effective_patterns,
            'effectiveness_rate': effective_patterns / total_patterns if total_patterns > 0 else 0,
            'top_patterns': [
                {
                    'vendor_id': q.vendor_id,
                    'field_path': q.field_path,
                    'success_rate': q.success_rate,
                    'applications': q.total_applications
                }
                for q in sorted(quality_data.values(), 
                              key=lambda x: (x.success_rate, x.total_applications), 
                              reverse=True)[:10]
            ]
        }
    
    def _generate_recommendations(self, events: List[Dict]) -> List[str]:
        """生成改善建議"""
        recommendations = []
        
        # 分析最近事件
        if len(events) == 0:
            recommendations.append("建議開始收集更多學習數據")
            return recommendations
        
        # 找出改善較少的供應商
        vendor_improvements = defaultdict(int)
        for event in events:
            if event['confidence_after'] > event['confidence_before']:
                vendor_improvements[event['vendor_id']] += 1
        
        if vendor_improvements:
            worst_vendor = min(vendor_improvements, key=vendor_improvements.get)
            recommendations.append(f"供應商 '{worst_vendor}' 的學習成效較差，建議增加人工校正範例")
        
        # 建議加強訓練的欄位
        field_failures = Counter()
        for event in events:
            if event['confidence_after'] <= event['confidence_before']:
                field_failures[event['field_path']] += 1
        
        if field_failures:
            problematic_field = field_failures.most_common(1)[0][0]
            recommendations.append(f"欄位 '{problematic_field}' 學習困難，建議檢查抽取邏輯或增加更多樣本")
        
        return recommendations


# ═══════════════════════════════════════════════════════════════════════
# 便利函數
# ═══════════════════════════════════════════════════════════════════════

def get_tunnie_style_report() -> Dict:
    """產生類似TUNNIE系統的學習報告"""
    kb = KnowledgeBase()
    insights = kb.get_learning_insights(days=90)  # 3個月的數據
    
    return {
        'report_title': 'PO Extractor Learning Intelligence Report',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'learning_summary': insights['summary'],
        'vendor_rankings': sorted(
            [(v, stats) for v, stats in insights['vendor_performance'].items()],
            key=lambda x: x[1]['avg_improvement'], 
            reverse=True
        ),
        'field_difficulty_ranking': sorted(
            [(f, stats) for f, stats in insights['field_difficulty'].items()],
            key=lambda x: x[1]['difficulty_score'],
            reverse=True
        ),
        'pattern_effectiveness': insights['pattern_effectiveness'],
        'action_recommendations': insights['recommendations'],
        'problematic_patterns': kb.get_problematic_patterns()
    }