"""Apply learned patterns during extraction.

This module provides a mixin/utility that extractors can call to
apply learned regex patterns BEFORE their built-in regexes.

Usage in any extractor:
    from po_extractor.pipeline.pattern_applier import apply_learned_patterns
    
    class MyExtractor(BaseExtractor):
        def extract(self, raw_text, pages):
            po = PurchaseOrder(vendor_id="my_vendor")
            # Apply learned patterns first (fills in fields from corrections)
            apply_learned_patterns(po, "my_vendor", raw_text)
            # Then run normal extraction (only fills empty fields)
            self._extract_header(raw_text, po)
            ...
"""
import re
import json
import os
import logging
from typing import Optional

from po_extractor.config import LEARNED_PATTERNS_PATH

logger = logging.getLogger(__name__)

_PATTERNS_CACHE = None
_PATTERNS_MTIME = 0


def _load_patterns() -> dict:
    """Load learned patterns with file-change caching."""
    global _PATTERNS_CACHE, _PATTERNS_MTIME

    if not os.path.exists(LEARNED_PATTERNS_PATH):
        return {}

    mtime = os.path.getmtime(LEARNED_PATTERNS_PATH)
    if _PATTERNS_CACHE is not None and mtime == _PATTERNS_MTIME:
        return _PATTERNS_CACHE

    with open(LEARNED_PATTERNS_PATH, 'r', encoding='utf-8') as f:
        _PATTERNS_CACHE = json.load(f)
    _PATTERNS_MTIME = mtime
    return _PATTERNS_CACHE


def _set_nested_value(obj, field_path: str, value: str):
    """Set a value on a PurchaseOrder by dot-path like 'purchase_info.po_number'."""
    parts = field_path.split('.')
    current = obj
    for part in parts[:-1]:
        current = getattr(current, part, None)
        if current is None:
            return
    final_field = parts[-1]
    if hasattr(current, final_field):
        # Only set if currently empty (don't overwrite existing values)
        existing = getattr(current, final_field, '')
        if not existing or not str(existing).strip():
            setattr(current, final_field, value)


def _get_nested_value(obj, field_path: str) -> str:
    """Get a value from a PurchaseOrder by dot-path."""
    parts = field_path.split('.')
    current = obj
    for part in parts:
        current = getattr(current, part, None)
        if current is None:
            return ''
    return str(current) if current else ''


def apply_learned_patterns(po, vendor_id: str, raw_text: str) -> int:
    """Apply all learned patterns for a vendor to fill empty fields.

    Args:
        po: PurchaseOrder instance
        vendor_id: The vendor ID to look up patterns for
        raw_text: The cleaned PDF text

    Returns:
        Number of fields successfully filled by learned patterns.
    """
    patterns = _load_patterns()
    vendor_patterns = patterns.get(vendor_id, {})

    if not vendor_patterns:
        return 0

    filled_count = 0

    for field_path, pattern_list in vendor_patterns.items():
        if field_path.startswith('_'):
            continue

        # Skip if field already has a value
        existing = _get_nested_value(po, field_path)
        if existing and existing.strip():
            continue

        # Try patterns in order of most samples (most confident first)
        sorted_patterns = sorted(pattern_list, key=lambda p: p.get('samples', 0), reverse=True)

        for pat_info in sorted_patterns:
            try:
                flags = re.IGNORECASE if 'IGNORECASE' in pat_info.get('flags', '') else 0
                m = re.search(pat_info['pattern'], raw_text, flags)
                if m:
                    value = m.group(pat_info.get('group', 1)).strip()
                    if value:
                        _set_nested_value(po, field_path, value)
                        filled_count += 1
                        logger.debug(f"  Learned pattern filled: {field_path} = '{value}'")
                        break
            except (re.error, IndexError):
                continue

    if filled_count > 0:
        logger.info(f"  Learned patterns filled {filled_count} field(s) for {vendor_id}")

    return filled_count


def get_learned_keywords() -> dict:
    """Get vendor keywords learned from corrections.

    Returns: {vendor_id: [keyword1, keyword2, ...]}
    """
    patterns = _load_patterns()
    return patterns.get('_keywords', {})
