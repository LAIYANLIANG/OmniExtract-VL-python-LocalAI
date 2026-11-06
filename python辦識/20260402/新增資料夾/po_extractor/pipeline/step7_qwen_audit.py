"""Step 7: Qwen3-VL-4B 裁決與誤差分析引擎 (92%閾值觸發)."""
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import requests


@dataclass
class VotingResult:
    """投票結果"""
    field: str
    correct_value: str
    source: str  # "majority_vote" | "qwen_decision" | "manual"
    reasoning: str
    confidence: float
    qwen_invoked: bool = False
    response_time_ms: float = 0


@dataclass
class DiagnosisSuggestion:
    """診斷建議"""
    step: int  # 1-7
    action: str  # "increase_contrast", "adjust_threshold", etc.
    value: Any
    reason: str
    field_affected: str
    priority: str  # "high" | "medium" | "low"


class QwenClient:
    """Qwen3-VL 客戶端"""
    
    def __init__(self, config_path="po_extractor/config/qwen_config.json"):
        """初始化 Qwen 客戶端"""
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = logging.getLogger(__name__)
        
        # 統計資訊
        self.total_calls = 0
        self.successful_calls = 0
        self.total_response_time = 0
    
    def _load_config(self) -> Dict[str, Any]:
        """載入配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {self.config_path}")
            return self._default_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """預設配置"""
        return {
            "runtime": {
                "backend": "ollama",
                "api_endpoint": "http://localhost:11434/api/generate",
                "model_id": "adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M",
                "max_tokens": 2048,
                "temperature": 0.3,
                "timeout_seconds": 60
            },
            "thresholds": {
                "voting_trigger_score": 0.90,
                "diagnosis_trigger_score": 0.75,
                "confidence_threshold": 0.85
            }
        }
    
    def _call_ollama_api(self, prompt: str, image_path: Optional[str] = None) -> Optional[str]:
        """呼叫 Ollama API"""
        api_url = self.config["runtime"]["api_endpoint"]
        model_id = self.config["runtime"]["model_id"]
        timeout = self.config["runtime"]["timeout_seconds"]
        
        payload = {
            "model": model_id,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config["runtime"]["temperature"],
                "num_predict": self.config["runtime"]["max_tokens"]
            }
        }
        
        # 如果有影像，加入 base64 編碼
        if image_path and os.path.exists(image_path):
            try:
                import base64
                with open(image_path, "rb") as img_file:
                    img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                payload["images"] = [img_base64]
            except Exception as e:
                self.logger.warning(f"Failed to encode image: {e}")
        
        try:
            start_time = datetime.now()
            response = requests.post(api_url, json=payload, timeout=timeout)
            end_time = datetime.now()
            
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            self.total_response_time += response_time_ms
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error(f"Ollama API timeout after {timeout}s")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.error("Cannot connect to Ollama API. Is Ollama running?")
            return None
        except Exception as e:
            self.logger.error(f"Ollama API call failed: {e}")
            return None
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析 JSON 回應"""
        try:
            # 尋找 JSON 區塊
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # 如果解析失敗，記錄原始回應
        self.logger.warning(f"Failed to parse JSON response: {response[:200]}...")
        return None
    
    def vote_on_field(self, field_name: str, votes: Dict[str, Any], 
                     image_path: Optional[str] = None) -> VotingResult:
        """
        對欄位進行投票裁決
        
        Args:
            field_name: 欄位名稱
            votes: 各步驟的投票結果 {"step_name": {"value": "val", "confidence": 0.8}}
            image_path: 影像路徑（可選）
            
        Returns:
            投票結果
        """
        # 先嘗試多數決
        value_counts = {}
        for step, vote in votes.items():
            if vote and vote.get("value"):
                v = str(vote["value"]).strip()
                if v:
                    value_counts[v] = value_counts.get(v, 0) + 1
        
        # 如果有3票以上一致，直接採用（不需要 Qwen）
        for value, count in value_counts.items():
            if count >= 3:
                return VotingResult(
                    field=field_name,
                    correct_value=value,
                    source="majority_vote",
                    reasoning=f"{count}/{len(votes)} 票一致",
                    confidence=0.95,
                    qwen_invoked=False
                )
        
        # 票數分散 → 呼叫 Qwen 裁決
        self.total_calls += 1
        
        prompt = self._build_voting_prompt(field_name, votes)
        
        start_time = datetime.now()
        response = self._call_ollama_api(prompt, image_path)
        end_time = datetime.now()
        
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        if response:
            parsed = self._parse_json_response(response)
            if parsed:
                self.successful_calls += 1
                return VotingResult(
                    field=parsed.get("field", field_name),
                    correct_value=parsed.get("correct_value", ""),
                    source=parsed.get("source", "qwen_decision"),
                    reasoning=parsed.get("reasoning", "Qwen 視覺分析"),
                    confidence=parsed.get("confidence", 0.8),
                    qwen_invoked=True,
                    response_time_ms=response_time_ms
                )
        
        # Qwen 失敗 → 降級為最高信心值
        fallback_value = ""
        max_confidence = 0
        for step, vote in votes.items():
            if vote and vote.get("confidence", 0) > max_confidence:
                max_confidence = vote["confidence"]
                fallback_value = vote.get("value", "")
        
        return VotingResult(
            field=field_name,
            correct_value=fallback_value,
            source="fallback_highest_confidence",
            reasoning=f"Qwen 不可用，採用最高信心值結果 ({max_confidence:.2f})",
            confidence=max_confidence,
            qwen_invoked=True,
            response_time_ms=response_time_ms
        )
    
    def _build_voting_prompt(self, field_name: str, votes: Dict[str, Any]) -> str:
        """建構投票 Prompt"""
        vote_details = ""
        labels = ['A', 'B', 'C', 'D']
        
        for i, (step, vote) in enumerate(votes.items()):
            if i < len(labels) and vote:
                value = vote.get("value", "")
                confidence = vote.get("confidence", 0)
                vote_details += f"結果 {labels[i]}（來源：{step}）：「{value}」（信心值：{confidence:.2f}）\n"
        
        system_prompt = self.config.get("prompts", {}).get("system_prompt", "")
        template = self.config.get("prompts", {}).get("audit_template", "")
        
        if template:
            prompt = template.format(field_name=field_name, vote_details=vote_details)
        else:
            # 預設模板
            prompt = f"""我有以下解析結果，它們在「{field_name}」上有差異：

{vote_details}

請你重新觀察原始文件，判斷哪個結果正確，或者給出你認為正確的數值。
回覆格式（JSON）：
{{"field": "{field_name}", "correct_value": "你判斷的正確值", "source": "採用哪個結果 或 自行判斷", "reasoning": "判斷理由", "confidence": 0.95}}"""
        
        if system_prompt:
            prompt = f"{system_prompt}\n\n{prompt}"
        
        return prompt
    
    def diagnose_corrections(self, vendor_id: str, field_diffs: List[Dict[str, Any]], 
                           image_path: Optional[str] = None) -> List[DiagnosisSuggestion]:
        """
        診斷用戶修正，產出改善建議
        
        Args:
            vendor_id: 供應商ID
            field_diffs: 欄位差異列表 [{"field": "xx", "original": "xx", "corrected": "xx"}]
            image_path: 原始影像路徑
            
        Returns:
            診斷建議列表
        """
        if not field_diffs:
            return []
        
        self.total_calls += 1
        
        # 組建診斷 Prompt
        diff_details = ""
        for diff in field_diffs:
            diff_details += f"- 欄位「{diff['field']}」：系統值=「{diff['original']}」→ 正確值=「{diff['corrected']}」\n"
        
        template = self.config.get("prompts", {}).get("diagnosis_template", "")
        if template:
            prompt = template.format(vendor_id=vendor_id, diff_details=diff_details)
        else:
            prompt = f"""以下是供應商 {vendor_id} 的採購單解析錯誤分析：

差異欄位：
{diff_details}

請分析以上錯誤可能的原因，並給出改善建議。
回覆格式（JSON陣列）：
[{{"step": 1, "action": "increase_contrast", "value": 1.2, "reason": "此類發票的統編字體較淡，位於浮水印上方", "field_affected": "tax_id", "priority": "high"}}]"""
        
        response = self._call_ollama_api(prompt, image_path)
        
        if response:
            try:
                # 尋找 JSON 陣列
                start = response.find('[')
                end = response.rfind(']') + 1
                
                if start != -1 and end > start:
                    json_str = response[start:end]
                    suggestions_data = json.loads(json_str)
                    
                    suggestions = []
                    for item in suggestions_data:
                        suggestions.append(DiagnosisSuggestion(
                            step=item.get("step", 1),
                            action=item.get("action", "unknown"),
                            value=item.get("value", None),
                            reason=item.get("reason", ""),
                            field_affected=item.get("field_affected", ""),
                            priority=item.get("priority", "medium")
                        ))
                    
                    self.successful_calls += 1
                    return suggestions
                    
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse diagnosis response: {e}")
        
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """取得統計資訊"""
        success_rate = self.successful_calls / max(self.total_calls, 1)
        avg_response_time = self.total_response_time / max(self.successful_calls, 1)
        
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "success_rate": success_rate,
            "avg_response_time_ms": avg_response_time
        }


class QwenAuditor:
    """Qwen 裁決器主類別"""
    
    def __init__(self, config_path="po_extractor/config/qwen_config.json"):
        """初始化裁決器"""
        self.qwen_client = QwenClient(config_path)
        self.logger = logging.getLogger(__name__)
        
        # 載入配置閾值
        config = self.qwen_client.config
        self.voting_threshold = config["thresholds"]["voting_trigger_score"]
        self.diagnosis_threshold = config["thresholds"]["diagnosis_trigger_score"]
    
    def should_trigger_voting(self, extraction_result: Dict[str, Any]) -> bool:
        """判斷是否需要觸發投票機制"""
        confidence_scores = extraction_result.get("_confidence", {})
        if not confidence_scores:
            return True  # 沒有信心值資料，啟動裁決
        
        # 計算平均信心值
        scores = [score.get("score", 0) for score in confidence_scores.values() if isinstance(score, dict)]
        avg_score = sum(scores) / max(len(scores), 1) / 100  # 轉換為 0-1 範圍
        
        should_trigger = avg_score < self.voting_threshold
        
        if should_trigger:
            self.logger.info(f"Voting triggered: avg_confidence={avg_score:.2f} < {self.voting_threshold}")
        
        return should_trigger
    
    def execute_audit(self, extraction_results: Dict[str, Dict[str, Any]], 
                     image_path: Optional[str] = None) -> Dict[str, VotingResult]:
        """
        執行裁決流程
        
        Args:
            extraction_results: 各步驟的提取結果 {"step_name": {...}}
            image_path: 原始影像路徑
            
        Returns:
            各欄位的投票結果
        """
        # 收集所有欄位的投票
        field_votes = {}
        
        # 遍歷所有步驟結果
        for step_name, result in extraction_results.items():
            if not result:
                continue
            
            # 扁平化提取欄位
            flattened_fields = self._flatten_dict(result)
            
            for field_path, value in flattened_fields.items():
                if field_path.startswith('_'):  # 跳過內部欄位
                    continue
                
                if field_path not in field_votes:
                    field_votes[field_path] = {}
                
                confidence = self._get_field_confidence(result, field_path)
                field_votes[field_path][step_name] = {
                    "value": value,
                    "confidence": confidence
                }
        
        # 對每個欄位執行投票
        voting_results = {}
        for field_path, votes in field_votes.items():
            if len(votes) >= 2:  # 至少需要2個投票才有意義
                result = self.qwen_client.vote_on_field(field_path, votes, image_path)
                voting_results[field_path] = result
        
        return voting_results
    
    def _flatten_dict(self, d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """扁平化巢狀字典"""
        result = {}
        for key, value in d.items():
            new_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict) and not key.startswith('_'):
                result.update(self._flatten_dict(value, new_key))
            elif isinstance(value, list):
                # 處理 line_items 等陣列
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        result.update(self._flatten_dict(item, f"{new_key}.{i}"))
            else:
                result[new_key] = value
        
        return result
    
    def _get_field_confidence(self, result: Dict[str, Any], field_path: str) -> float:
        """取得欄位信心值"""
        confidence_data = result.get("_confidence", {})
        if field_path in confidence_data:
            conf = confidence_data[field_path]
            if isinstance(conf, dict):
                return conf.get("score", 50) / 100
        return 0.5  # 預設信心值


def audit_extraction_results(extraction_results: Dict[str, Dict[str, Any]], 
                            image_path: Optional[str] = None,
                            config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    主要入口函數：裁決提取結果
    
    Args:
        extraction_results: 各步驟提取結果
        image_path: 原始影像路徑
        config_path: 配置檔案路徑
        
    Returns:
        裁決結果
    """
    auditor = QwenAuditor(config_path) if config_path else QwenAuditor()
    
    # 檢查是否需要裁決
    combined_result = {}
    for result in extraction_results.values():
        if result:
            combined_result.update(result)
    
    if not auditor.should_trigger_voting(combined_result):
        return {"audit_skipped": True, "reason": "confidence_above_threshold"}
    
    # 執行裁決
    voting_results = auditor.execute_audit(extraction_results, image_path)
    
    # 統計資訊
    stats = auditor.qwen_client.get_statistics()
    
    return {
        "audit_executed": True,
        "voting_results": {k: asdict(v) for k, v in voting_results.items()},
        "total_fields_audited": len(voting_results),
        "qwen_invoked_count": sum(1 for v in voting_results.values() if v.qwen_invoked),
        "statistics": stats
    }