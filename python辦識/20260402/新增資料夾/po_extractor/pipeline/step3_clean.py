"""Step 4: Data cleaning / normalization (Enhanced for Qwen Pipeline)."""
import re
import json
import logging
import unicodedata
from datetime import datetime
from .symbol_validator import normalize_text_symbols


def load_cleaning_rules() -> dict:
    """載入清洗規則（版本化控制）"""
    rules_path = "po_extractor/config/regex_rules.json"
    
    try:
        with open(rules_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 只載入活躍的規則
        active_rules = [rule for rule in config.get("rules", []) 
                       if rule.get("status") == "active"]
        
        return {
            "rules": active_rules,
            "version": config.get("_version", "1.0.0"),
            "failure_log": config.get("_failure_log", [])
        }
        
    except Exception as e:
        logging.warning(f"Failed to load cleaning rules: {e}")
        return {"rules": [], "version": "1.0.0", "failure_log": []}


def apply_cleaning_rules(text: str, rules_config: dict = None) -> tuple:
    """
    套用清洗規則
    
    Returns:
        tuple: (cleaned_text, applied_rules_count, failed_rules)
    """
    if rules_config is None:
        rules_config = load_cleaning_rules()
    
    cleaned = text
    applied_count = 0
    failed_rules = []
    
    for rule in rules_config["rules"]:
        try:
            pattern = rule["pattern"]
            replacement = rule["replacement"]
            
            # 套用規則
            before_length = len(cleaned)
            cleaned = re.sub(pattern, replacement, cleaned)
            after_length = len(cleaned)
            
            if before_length != after_length:
                applied_count += 1
                # 更新成功計數器
                update_rule_success(rule["id"])
            
        except re.error as e:
            failed_rules.append({
                "rule_id": rule["id"],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            update_rule_failure(rule["id"], str(e))
            
    return cleaned, applied_count, failed_rules


def update_rule_success(rule_id: str):
    """更新規則成功計數"""
    _update_rule_stats(rule_id, success=True)


def update_rule_failure(rule_id: str, error: str):
    """記錄規則失敗"""
    _update_rule_stats(rule_id, success=False, error=error)


def _update_rule_stats(rule_id: str, success: bool, error: str = None):
    """更新規則統計資訊"""
    rules_path = "po_extractor/config/regex_rules.json"
    
    try:
        with open(rules_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 更新規則統計
        for rule in config["rules"]:
            if rule["id"] == rule_id:
                if success:
                    rule["success_count"] = rule.get("success_count", 0) + 1
                else:
                    rule["failure_count"] = rule.get("failure_count", 0) + 1
                    # 記錄失敗詳情
                    if "_failure_log" not in config:
                        config["_failure_log"] = []
                    config["_failure_log"].append({
                        "rule_id": rule_id,
                        "error": error,
                        "timestamp": datetime.now().isoformat()
                    })
                break
        
        # 儲存更新
        with open(rules_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logging.error(f"Failed to update rule stats: {e}")


def clean_text_for_matching(raw_text: str) -> str:
    """
    Clean raw text for feature matching (Enhanced Version).
    1. Apply configurable rules from JSON
    2. Symbol normalization (variant chars → ASCII)
    3. Remove [cite: xx] markers
    4. Remove all whitespace
    5. Unicode NFKC normalization
    """
    # Step 1: 載入並套用規則
    rules_config = load_cleaning_rules()
    cleaned, applied_count, failed_rules = apply_cleaning_rules(raw_text, rules_config)
    
    # Step 2: 原有的清洗功能（向後相容）
    cleaned = normalize_text_symbols(cleaned)
    cleaned = re.sub(r'\[cite:\s*\d+\]', '', cleaned)
    cleaned = re.sub(r'\s+', '', cleaned)
    cleaned = unicodedata.normalize('NFKC', cleaned)
    
    logging.debug(f"Text cleaning applied {applied_count} rules, "
                  f"{len(failed_rules)} rules failed")
    
    return cleaned


def clean_text_preserve_structure(raw_text: str) -> str:
    """
    Clean text but preserve line structure for parsing (Enhanced Version).
    1. Apply configurable rules from JSON (structure-safe only)
    2. Symbol normalization (variant chars → ASCII)
    3. Remove [cite: xx] markers
    4. Normalize whitespace (collapse multiple spaces, keep newlines)
    5. Unicode NFKC normalization
    """
    # 只套用不影響結構的規則
    rules_config = load_cleaning_rules()
    structure_safe_rules = [
        rule for rule in rules_config["rules"]
        if rule["id"] not in ["clean_whitespace"]  # 排除移除空白的規則
    ]
    
    cleaned = raw_text
    
    # 套用安全規則
    for rule in structure_safe_rules:
        try:
            pattern = rule["pattern"]
            replacement = rule["replacement"]
            cleaned = re.sub(pattern, replacement, cleaned)
        except re.error:
            continue
    
    # 原有的清潔功能（向後相容）
    cleaned = normalize_text_symbols(cleaned)
    cleaned = re.sub(r'\[cite:\s*\d+\]', '', cleaned)
    cleaned = re.sub(r'[^\S\n]+', ' ', cleaned)
    cleaned = unicodedata.normalize('NFKC', cleaned)
    lines = [line.strip() for line in cleaned.split('\n')]
    cleaned = '\n'.join(line for line in lines if line)
    return cleaned


def record_user_correction_failure(rule_id: str, field_name: str, 
                                   expected_value: str, actual_value: str):
    """當用戶手動修正欄位時，記錄是哪個清洗規則失效"""
    rules_path = "po_extractor/config/regex_rules.json"
    
    failure_entry = {
        "rule_id": rule_id,
        "field": field_name,
        "expected": expected_value,
        "actual": actual_value,
        "timestamp": datetime.now().isoformat(),
        "status": "pending_review"
    }
    
    try:
        with open(rules_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if "_failure_log" not in config:
            config["_failure_log"] = []
        
        config["_failure_log"].append(failure_entry)
        
        with open(rules_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
        logging.warning(f"Recorded rule failure for {rule_id}: {field_name}")
        
    except Exception as e:
        logging.error(f"Failed to record rule failure: {e}")


def get_cleaning_statistics() -> dict:
    """取得清洗規則統計資訊"""
    rules_config = load_cleaning_rules()
    
    total_rules = len(rules_config["rules"])
    total_successes = sum(rule.get("success_count", 0) for rule in rules_config["rules"])
    total_failures = sum(rule.get("failure_count", 0) for rule in rules_config["rules"])
    
    return {
        "total_rules": total_rules,
        "rules_version": rules_config["version"],
        "total_applications": total_successes,
        "total_failures": total_failures,
        "success_rate": total_successes / max(total_successes + total_failures, 1),
        "most_used_rules": sorted(
            rules_config["rules"], 
            key=lambda x: x.get("success_count", 0), 
            reverse=True
        )[:5]
    }
