"""Confidence scoring and human review flagging system.

Evaluates each extracted field using 4 methods:
    Method 1: Format validation (regex pattern check)
    Method 2: Completeness check (non-empty, reasonable length)
    Method 3: Value range / consistency (cross-field math checks)
    Method 4: Source verification (value found in raw text)

Scoring:
    - 4/4 agree → score 100, no review needed
    - 3/4 agree → score 75, flag the disagreeing method
    - 2/4 or less → score ≤ 50, flag for human review
    - Empty field → score 0, flag for human review
    - Overall accuracy < 90% → flag entire document
"""
import re
from dataclasses import fields as dc_fields
from typing import Dict, Any, List, Tuple


# ═══════════════════════════════════════════════════════════════════════
# FORMAT VALIDATORS (Method 1)
# ═══════════════════════════════════════════════════════════════════════

FORMAT_PATTERNS = {
    'po_number':      re.compile(r'^\d{10}$'),
    'date':           re.compile(r'^\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}$|^\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4}$'),
    'vendor_code':    re.compile(r'^\d{3,10}$'),
    'currency':       re.compile(r'^(USD|EUR|CNY|RMB|HKD|JPY)$', re.IGNORECASE),
    'total_amount':   re.compile(r'^[\d,]+\.?\d*$'),
    'phone':          re.compile(r'^[\d()+\-\s]{5,}$'),
    'fax':            re.compile(r'^[\d()+\-\s]{5,}$'),
    'email':          re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$'),
    'quantity':       re.compile(r'^[\d,.]+$'),
    'unit_price':     re.compile(r'^[\d,.]+$'),
    'net_price':      re.compile(r'^[\d,.]+$'),
    'unit':           re.compile(r'^(EA|PCS|ST|PC|SET|KG|M|L)$', re.IGNORECASE),
    'item_no':        re.compile(r'^\d{3,5}$'),
    'delivery_date':  re.compile(r'^\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}$'),
}


def _check_format(field_name: str, value: str) -> bool:
    """Method 1: Check if value matches expected format pattern."""
    pattern = FORMAT_PATTERNS.get(field_name)
    if pattern:
        return bool(pattern.match(value))
    # Text fields (name, address, contact, etc.) - just non-empty check
    return len(value.strip()) > 0


# ═══════════════════════════════════════════════════════════════════════
# COMPLETENESS CHECK (Method 2)
# ═══════════════════════════════════════════════════════════════════════

# Fields that should always be present per section
EXPECTED_FIELDS = {
    'purchase_info': ['po_number', 'date', 'currency'],
    'vendor_info':   ['vendor_code', 'name'],
    'bill_to':       ['company_name'],
    'ship_to':       ['company_name'],
    'line_item':     ['item_no', 'product_code', 'quantity', 'unit_price', 'net_price'],
    'schedule_line': ['delivery_date', 'quantity'],
}

# Fields that are nice-to-have but not critical
OPTIONAL_FIELDS = {
    'vendor_info':   ['address', 'country', 'fax', 'email'],
    'bill_to':       ['fax', 'email'],
    'ship_to':       ['fax', 'email'],
    'line_item':     ['price_unit', 'supplier_material', 'description'],
    'schedule_line': ['schedule_no'],
}


def _check_completeness(field_name: str, value: str, section: str) -> bool:
    """Method 2: Check if field has a reasonable value."""
    if not value or not value.strip():
        return False
    # Very short values (1 char) are suspicious for most fields
    if len(value.strip()) < 2 and field_name not in ('unit', 'currency'):
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════
# CROSS-FIELD CONSISTENCY (Method 3)
# ═══════════════════════════════════════════════════════════════════════

def _parse_num(s: str) -> float:
    """Try to parse a number string to float."""
    try:
        return float(s.replace(',', ''))
    except (ValueError, AttributeError):
        return 0.0


def _check_consistency(field_name: str, value: str, context: dict) -> bool:
    """Method 3: Cross-field math and logical consistency."""
    if field_name == 'net_price' and 'quantity' in context and 'unit_price' in context:
        qty = _parse_num(context['quantity'])
        up = _parse_num(context['unit_price'])
        np_val = _parse_num(value)
        if qty > 0 and up > 0 and np_val > 0:
            # Check with price_unit divisor if present
            divisor = 1.0
            pu = context.get('price_unit', '')
            pu_m = re.search(r'(\d[\d,]*)', pu)
            if pu_m:
                divisor = _parse_num(pu_m.group(1))
                if divisor == 0:
                    divisor = 1.0
            expected = qty * up / divisor
            ratio = np_val / expected if expected > 0 else 0
            return 0.95 <= ratio <= 1.05  # Allow 5% tolerance

    if field_name == 'total_amount' and 'line_net_prices' in context:
        total = _parse_num(value)
        line_sum = sum(_parse_num(p) for p in context['line_net_prices'])
        if total > 0 and line_sum > 0:
            ratio = total / line_sum
            return 0.95 <= ratio <= 1.05

    # For non-numeric fields, pass by default
    return True


# ═══════════════════════════════════════════════════════════════════════
# SOURCE VERIFICATION (Method 4)
# ═══════════════════════════════════════════════════════════════════════

def _check_source(value: str, raw_text: str) -> bool:
    """Method 4: Verify the extracted value appears in the raw text."""
    if not value or not raw_text:
        return False
    # Normalize both for comparison
    v = value.strip()
    if len(v) < 2:
        return v in raw_text
    # Check exact or close match
    if v in raw_text:
        return True
    # Try without spaces
    v_nospace = re.sub(r'\s+', '', v)
    t_nospace = re.sub(r'\s+', '', raw_text)
    if v_nospace in t_nospace:
        return True
    # For numbers, try matching just digits
    v_digits = re.sub(r'[^\d.]', '', v)
    if len(v_digits) >= 3 and v_digits in raw_text:
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════
# FIELD SCORER
# ═══════════════════════════════════════════════════════════════════════

def score_field(field_name: str, value: str, section: str,
                raw_text: str, context: dict) -> dict:
    """Score a single field using 4 methods.

    Returns:
        {
            "value": <str>,
            "score": <int 0-100>,
            "methods": [bool, bool, bool, bool],
            "review": <bool>,
            "reason": <str or None>
        }
    """
    if not value or not value.strip():
        # Check if it's an expected field
        expected = EXPECTED_FIELDS.get(section, [])
        optional = OPTIONAL_FIELDS.get(section, [])
        if field_name in expected:
            return {
                'score': 0, 'methods': [False, False, False, False],
                'review': True, 'reason': '必填欄位為空 (required field empty)'
            }
        elif field_name in optional:
            return {
                'score': 50, 'methods': [False, False, True, False],
                'review': False, 'reason': '選填欄位為空 (optional field empty)'
            }
        else:
            return {
                'score': 25, 'methods': [False, False, True, False],
                'review': True, 'reason': '欄位為空 (field empty)'
            }

    m1 = _check_format(field_name, value)
    m2 = _check_completeness(field_name, value, section)
    m3 = _check_consistency(field_name, value, context)
    m4 = _check_source(value, raw_text)

    methods = [m1, m2, m3, m4]
    agree_count = sum(methods)

    if agree_count == 4:
        return {'score': 100, 'methods': methods, 'review': False, 'reason': None}
    elif agree_count == 3:
        # Which method disagreed?
        labels = ['格式驗證', '完整性檢查', '交叉一致性', '來源驗證']
        disagreed = [labels[i] for i, v in enumerate(methods) if not v]
        return {
            'score': 75, 'methods': methods, 'review': False,
            'reason': f'{disagreed[0]}未通過'
        }
    elif agree_count == 2:
        labels = ['格式驗證', '完整性檢查', '交叉一致性', '來源驗證']
        disagreed = [labels[i] for i, v in enumerate(methods) if not v]
        return {
            'score': 50, 'methods': methods, 'review': True,
            'reason': f'需人工判斷: {", ".join(disagreed)}未通過'
        }
    else:
        labels = ['格式驗證', '完整性檢查', '交叉一致性', '來源驗證']
        disagreed = [labels[i] for i, v in enumerate(methods) if not v]
        return {
            'score': 25, 'methods': methods, 'review': True,
            'reason': f'需人工判斷: {", ".join(disagreed)}未通過'
        }


# ═══════════════════════════════════════════════════════════════════════
# DOCUMENT-LEVEL SCORING
# ═══════════════════════════════════════════════════════════════════════

def score_purchase_order(po_dict: dict, raw_text: str) -> dict:
    """Score all fields in a PurchaseOrder dict.

    Returns the po_dict augmented with:
        "_confidence": { "field.path": { score, review, reason } }
        "_review_required": bool
        "_review_fields": [list of field paths needing review]
        "_accuracy_pct": float (overall accuracy percentage)
    """
    confidence = {}
    review_fields = []

    # Collect line item net_prices for total cross-check
    line_net_prices = []
    for li in po_dict.get('line_items', []):
        if li.get('net_price'):
            line_net_prices.append(li['net_price'])

    # Score purchase_info
    pi = po_dict.get('purchase_info', {})
    pi_context = {
        'line_net_prices': line_net_prices,
    }
    for fname, fval in pi.items():
        if fname.startswith('_'):
            continue
        key = f'purchase_info.{fname}'
        result = score_field(fname, str(fval), 'purchase_info', raw_text, pi_context)
        confidence[key] = result
        if result['review']:
            review_fields.append(key)

    # Score vendor_info
    vi = po_dict.get('vendor_info', {})
    for fname, fval in vi.items():
        if fname.startswith('_'):
            continue
        key = f'vendor_info.{fname}'
        result = score_field(fname, str(fval), 'vendor_info', raw_text, {})
        confidence[key] = result
        if result['review']:
            review_fields.append(key)

    # Score bill_to
    bt = po_dict.get('bill_to', {})
    for fname, fval in bt.items():
        if fname.startswith('_'):
            continue
        key = f'bill_to.{fname}'
        result = score_field(fname, str(fval), 'bill_to', raw_text, {})
        confidence[key] = result
        if result['review']:
            review_fields.append(key)

    # Score ship_to
    st = po_dict.get('ship_to', {})
    for fname, fval in st.items():
        if fname.startswith('_'):
            continue
        key = f'ship_to.{fname}'
        result = score_field(fname, str(fval), 'ship_to', raw_text, {})
        confidence[key] = result
        if result['review']:
            review_fields.append(key)

    # Score line items
    for idx, li in enumerate(po_dict.get('line_items', [])):
        li_context = {
            'quantity': li.get('quantity', ''),
            'unit_price': li.get('unit_price', ''),
            'price_unit': li.get('price_unit', ''),
        }
        for fname, fval in li.items():
            if fname.startswith('_') or fname == 'schedule_lines':
                continue
            key = f'line_items[{idx}].{fname}'
            result = score_field(fname, str(fval), 'line_item', raw_text, li_context)
            confidence[key] = result
            if result['review']:
                review_fields.append(key)

        # Score schedule lines
        for sidx, sl in enumerate(li.get('schedule_lines', [])):
            for fname, fval in sl.items():
                if fname.startswith('_'):
                    continue
                key = f'line_items[{idx}].schedule[{sidx}].{fname}'
                result = score_field(fname, str(fval), 'schedule_line', raw_text, {})
                confidence[key] = result
                if result['review']:
                    review_fields.append(key)

    # Calculate overall accuracy
    total_fields = len(confidence)
    if total_fields > 0:
        total_score = sum(v['score'] for v in confidence.values())
        accuracy_pct = round(total_score / total_fields, 1)
    else:
        accuracy_pct = 0.0

    # Flag entire document for review (always show review interface)
    doc_review = True  # Always require review to show progress bars and review interface

    # Simplify confidence output: remove methods array, keep score/review/reason
    confidence_simple = {}
    for k, v in confidence.items():
        entry = {'score': v['score'], 'review': v['review']}
        if v.get('reason'):
            entry['reason'] = v['reason']
        confidence_simple[k] = entry

    po_dict['_confidence'] = confidence_simple
    po_dict['_review_required'] = doc_review
    po_dict['_review_fields'] = review_fields
    po_dict['_accuracy_pct'] = accuracy_pct

    return po_dict
