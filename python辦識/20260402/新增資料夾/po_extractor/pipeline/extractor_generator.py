"""Auto-Extractor Generator.

When a vendor accumulates >= AUTO_EXTRACTOR_THRESHOLD corrected samples,
this module generates a dedicated Python extractor file for that vendor.

The generated extractor uses the learned patterns from learned_patterns.json
and falls back to generic extraction for unlearned fields.

Usage:
    from po_extractor.pipeline.extractor_generator import check_and_generate_extractors
    generated = check_and_generate_extractors()
"""
import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, List

from po_extractor.config import (
    DEFAULT_CORRECTED_DIR, LEARNED_PATTERNS_PATH,
    AUTO_EXTRACTOR_THRESHOLD, VENDOR_FOLDER_MAP, WORKSPACE_DIR
)

logger = logging.getLogger(__name__)

EXTRACTORS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'extractors')
EXTRACTORS_DIR = os.path.normpath(EXTRACTORS_DIR)


def _count_corrected_samples(vendor_id: str, corrected_dir: str = None) -> int:
    """Count how many corrected JSON files exist for a vendor."""
    corrected_dir = corrected_dir or DEFAULT_CORRECTED_DIR
    count = 0
    # Check all folders - vendor_id might map to various folder names
    for folder_name in os.listdir(corrected_dir) if os.path.exists(corrected_dir) else []:
        folder_path = os.path.join(corrected_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue
        # Check if any JSON in this folder has this vendor_id
        for f in os.listdir(folder_path):
            if not f.endswith('.json'):
                continue
            json_path = os.path.join(folder_path, f)
            try:
                with open(json_path, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                if data.get('vendor_id') == vendor_id:
                    count += 1
            except (json.JSONDecodeError, KeyError):
                continue
    return count


def _get_existing_vendor_ids() -> set:
    """Get vendor IDs that already have dedicated extractors (not generic)."""
    # Read __init__.py to see which modules are imported
    init_path = os.path.join(EXTRACTORS_DIR, '__init__.py')
    existing = set()
    if os.path.exists(init_path):
        with open(init_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Find all "from .xxx import" patterns
        for m in re.finditer(r'from\s+\.(\w+)\s+import', content):
            module = m.group(1)
            if module not in ('base', 'registry', 'generic'):
                existing.add(module)
    return existing


def _safe_vendor_module_name(vendor_id: str) -> str:
    """Convert vendor_id to a safe Python module name."""
    name = re.sub(r'[^a-z0-9_]', '_', vendor_id.lower())
    name = re.sub(r'_+', '_', name).strip('_')
    if name[0].isdigit():
        name = 'v_' + name
    return name


def _safe_class_name(vendor_id: str) -> str:
    """Convert vendor_id to a PascalCase class name."""
    parts = re.split(r'[_\-\s]+', vendor_id)
    return ''.join(p.capitalize() for p in parts) + 'Extractor'


def generate_extractor_code(vendor_id: str, patterns: dict) -> str:
    """Generate Python source code for a vendor-specific extractor.

    The generated extractor:
    - Registers itself via @ExtractorRegistry.register
    - Applies learned patterns via base class
    - Has auto-generated regex from learned_patterns.json
    - Falls back to generic patterns for unlearned fields
    """
    module_name = _safe_vendor_module_name(vendor_id)
    class_name = _safe_class_name(vendor_id)
    vendor_patterns = patterns.get(vendor_id, {})

    # Group field patterns by section
    header_fields = {}
    vendor_fields = {}
    address_fields = {}
    for field_path, pat_list in vendor_patterns.items():
        if field_path.startswith('_'):
            continue
        if not pat_list:
            continue
        # Use the pattern with most samples
        best = max(pat_list, key=lambda p: p.get('samples', 0))
        section = field_path.split('.')[0]
        if section == 'purchase_info':
            header_fields[field_path] = best
        elif section == 'vendor_info':
            vendor_fields[field_path] = best
        elif section in ('bill_to', 'ship_to'):
            address_fields[field_path] = best

    # Build extraction code blocks
    header_code = _generate_section_code(header_fields, 'info', 'po.purchase_info')
    vendor_code = _generate_section_code(vendor_fields, 'v', 'po.vendor_info')
    address_code = _generate_address_code(address_fields)

    code = f'''"""Auto-generated extractor for vendor: {vendor_id}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Based on {sum(p.get("samples", 1) for pats in vendor_patterns.values() for p in pats)} learned samples.

This extractor was automatically generated from human-corrected samples.
It uses learned regex patterns and falls back to generic extraction.
You can edit this file to refine patterns further.
"""
import re
from typing import List
from .base import BaseExtractor
from .registry import ExtractorRegistry
from ..models.po_model import (
    PurchaseOrder, PurchaseInfo, VendorInfo, AddressInfo, LineItem, ScheduleLine
)
from ..pipeline.symbol_validator import validate_number, validate_date


@ExtractorRegistry.register("{vendor_id}")
class {class_name}(BaseExtractor):

    def extract(self, raw_text: str, pages: List[str]) -> PurchaseOrder:
        po = PurchaseOrder(vendor_id="{vendor_id}")
        self._extract_header(raw_text, po)
        self._extract_vendor(raw_text, po)
        self._extract_addresses(raw_text, po)
        self._extract_line_items(raw_text, po)
        self.apply_learned(po, raw_text)
        return po

    def _extract_header(self, text: str, po: PurchaseOrder):
        info = po.purchase_info
{header_code}

    def _extract_vendor(self, text: str, po: PurchaseOrder):
        v = po.vendor_info
{vendor_code}

    def _extract_addresses(self, text: str, po: PurchaseOrder):
        bill = po.bill_to
        ship = po.ship_to
{address_code}

    def _extract_line_items(self, text: str, po: PurchaseOrder):
        """Line item extraction - uses generic patterns.

        TODO: Refine this method based on the vendor\'s specific format.
        """
        # Generic SAP-style item pattern: 5-digit item + product code + qty + amount
        pattern = re.compile(
            r\'^(\\d{{4,5}})\\s+\'
            r\'(\\S+)\\s+\'
            r\'(.+?)\\s+\'
            r\'([\\d,]+\\.?\\d*)\\s+\'
            r\'(PCS|EA|ST|Piece|PC|SET|KG)\\s+\'
            r\'([\\d,]+\\.?\\d*)\',
            re.MULTILINE | re.IGNORECASE
        )
        for m in pattern.finditer(text):
            item = LineItem(
                item_no=m.group(1),
                product_code=m.group(2),
                description=m.group(3).strip(),
                quantity=validate_number(m.group(4), text),
                unit=m.group(5),
                unit_price=validate_number(m.group(6), text),
            )
            po.line_items.append(item)
'''
    return code


def _generate_section_code(fields: dict, var_name: str, obj_path: str) -> str:
    """Generate regex extraction code for a section."""
    if not fields:
        return '        pass  # No learned patterns yet'

    lines = []
    for field_path, pat_info in fields.items():
        field_name = field_path.split('.')[-1]
        pattern = pat_info['pattern']
        group = pat_info.get('group', 1)
        label = pat_info.get('label', '')
        flags = ', re.IGNORECASE' if 'IGNORECASE' in pat_info.get('flags', '') else ''

        lines.append(f'        # {label} (learned pattern, {pat_info.get("samples", 1)} sample(s))')
        lines.append(f'        m = re.search(r\'{pattern}\', text{flags})')
        lines.append(f'        if m:')
        lines.append(f'            {var_name}.{field_name} = m.group({group}).strip()')
        lines.append('')

    return '\n'.join(lines)


def _generate_address_code(fields: dict) -> str:
    """Generate address extraction code."""
    if not fields:
        return '        pass  # No learned patterns yet'

    lines = []
    for field_path, pat_info in fields.items():
        parts = field_path.split('.')
        section = parts[0]  # bill_to or ship_to
        field_name = parts[-1]
        var_name = 'bill' if section == 'bill_to' else 'ship'
        pattern = pat_info['pattern']
        group = pat_info.get('group', 1)
        label = pat_info.get('label', '')
        flags = ', re.IGNORECASE' if 'IGNORECASE' in pat_info.get('flags', '') else ''

        lines.append(f'        # {section}.{field_name}: {label} (learned)')
        lines.append(f'        m = re.search(r\'{pattern}\', text{flags})')
        lines.append(f'        if m:')
        lines.append(f'            {var_name}.{field_name} = m.group({group}).strip()')
        lines.append('')

    return '\n'.join(lines)


def _register_in_init(module_name: str):
    """Add import for new extractor in __init__.py."""
    init_path = os.path.join(EXTRACTORS_DIR, '__init__.py')
    if not os.path.exists(init_path):
        return

    with open(init_path, 'r', encoding='utf-8') as f:
        content = f.read()

    import_line = f'from .{module_name} import *  # auto-generated'
    if import_line in content or f'from .{module_name} ' in content:
        return  # Already imported

    # Append the import
    content = content.rstrip() + f'\n{import_line}\n'
    with open(init_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"  Registered in __init__.py: {import_line}")


def _register_in_feature_db(vendor_id: str, keywords: list):
    """Add vendor to feature_db.py for classification."""
    from po_extractor.features.feature_db import FEATURE_DB

    # Check if already exists
    for entry in FEATURE_DB:
        if entry['vendor_id'] == vendor_id:
            return

    # Add at runtime
    new_entry = {
        'vendor_id': vendor_id,
        'name': vendor_id.replace('_', ' ').title(),
        'keywords': keywords,
        'priority': 10,
    }
    FEATURE_DB.append(new_entry)

    # Also update the file on disk
    feature_db_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'features', 'feature_db.py'
    )
    feature_db_path = os.path.normpath(feature_db_path)
    if os.path.exists(feature_db_path):
        with open(feature_db_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Insert before the closing ]
        entry_str = (
            f'    {{\n'
            f'        "vendor_id": "{vendor_id}",\n'
            f'        "name": "{new_entry["name"]}",\n'
            f'        "keywords": {json.dumps(keywords, ensure_ascii=False)},\n'
            f'        "priority": 10,\n'
            f'    }},\n'
        )
        content = content.rstrip().rstrip(']').rstrip() + '\n' + entry_str + ']\n'
        with open(feature_db_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"  Added to feature_db.py: {vendor_id}")


def check_and_generate_extractors(corrected_dir: str = None) -> List[str]:
    """Check all vendors in corrected/ and generate extractors where threshold is met.

    Returns: List of vendor_ids for which extractors were generated.
    """
    corrected_dir = corrected_dir or DEFAULT_CORRECTED_DIR
    if not os.path.exists(corrected_dir):
        return []

    if not os.path.exists(LEARNED_PATTERNS_PATH):
        logger.info("No learned patterns yet. Run 'py -m po_extractor.learn' first.")
        return []

    with open(LEARNED_PATTERNS_PATH, 'r', encoding='utf-8') as f:
        all_patterns = json.load(f)

    existing_vendors = _get_existing_vendor_ids()
    generated = []

    # Find all vendor_ids in the patterns file
    for vendor_id in list(all_patterns.keys()):
        if vendor_id.startswith('_'):
            continue
        if vendor_id in existing_vendors:
            continue  # Already has a dedicated extractor
        if vendor_id == 'generic':
            continue

        # Count corrected samples
        sample_count = _count_corrected_samples(vendor_id, corrected_dir)
        if sample_count < AUTO_EXTRACTOR_THRESHOLD:
            logger.info(
                f"  {vendor_id}: {sample_count}/{AUTO_EXTRACTOR_THRESHOLD} samples "
                f"(need {AUTO_EXTRACTOR_THRESHOLD - sample_count} more)"
            )
            continue

        # Generate!
        module_name = _safe_vendor_module_name(vendor_id)
        class_name = _safe_class_name(vendor_id)
        output_path = os.path.join(EXTRACTORS_DIR, f"{module_name}.py")

        if os.path.exists(output_path):
            logger.info(f"  {vendor_id}: Extractor file already exists, skipping")
            continue

        logger.info(f"  Generating extractor for '{vendor_id}' ({sample_count} samples)...")
        code = generate_extractor_code(vendor_id, all_patterns)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)
        logger.info(f"  Created: {os.path.basename(output_path)}")

        # Register in __init__.py
        _register_in_init(module_name)

        # Add to feature_db
        keywords = all_patterns.get('_keywords', {}).get(vendor_id, [])
        if keywords:
            _register_in_feature_db(vendor_id, keywords)

        # Add to VENDOR_FOLDER_MAP (runtime only, print instruction)
        if vendor_id not in VENDOR_FOLDER_MAP:
            folder = vendor_id.upper().replace(' ', '_')
            VENDOR_FOLDER_MAP[vendor_id] = folder
            logger.info(f"  Mapped: {vendor_id} → {folder}")

        generated.append(vendor_id)

    return generated
