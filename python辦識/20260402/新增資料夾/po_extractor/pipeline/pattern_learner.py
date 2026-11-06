"""Pattern Learning Engine.

Compares original extraction vs human-corrected JSON to learn new regex patterns.
Stores learned patterns in learned_patterns.json for future extraction.

Workflow:
    1. System extracts PO → output_doc/<Vendor>/xxx.json
    2. User copies & corrects → corrected/<Vendor>/xxx.json
    3. `py -m po_extractor.learn` compares both, learns patterns
    4. Next extraction uses learned patterns first

Pattern Generation Strategy:
    For each field where original != corrected:
    - Find the corrected value in the raw PDF text
    - Capture surrounding context (label text before the value)
    - Generate a regex pattern: <context_label>\\s*[:：]?\\s*(<value_pattern>)
    - Store with vendor_id, field_path, pattern, confidence
"""
import json
import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from po_extractor.config import (
    DEFAULT_OUTPUT_DIR, DEFAULT_CORRECTED_DIR, DEFAULT_FINISH_DIR,
    LEARNED_PATTERNS_PATH, WORKSPACE_DIR
)
from po_extractor.pipeline.step2_extract import extract_text_from_pdf
from po_extractor.pipeline.step3_clean import clean_text_preserve_structure

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# LEARNED PATTERNS STORE
# ═══════════════════════════════════════════════════════════════════════

def load_learned_patterns() -> dict:
    """Load learned patterns from disk.

    Structure:
    {
        "<vendor_id>": {
            "<field_path>": [
                {
                    "pattern": "<regex>",
                    "group": 1,
                    "flags": "IGNORECASE",
                    "samples": 3,
                    "last_updated": "2026-03-30",
                    "source_files": ["xxx.json", ...]
                }
            ]
        },
        "_keywords": {
            "<vendor_id>": ["keyword1", "keyword2"]
        }
    }
    """
    if os.path.exists(LEARNED_PATTERNS_PATH):
        with open(LEARNED_PATTERNS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_learned_patterns(patterns: dict):
    """Save learned patterns to disk."""
    with open(LEARNED_PATTERNS_PATH, 'w', encoding='utf-8') as f:
        json.dump(patterns, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved learned patterns to: {os.path.basename(LEARNED_PATTERNS_PATH)}")


def get_vendor_patterns(vendor_id: str) -> Dict[str, list]:
    """Get all learned patterns for a specific vendor."""
    patterns = load_learned_patterns()
    return patterns.get(vendor_id, {})


# ═══════════════════════════════════════════════════════════════════════
# PATTERN GENERATION
# ═══════════════════════════════════════════════════════════════════════

def _escape_for_regex(text: str) -> str:
    """Escape special regex characters in text."""
    return re.escape(text)


def _find_value_context(value: str, raw_text: str, max_context: int = 80) -> Optional[Tuple[str, int]]:
    """Find the corrected value in raw text and extract its surrounding context.

    Returns: (context_before, position) or None if not found.
    """
    if not value or not raw_text:
        return None

    # Try exact match first
    pos = raw_text.find(value)
    if pos == -1:
        # Try without spaces
        value_nospace = re.sub(r'\s+', '', value)
        text_nospace = re.sub(r'\s+', '', raw_text)
        pos_ns = text_nospace.find(value_nospace)
        if pos_ns == -1:
            # Try matching just digits for numbers
            value_digits = re.sub(r'[^\d.]', '', value)
            if len(value_digits) >= 3:
                pos = raw_text.find(value_digits)
                if pos == -1:
                    return None
            else:
                return None
        else:
            # Map back to original position (approximate)
            pos = max(0, pos_ns - 5)

    # Extract context before the value
    start = max(0, pos - max_context)
    context = raw_text[start:pos].strip()
    return (context, pos)


def _generate_pattern_for_field(
    field_name: str, corrected_value: str, raw_text: str
) -> Optional[dict]:
    """Generate a regex pattern that can extract the corrected value from raw text.

    Strategy:
    1. Find the value in raw text
    2. Look at the label/context before it
    3. Build a pattern: <label_pattern>\\s*[:：]?\\s*(<value_capture>)
    """
    if not corrected_value or not corrected_value.strip():
        return None

    result = _find_value_context(corrected_value, raw_text)
    if result is None:
        return None

    context_before, pos = result

    # Extract the last meaningful label before the value
    # Look for Chinese or English label text
    label_match = re.search(
        r'([\u4e00-\u9fff]{2,10}|[A-Za-z][\w\s]{2,25})\s*[:：/]?\s*$',
        context_before
    )

    if label_match:
        label = label_match.group(1).strip()
        label_escaped = _escape_for_regex(label)
    else:
        # Use last 15 chars as anchor
        label_escaped = _escape_for_regex(context_before[-15:].strip()) if len(context_before) >= 5 else None
        if not label_escaped:
            return None

    # Build value capture pattern based on field type
    value_pattern = _get_value_pattern(field_name, corrected_value)

    # Compose full regex
    pattern = f'{label_escaped}\\s*[:：]?\\s*({value_pattern})'

    # Verify the pattern actually works
    try:
        m = re.search(pattern, raw_text, re.IGNORECASE)
        if m and _values_match(m.group(1), corrected_value):
            return {
                'pattern': pattern,
                'group': 1,
                'flags': 'IGNORECASE',
                'label': label_match.group(1).strip() if label_match else '',
            }
    except re.error:
        pass

    return None


def _get_value_pattern(field_name: str, sample_value: str) -> str:
    """Generate a regex capture pattern based on the field type and sample value."""
    # Numeric fields
    if field_name in ('quantity', 'unit_price', 'net_price', 'total_amount'):
        return r'[\d,]+\.?\d*'

    # Code fields
    if field_name in ('po_number', 'vendor_code'):
        digit_count = len(re.sub(r'\D', '', sample_value))
        return rf'\d{{{max(digit_count-1, 3)},{digit_count+2}}}'

    # Date fields
    if field_name in ('date', 'delivery_date'):
        return r'\d{1,4}[/.\-]\d{1,2}[/.\-]\d{2,4}'

    # Currency
    if field_name == 'currency':
        return r'[A-Z]{3}'

    # Unit
    if field_name == 'unit':
        return r'[A-Za-z]{1,5}'

    # Phone/fax
    if field_name in ('phone', 'fax'):
        return r'[\d()+\-\s]{5,25}'

    # Email
    if field_name == 'email':
        return r'\S+@\S+\.\S+'

    # Generic text (name, address, contact, etc.)
    return r'[^\n]{1,100}'


def _values_match(extracted: str, expected: str) -> bool:
    """Check if extracted value is close enough to expected."""
    e1 = re.sub(r'\s+', '', extracted.strip())
    e2 = re.sub(r'\s+', '', expected.strip())
    if e1 == e2:
        return True
    # For numbers, compare digit content
    d1 = re.sub(r'[^\d.]', '', e1)
    d2 = re.sub(r'[^\d.]', '', e2)
    if d1 and d2 and d1 == d2:
        return True
    # Substring match (extracted contains expected or vice versa)
    if len(e2) >= 3 and (e2 in e1 or e1 in e2):
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════
# DIFF ENGINE: COMPARE ORIGINAL VS CORRECTED
# ═══════════════════════════════════════════════════════════════════════

def _flatten_dict(d: dict, prefix: str = '') -> Dict[str, str]:
    """Flatten nested dict to dot-notation paths.

    Example: {"purchase_info": {"po_number": "123"}} → {"purchase_info.po_number": "123"}
    Skips _confidence, _review_*, line_items (handled separately).
    """
    flat = {}
    for key, val in d.items():
        if key.startswith('_') or key == 'line_items':
            continue
        path = f'{prefix}{key}' if not prefix else f'{prefix}.{key}'
        if isinstance(val, dict):
            flat.update(_flatten_dict(val, path))
        else:
            flat[path] = str(val) if val else ''
    return flat


def diff_original_vs_corrected(original: dict, corrected: dict) -> Dict[str, Tuple[str, str]]:
    """Find fields where original extraction differs from corrected version.

    Returns: {field_path: (original_value, corrected_value)}
    """
    orig_flat = _flatten_dict(original)
    corr_flat = _flatten_dict(corrected)
    diffs = {}

    for field_path, corr_val in corr_flat.items():
        orig_val = orig_flat.get(field_path, '')
        if orig_val.strip() != corr_val.strip() and corr_val.strip():
            diffs[field_path] = (orig_val, corr_val)

    return diffs


# ═══════════════════════════════════════════════════════════════════════
# MAIN LEARNING FUNCTION
# ═══════════════════════════════════════════════════════════════════════

def _get_raw_text_for_file(base_name: str) -> Optional[str]:
    """Get the raw PDF text for a given file (search in finish/)."""
    for root, dirs, files in os.walk(DEFAULT_FINISH_DIR):
        for f in files:
            if f.lower().endswith('.pdf'):
                f_base = os.path.splitext(f)[0]
                if f_base == base_name:
                    pdf_path = os.path.join(root, f)
                    result = extract_text_from_pdf(pdf_path)
                    if not result['is_image_pdf']:
                        return clean_text_preserve_structure(result['full_text'])
    return None


def learn_from_corrections(corrected_dir: str = None, output_dir: str = None) -> dict:
    """Main learning function: compare all corrected JSONs against originals.

    Scans corrected/<Vendor>/*.json, finds matching output_doc/<Vendor>/*.json,
    computes diffs, generates patterns, and saves to learned_patterns.json.

    Returns: summary dict with stats.
    """
    corrected_dir = corrected_dir or DEFAULT_CORRECTED_DIR
    output_dir = output_dir or DEFAULT_OUTPUT_DIR

    if not os.path.exists(corrected_dir):
        logger.warning(f"Corrected directory not found: {corrected_dir}")
        return {'status': 'no_corrections', 'files': 0}

    all_patterns = load_learned_patterns()
    stats = {
        'files_processed': 0,
        'fields_learned': 0,
        'patterns_generated': 0,
        'vendors': {},
    }

    # Scan corrected/<Vendor>/*.json
    for vendor_folder in os.listdir(corrected_dir):
        vendor_path = os.path.join(corrected_dir, vendor_folder)
        if not os.path.isdir(vendor_path):
            continue

        for json_file in os.listdir(vendor_path):
            if not json_file.endswith('.json'):
                continue

            corrected_path = os.path.join(vendor_path, json_file)
            original_path = os.path.join(output_dir, vendor_folder, json_file)

            if not os.path.exists(original_path):
                logger.warning(f"  No matching original for: {vendor_folder}/{json_file}")
                continue

            # Load both
            with open(corrected_path, 'r', encoding='utf-8') as f:
                corrected = json.load(f)
            with open(original_path, 'r', encoding='utf-8') as f:
                original = json.load(f)

            vendor_id = corrected.get('vendor_id', original.get('vendor_id', 'unknown'))
            logger.info(f"  Learning from: {vendor_folder}/{json_file} (vendor={vendor_id})")

            # Compute diffs
            diffs = diff_original_vs_corrected(original, corrected)
            if not diffs:
                logger.info(f"    No differences found, skipping")
                stats['files_processed'] += 1
                continue

            # Get raw PDF text
            base_name = os.path.splitext(json_file)[0]
            raw_text = _get_raw_text_for_file(base_name)
            if not raw_text:
                logger.warning(f"    Could not find raw PDF for: {base_name}")
                stats['files_processed'] += 1
                continue

            # Learn patterns for each diff field
            if vendor_id not in all_patterns:
                all_patterns[vendor_id] = {}

            for field_path, (orig_val, corr_val) in diffs.items():
                field_name = field_path.split('.')[-1]
                logger.info(f"    Field {field_path}: '{orig_val}' → '{corr_val}'")

                # Generate pattern
                pat_info = _generate_pattern_for_field(field_name, corr_val, raw_text)
                if pat_info:
                    # Store / update pattern
                    if field_path not in all_patterns[vendor_id]:
                        all_patterns[vendor_id][field_path] = []

                    existing = all_patterns[vendor_id][field_path]
                    # Check if similar pattern already exists
                    found = False
                    for ep in existing:
                        if ep['pattern'] == pat_info['pattern']:
                            ep['samples'] = ep.get('samples', 1) + 1
                            ep['last_updated'] = datetime.now().strftime('%Y-%m-%d')
                            if json_file not in ep.get('source_files', []):
                                ep.setdefault('source_files', []).append(json_file)
                            found = True
                            break

                    if not found:
                        existing.append({
                            'pattern': pat_info['pattern'],
                            'group': pat_info['group'],
                            'flags': pat_info.get('flags', ''),
                            'label': pat_info.get('label', ''),
                            'samples': 1,
                            'last_updated': datetime.now().strftime('%Y-%m-%d'),
                            'source_files': [json_file],
                        })

                    stats['patterns_generated'] += 1
                    logger.info(f"      ✓ Pattern learned: {pat_info['pattern'][:60]}...")
                else:
                    logger.info(f"      ✗ Could not generate pattern")

                stats['fields_learned'] += 1

            # Learn vendor keywords for classification
            if vendor_id != 'generic' and vendor_id != 'unknown':
                _learn_vendor_keywords(all_patterns, vendor_id, raw_text, corrected)

            stats['files_processed'] += 1
            stats['vendors'][vendor_id] = stats['vendors'].get(vendor_id, 0) + 1

    # Save all patterns
    save_learned_patterns(all_patterns)

    logger.info(f"\n=== Learning Summary ===")
    logger.info(f"  Files processed: {stats['files_processed']}")
    logger.info(f"  Fields with differences: {stats['fields_learned']}")
    logger.info(f"  Patterns generated: {stats['patterns_generated']}")
    for vid, cnt in stats['vendors'].items():
        logger.info(f"  Vendor '{vid}': {cnt} file(s)")

    return stats


def _learn_vendor_keywords(patterns: dict, vendor_id: str, raw_text: str, corrected: dict):
    """Extract unique keywords for vendor classification from the raw text."""
    if '_keywords' not in patterns:
        patterns['_keywords'] = {}
    if vendor_id not in patterns['_keywords']:
        patterns['_keywords'][vendor_id] = []

    existing_kw = set(patterns['_keywords'][vendor_id])

    # Good keyword candidates: company name, buyer, bill_to company
    for field in ['vendor_info.name', 'purchase_info.buyer', 'bill_to.company_name']:
        parts = field.split('.')
        val = corrected
        for p in parts:
            val = val.get(p, {}) if isinstance(val, dict) else ''
        if isinstance(val, str) and len(val) >= 3 and val not in existing_kw:
            # Verify it's in raw text
            if val in raw_text or re.sub(r'\s+', '', val) in re.sub(r'\s+', '', raw_text):
                existing_kw.add(val)

    patterns['_keywords'][vendor_id] = list(existing_kw)


def learn_from_pretrain(raw_text: str, fields_data: dict, vendor_id: str, filename: str = None) -> dict:
    """Learn patterns directly from user-provided field data and raw PDF text.
    
    This is used for the pretrain feature where users provide field-value pairs
    along with a PDF file.
    
    Args:
        raw_text: Raw PDF text 
        fields_data: Dict of field_path -> value (e.g., {"purchase_info.po_number": "12345"})
        vendor_id: Vendor identifier
        filename: Optional filename for tracking
        
    Returns:
        Dict with learning statistics
    """
    logger.info(f"=== Pretrain Learning for vendor '{vendor_id}' ===")
    
    all_patterns = load_learned_patterns()
    if vendor_id not in all_patterns:
        all_patterns[vendor_id] = {}
    
    stats = {
        'fields_processed': 0,
        'patterns_generated': 0,
        'patterns_failed': 0,
        'vendor_id': vendor_id,
        'source': filename or 'pretrain',
        'results': {}
    }
    
    for field_path, field_value in fields_data.items():
        if not field_value or not field_value.strip():
            continue
            
        stats['fields_processed'] += 1
        logger.info(f"  Processing field: {field_path} = '{field_value}'")
        
        field_name = field_path.split('.')[-1]
        pat_info = _generate_pattern_for_field(field_name, field_value, raw_text)
        
        if pat_info:
            # Store pattern
            if field_path not in all_patterns[vendor_id]:
                all_patterns[vendor_id][field_path] = []
            
            existing = all_patterns[vendor_id][field_path]
            found = False
            
            # Check if similar pattern exists
            for ep in existing:
                if ep['pattern'] == pat_info['pattern']:
                    ep['samples'] = ep.get('samples', 1) + 1
                    ep['last_updated'] = datetime.now().strftime('%Y-%m-%d')
                    if stats['source'] not in ep.get('source_files', []):
                        ep.setdefault('source_files', []).append(stats['source'])
                    found = True
                    break
            
            if not found:
                existing.append({
                    'pattern': pat_info['pattern'],
                    'group': pat_info['group'],
                    'flags': pat_info.get('flags', ''),
                    'label': pat_info.get('label', ''),
                    'samples': 1,
                    'last_updated': datetime.now().strftime('%Y-%m-%d'),
                    'source_files': [stats['source']],
                    'pretrained': True,  # Mark as pretrained
                })
            
            stats['patterns_generated'] += 1
            stats['results'][field_path] = 'success'
            logger.info(f"    ✓ Pattern learned")
        else:
            stats['patterns_failed'] += 1
            stats['results'][field_path] = 'not_found_in_pdf'
            logger.info(f"    ✗ Could not locate value in PDF text")
    
    # Learn vendor keywords
    if vendor_id != 'generic' and vendor_id != 'unknown':
        if '_keywords' not in all_patterns:
            all_patterns['_keywords'] = {}
        if vendor_id not in all_patterns['_keywords']:
            all_patterns['_keywords'][vendor_id] = []
        
        existing_kw = set(all_patterns['_keywords'][vendor_id])
        
        # Extract keywords from field values that appear in PDF
        for field_path, field_value in fields_data.items():
            if isinstance(field_value, str) and len(field_value) >= 3:
                if field_value in raw_text and field_value not in existing_kw:
                    existing_kw.add(field_value)
                    logger.info(f"    ✓ Keyword learned: {field_value}")
        
        all_patterns['_keywords'][vendor_id] = list(existing_kw)
    
    # Save patterns
    save_learned_patterns(all_patterns)
    
    logger.info(f"=== Pretrain Summary ===")
    logger.info(f"  Fields processed: {stats['fields_processed']}")
    logger.info(f"  Patterns generated: {stats['patterns_generated']}")
    logger.info(f"  Patterns failed: {stats['patterns_failed']}")
    
    return stats
