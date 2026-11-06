"""4+1 投票機制實現."""
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter


@dataclass
class Vote:
    """單一投票"""
    step_name: str
    value: Any
    confidence: float
    source: str = ""


@dataclass
class VotingSession:
    """投票會話"""
    field_name: str
    votes: List[Vote]
    majority_threshold: int = 3
    confidence_weight: float = 0.3


class VotingSystem:
    """4+1 投票機制核心實現"""
    
    def __init__(self, qwen_client=None):
        """
        初始化投票系統
        
        Args:
            qwen_client: Qwen 客戶端（第5票裁決者）
        """
        self.qwen_client = qwen_client
        self.logger = logging.getLogger(__name__)
        
        # 統計資訊
        self.total_sessions = 0
        self.majority_decisions = 0
        self.qwen_decisions = 0
        self.tie_situations = 0
    
    def collect_votes_for_field(self, field_name: str, 
                               step_results: Dict[str, Dict[str, Any]]) -> Option[VotingSession]:
        """
        收集某個欄位的所有投票
        
        Args:
            field_name: 欄位名稱（支援巢狀路徑，如 "purchase_info.po_number"）
            step_results: 各步驟結果 {"step_name": {"field_path": value, ...}}
            
        Returns:
            投票會話或 None
        """
        votes = []
        
        for step_name, result in step_results.items():
            if not result:
                continue
            
            # 取得欄位值
            value = self._get_nested_value(result, field_name)
            if value is not None and str(value).strip():
                
                # 取得信心值
                confidence = self._extract_confidence(result, field_name)
                
                votes.append(Vote(
                    step_name=step_name,
                    value=str(value).strip(),
                    confidence=confidence,
                    source=f"step_{step_name}"
                ))
        
        if len(votes) >= 2:  # 至少需要2票才有意義
            return VotingSession(field_name=field_name, votes=votes)
        
        return None
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """取得巢狀欄位值"""
        try:
            parts = field_path.split('.')
            current = data
            
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
                
                if current is None:
                    return None
            
            return current
        except Exception:
            return None
    
    def _extract_confidence(self, result: Dict[str, Any], field_path: str) -> float:
        """提取信心值"""
        # 檢查信心值資料
        confidence_data = result.get("_confidence", {})
        if field_path in confidence_data:
            conf = confidence_data[field_path]
            if isinstance(conf, dict):
                return conf.get("score", 50) / 100  # 轉換為 0-1
            elif isinstance(conf, (int, float)):
                return min(conf / 100 if conf > 1 else conf, 1.0)
        
        # 檢查欄位級別的信心值
        field_name = field_path.split('.')[-1]
        confidence_key = f"{field_name}_confidence"
        if confidence_key in result:
            return min(result[confidence_key], 1.0)
        
        return 0.5  # 預設信心值
    
    def execute_voting(self, session: VotingSession, 
                      image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        執行投票決策
        
        Args:
            session: 投票會話
            image_path: 原始影像路徑（供 Qwen 分析）
            
        Returns:
            投票結果
        """
        self.total_sessions += 1
        
        # Step 1: 多數決檢查
        majority_result = self._check_majority_vote(session)
        if majority_result:
            self.majority_decisions += 1
            return majority_result
        
        # Step 2: 加權投票（考慮信心值）
        weighted_result = self._weighted_voting(session)
        if weighted_result["confidence"] >= 0.8:
            return weighted_result
        
        # Step 3: Qwen 裁決（第5票）
        if self.qwen_client:
            qwen_result = self._qwen_arbitration(session, image_path)
            if qwen_result:
                self.qwen_decisions += 1
                return qwen_result
        
        # Step 4: 降級決策（最高信心值）
        return self._fallback_decision(session)
    
    def _check_majority_vote(self, session: VotingSession) -> Optional[Dict[str, Any]]:
        """檢查多數決"""
        value_counts = Counter(vote.value for vote in session.votes)
        
        for value, count in value_counts.items():
            if count >= session.majority_threshold:
                # 計算支持此值的票的平均信心值
                supporting_votes = [v for v in session.votes if v.value == value]
                avg_confidence = sum(v.confidence for v in supporting_votes) / len(supporting_votes)
                
                return {
                    "field": session.field_name,
                    "final_value": value,
                    "decision_method": "majority_vote",
                    "vote_count": f"{count}/{len(session.votes)}",
                    "confidence": min(avg_confidence * 1.1, 1.0),  # 多數決加成
                    "reasoning": f"{count} 票支持此值",
                    "supporting_steps": [v.step_name for v in supporting_votes],
                    "qwen_invoked": False
                }
        
        return None
    
    def _weighted_voting(self, session: VotingSession) -> Dict[str, Any]:
        """加權投票（考慮信心值）"""
        value_weights = {}
        
        for vote in session.votes:
            if vote.value not in value_weights:
                value_weights[vote.value] = {"weight": 0, "votes": []}
            
            # 權重 = 信心值 + 步驟權重
            step_weight = self._get_step_weight(vote.step_name)
            total_weight = vote.confidence * (1 - session.confidence_weight) + step_weight * session.confidence_weight
            
            value_weights[vote.value]["weight"] += total_weight
            value_weights[vote.value]["votes"].append(vote)
        
        # 找出最高權重值
        if value_weights:
            best_value = max(value_weights.items(), key=lambda x: x[1]["weight"])
            value, data = best_value
            
            # 正規化信心值
            max_possible_weight = len(session.votes) * 1.0
            normalized_confidence = min(data["weight"] / max_possible_weight, 1.0)
            
            return {
                "field": session.field_name,
                "final_value": value,
                "decision_method": "weighted_voting",
                "vote_count": f"{len(data['votes'])}/{len(session.votes)}",
                "confidence": normalized_confidence,
                "reasoning": f"加權投票勝出，權重: {data['weight']:.2f}",
                "supporting_steps": [v.step_name for v in data["votes"]],
                "qwen_invoked": False
            }
        
        return self._fallback_decision(session)
    
    def _get_step_weight(self, step_name: str) -> float:
        """取得步驟權重"""
        step_weights = {
            "step2_extract": 0.7,      # pdfplumber 文字提取
            "step3_ocr": 0.8,         # PaddleOCR
            "step4_classify": 0.6,     # 邏輯分類
            "step5_extract": 0.9,      # 供應商專用提取器
            "step6_layoutlm": 0.95,    # LayoutLM 深度學習
            "learned_patterns": 0.85,  # 學習模式
            "manual_correction": 1.0   # 人工修正
        }
        
        # 支援更靈活的命名
        for key, weight in step_weights.items():
            if key in step_name.lower():
                return weight
        
        return 0.5  # 預設權重
    
    def _qwen_arbitration(self, session: VotingSession, 
                         image_path: Optional[str]) -> Optional[Dict[str, Any]]:
        """Qwen 裁決（第5票）"""
        if not self.qwen_client:
            return None
        
        try:
            # 組建 Qwen 投票格式
            votes_dict = {
                vote.step_name: {
                    "value": vote.value,
                    "confidence": vote.confidence
                }
                for vote in session.votes
            }
            
            # 呼叫 Qwen 裁決
            qwen_result = self.qwen_client.vote_on_field(
                session.field_name, 
                votes_dict, 
                image_path
            )
            
            return {
                "field": session.field_name,
                "final_value": qwen_result.correct_value,
                "decision_method": "qwen_arbitration",
                "vote_count": f"1/{len(session.votes)} (Qwen決策)",
                "confidence": qwen_result.confidence,
                "reasoning": qwen_result.reasoning,
                "supporting_steps": ["qwen3-vl"],
                "qwen_invoked": True,
                "qwen_source": qwen_result.source,
                "response_time_ms": qwen_result.response_time_ms
            }
            
        except Exception as e:
            self.logger.error(f"Qwen arbitration failed: {e}")
            return None
    
    def _fallback_decision(self, session: VotingSession) -> Dict[str, Any]:
        """降級決策（最高信心值）"""
        if not session.votes:
            return {
                "field": session.field_name,
                "final_value": "",
                "decision_method": "no_votes",
                "vote_count": "0/0",
                "confidence": 0.0,
                "reasoning": "沒有有效投票",
                "supporting_steps": [],
                "qwen_invoked": False
            }
        
        # 選擇最高信心值的投票
        best_vote = max(session.votes, key=lambda v: v.confidence)
        
        return {
            "field": session.field_name,
            "final_value": best_vote.value,
            "decision_method": "highest_confidence_fallback",
            "vote_count": f"1/{len(session.votes)}",
            "confidence": best_vote.confidence,
            "reasoning": f"選擇最高信心值 ({best_vote.confidence:.2f}) 來自 {best_vote.step_name}",
            "supporting_steps": [best_vote.step_name],
            "qwen_invoked": False
        }
    
    def vote_on_multiple_fields(self, step_results: Dict[str, Dict[str, Any]], 
                               field_list: Optional[List[str]] = None,
                               image_path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        對多個欄位進行投票
        
        Args:
            step_results: 各步驟結果
            field_list: 要投票的欄位列表（None = 自動偵測）
            image_path: 影像路徑
            
        Returns:
            各欄位投票結果
        """
        if field_list is None:
            field_list = self._extract_all_fields(step_results)
        
        voting_results = {}
        
        for field_name in field_list:
            session = self.collect_votes_for_field(field_name, step_results)
            if session:
                result = self.execute_voting(session, image_path)
                voting_results[field_name] = result
        
        return voting_results
    
    def _extract_all_fields(self, step_results: Dict[str, Dict[str, Any]]) -> List[str]:
        """自動提取所有可投票的欄位"""
        all_fields = set()
        
        for step_name, result in step_results.items():
            if result:
                field_paths = self._get_all_field_paths(result)
                all_fields.update(field_paths)
        
        # 過濾掉內部欄位
        return [f for f in all_fields if not f.startswith('_')]
    
    def _get_all_field_paths(self, data: Dict[str, Any], prefix: str = "") -> List[str]:
        """遞歸取得所有欄位路徑"""
        paths = []
        
        for key, value in data.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict) and not key.startswith('_'):
                paths.extend(self._get_all_field_paths(value, current_path))
            elif not isinstance(value, (list, dict)) or key.startswith('_'):
                paths.append(current_path)
        
        return paths
    
    def get_statistics(self) -> Dict[str, Any]:
        """取得投票統計資訊"""
        return {
            "total_sessions": self.total_sessions,
            "majority_decisions": self.majority_decisions,
            "qwen_decisions": self.qwen_decisions,
            "tie_situations": self.tie_situations,
            "majority_rate": self.majority_decisions / max(self.total_sessions, 1),
            "qwen_usage_rate": self.qwen_decisions / max(self.total_sessions, 1)
        }


def create_voting_system(qwen_config_path: Optional[str] = None):
    """工廠函數：建立投票系統"""
    qwen_client = None
    
    if qwen_config_path:
        try:
            from .step7_qwen_audit import QwenClient
            qwen_client = QwenClient(qwen_config_path)
        except ImportError:
            logging.warning("Qwen client not available, voting system will use fallback decisions")
    
    return VotingSystem(qwen_client=qwen_client)