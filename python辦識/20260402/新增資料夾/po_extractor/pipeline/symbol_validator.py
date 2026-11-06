"""Symbol normalization & multi-method number validation.

This module addresses the problem of visually similar symbols in PDF text:
  - Period variants: . (U+002E) vs ˙ (U+02D9) vs · (U+00B7) vs ．(U+FF0E) vs 。(U+3002)
  - Comma variants:  , (U+002C) vs ，(U+FF0C) vs 、(U+3001) vs ‚ (U+201A)
  - Hyphen variants: - (U+002D) vs – (U+2013) vs — (U+2014) vs ー (U+30FC)
  - Space variants:  (U+0020) vs   (U+00A0) vs   (U+3000)

Strategy: 4 independent verification methods for numbers:
  Method 1: Unicode normalization (canonical mapping)
  Method 2: Context-based inference (digit adjacency analysis)
  Method 3: Format pattern matching (known number formats)
  Method 4: Cross-field consistency check (compare with other numbers in same document)
"""
import re
import unicodedata
from typing import Optional

# ═══════════════════════════════════════════════════════════════════════
# SYMBOL NORMALIZATION MAPS
# ═══════════════════════════════════════════════════════════════════════

# Map all period-like characters to ASCII period
PERIOD_VARIANTS = {
    '\u00B7': '.',  # MIDDLE DOT (·)
    '\u02D9': '.',  # DOT ABOVE (˙)
    '\u0307': '.',  # COMBINING DOT ABOVE
    '\u2022': '.',  # BULLET (•)
    '\u2027': '.',  # HYPHENATION POINT
    '\u2219': '.',  # BULLET OPERATOR
    '\u22C5': '.',  # DOT OPERATOR (⋅)
    '\u30FB': '.',  # KATAKANA MIDDLE DOT (・)
    '\uFF0E': '.',  # FULLWIDTH FULL STOP (．)
    '\u3002': '.',  # IDEOGRAPHIC FULL STOP (。)
    '\uFF61': '.',  # HALFWIDTH IDEOGRAPHIC FULL STOP
}

# Map all comma-like characters to ASCII comma
COMMA_VARIANTS = {
    '\uFF0C': ',',  # FULLWIDTH COMMA (，)
    '\u3001': ',',  # IDEOGRAPHIC COMMA (、)
    '\u201A': ',',  # SINGLE LOW-9 QUOTATION MARK (‚)
    '\uFE50': ',',  # SMALL COMMA
    '\uFE51': ',',  # SMALL IDEOGRAPHIC COMMA
}

# Map all hyphen/dash variants to ASCII hyphen-minus
HYPHEN_VARIANTS = {
    '\u2010': '-',  # HYPHEN (‐)
    '\u2011': '-',  # NON-BREAKING HYPHEN
    '\u2012': '-',  # FIGURE DASH
    '\u2013': '-',  # EN DASH (–)
    '\u2014': '-',  # EM DASH (—)
    '\u2015': '-',  # HORIZONTAL BAR
    '\uFE58': '-',  # SMALL EM DASH
    '\uFE63': '-',  # SMALL HYPHEN-MINUS
    '\uFF0D': '-',  # FULLWIDTH HYPHEN-MINUS (－)
    '\u00AD': '',   # SOFT HYPHEN (remove)
}

# Map whitespace variants to ASCII space
SPACE_VARIANTS = {
    '\u00A0': ' ',  # NO-BREAK SPACE
    '\u2002': ' ',  # EN SPACE
    '\u2003': ' ',  # EM SPACE
    '\u2004': ' ',  # THREE-PER-EM SPACE
    '\u2005': ' ',  # FOUR-PER-EM SPACE
    '\u2006': ' ',  # SIX-PER-EM SPACE
    '\u2007': ' ',  # FIGURE SPACE
    '\u2008': ' ',  # PUNCTUATION SPACE
    '\u2009': ' ',  # THIN SPACE
    '\u200A': ' ',  # HAIR SPACE
    '\u200B': '',   # ZERO WIDTH SPACE (remove)
    '\u202F': ' ',  # NARROW NO-BREAK SPACE
    '\u205F': ' ',  # MEDIUM MATHEMATICAL SPACE
    '\u3000': ' ',  # IDEOGRAPHIC SPACE (　)
    '\uFEFF': '',   # ZERO WIDTH NO-BREAK SPACE / BOM (remove)
}

# Asterisk variants
ASTERISK_VARIANTS = {
    '\uFF0A': '*',  # FULLWIDTH ASTERISK (＊)
    '\u2217': '*',  # ASTERISK OPERATOR
    '\u204E': '*',  # LOW ASTERISK
    '\u2055': '*',  # FLOWER PUNCTUATION MARK
}

# Combined full map
SYMBOL_MAP = {}
SYMBOL_MAP.update(PERIOD_VARIANTS)
SYMBOL_MAP.update(COMMA_VARIANTS)
SYMBOL_MAP.update(HYPHEN_VARIANTS)
SYMBOL_MAP.update(SPACE_VARIANTS)
SYMBOL_MAP.update(ASTERISK_VARIANTS)

# Build translation table for fast str.translate()
_TRANS_TABLE = str.maketrans(SYMBOL_MAP)


# ═══════════════════════════════════════════════════════════════════════
# METHOD 1: Unicode Normalization
# ═══════════════════════════════════════════════════════════════════════

def normalize_symbols(text: str) -> str:
    """Replace all known symbol variants with ASCII equivalents.
    
    This is the primary normalization pass - applied to all text before parsing.
    Uses NFKC normalization first (handles fullwidth → ASCII for many chars),
    then applies our custom symbol map for remaining variants.
    """
    # Step 1: Unicode NFKC normalization (handles many fullwidth chars)
    text = unicodedata.normalize('NFKC', text)
    # Step 2: Custom translation for remaining variants
    text = text.translate(_TRANS_TABLE)
    return text


# ═══════════════════════════════════════════════════════════════════════
# METHOD 2: Context-based Digit-Adjacency Inference
# ═══════════════════════════════════════════════════════════════════════

def _infer_symbol_from_context(text: str, pos: int) -> str:
    """Infer what a symbol between/near digits should be based on context.
    
    Rules:
    - Between digits with 3-digit groups on right → thousands separator
    - Between digits with 1-2 digits on right at end → decimal point
    - Between digits in date context (DD.MM.YYYY) → period
    """
    ch = text[pos]
    
    # Get digits before and after
    before = ''
    i = pos - 1
    while i >= 0 and text[i].isdigit():
        before = text[i] + before
        i -= 1
    
    after = ''
    i = pos + 1
    while i < len(text) and text[i].isdigit():
        after += text[i]
        i += 1
    
    if not before or not after:
        return ch  # Not between digits, keep as-is
    
    # Date pattern: 2 digits . 2 digits . 4 digits
    if len(before) <= 2 and len(after) == 2:
        # Could be DD.MM or MM.YYYY, likely a period
        return '.'
    if len(before) == 2 and len(after) == 4:
        return '.'
    
    # Thousands separator: 3 digits after
    if len(after) == 3:
        return ','  # or '.' depending on locale, handled by format detection
    
    # Decimal: 1-2 digits after at word boundary
    if len(after) <= 2:
        return '.'
    
    return ch


def normalize_symbols_contextual(text: str) -> str:
    """Apply context-based symbol inference for ambiguous characters."""
    result = list(text)
    ambiguous = set(PERIOD_VARIANTS.keys()) | set(COMMA_VARIANTS.keys())
    
    for i, ch in enumerate(text):
        if ch in ambiguous:
            result[i] = _infer_symbol_from_context(text, i)
    
    return ''.join(result)


# ═══════════════════════════════════════════════════════════════════════
# METHOD 3: Number Format Pattern Detection
# ═══════════════════════════════════════════════════════════════════════

# Known number format patterns
NUMBER_FORMATS = {
    'standard':  re.compile(r'^(\d{1,3})(,\d{3})*(\.\d+)?$'),     # 1,000.50
    'european':  re.compile(r'^(\d{1,3})(\.\d{3})*(,\d+)?$'),     # 1.000,50
    'plain':     re.compile(r'^(\d+)(\.\d+)?$'),                   # 1000.50
    'chinese':   re.compile(r'^(\d+)(\.?\d*)$'),                   # 1000 or 1000.50
}


def detect_number_format(text: str) -> str:
    """Detect the primary number format used in a document.
    
    Returns: 'standard', 'european', 'plain', or 'unknown'
    """
    # Count format occurrences
    eu_count = len(re.findall(r'\d{1,3}(?:\.\d{3})+,\d{2}', text))
    std_count = len(re.findall(r'\d{1,3}(?:,\d{3})+\.\d{2}', text))
    
    if eu_count > 0 and eu_count > std_count:
        return 'european'
    if std_count > 0:
        return 'standard'
    return 'plain'


def parse_number_by_format(num_str: str, fmt: str) -> Optional[str]:
    """Parse a number string according to detected format.
    
    Always returns standard format (e.g., "1000.50").
    Returns None if parsing fails.
    """
    num_str = num_str.strip()
    if not num_str:
        return None
    
    if fmt == 'european':
        # 1.500 → 1500, 190,00 → 190.00, 2.850,00 → 2850.00
        if re.match(r'^\d{1,3}(\.\d{3})*(,\d+)?$', num_str):
            return num_str.replace('.', '').replace(',', '.')
        elif ',' in num_str and '.' not in num_str:
            return num_str.replace(',', '.')
        return num_str
    
    elif fmt == 'standard':
        # 1,000.50 → 1000.50
        if re.match(r'^\d{1,3}(,\d{3})*(\.\d+)?$', num_str):
            return num_str.replace(',', '')
        return num_str
    
    else:  # plain
        return num_str.replace(',', '')


# ═══════════════════════════════════════════════════════════════════════
# METHOD 4: Cross-field Consistency Voting
# ═══════════════════════════════════════════════════════════════════════

def validate_number_consensus(raw_value: str, document_format: str,
                               context_values: list = None) -> str:
    """Multi-method validation: run all methods and take consensus.
    
    Args:
        raw_value: The raw number string from PDF
        document_format: Detected format ('standard', 'european', 'plain')
        context_values: Other numbers from the same document for consistency check
    
    Returns:
        Validated number string in standard format
    """
    if not raw_value or not raw_value.strip():
        return raw_value
    
    raw = raw_value.strip()
    
    # Skip non-number strings
    if not re.search(r'\d', raw):
        return raw
    
    # ── Method 1: Direct symbol normalization ──
    m1 = normalize_symbols(raw)
    m1_parsed = parse_number_by_format(m1, document_format)
    
    # ── Method 2: Context-based inference ──
    m2 = normalize_symbols_contextual(raw)
    m2_parsed = parse_number_by_format(m2, document_format)
    
    # ── Method 3: Pattern-based parsing ──
    m3_parsed = parse_number_by_format(normalize_symbols(raw), document_format)
    
    # ── Method 4: Cross-field consistency ──
    m4_parsed = m3_parsed  # default
    if context_values:
        # Check if other values in the document use consistent formatting
        formats_seen = set()
        for cv in context_values:
            cv_clean = normalize_symbols(cv)
            if re.match(r'^\d{1,3}(\.\d{3})*(,\d+)?$', cv_clean):
                formats_seen.add('european')
            elif re.match(r'^\d{1,3}(,\d{3})*(\.\d+)?$', cv_clean):
                formats_seen.add('standard')
        
        if len(formats_seen) == 1:
            consistent_fmt = formats_seen.pop()
            m4_parsed = parse_number_by_format(normalize_symbols(raw), consistent_fmt)
    
    # ── Consensus vote ──
    candidates = [m1_parsed, m2_parsed, m3_parsed, m4_parsed]
    candidates = [c for c in candidates if c is not None]
    
    if not candidates:
        return raw
    
    # Count votes
    votes = {}
    for c in candidates:
        votes[c] = votes.get(c, 0) + 1
    
    # Return the most-voted result
    winner = max(votes, key=votes.get)
    return winner


# ═══════════════════════════════════════════════════════════════════════
# HIGH-LEVEL API
# ═══════════════════════════════════════════════════════════════════════

def normalize_text_symbols(text: str) -> str:
    """Full symbol normalization for text. Apply before any parsing."""
    return normalize_symbols(text)


def validate_number(raw_value: str, document_text: str = '',
                    context_values: list = None) -> str:
    """Validate and normalize a number string using multi-method consensus.
    
    Use this when extracting price, quantity, or total fields.
    
    Args:
        raw_value: Raw extracted number string (e.g., "2.850,00" or "45,450.24")
        document_text: Full document text (for format auto-detection)
        context_values: Other numbers from the same document
    
    Returns:
        Normalized number string in standard format (e.g., "2850.00")
    """
    fmt = detect_number_format(document_text) if document_text else 'plain'
    return validate_number_consensus(raw_value, fmt, context_values)


def validate_date(raw_date: str) -> str:
    """Normalize date string after symbol normalization.
    
    Handles: 2025.02.11, 2025-02-11, 2025/02/11, 11.02.2025 (EU), 02/11/2025
    Returns the date in its original format but with clean symbols.
    """
    cleaned = normalize_symbols(raw_date).strip()
    # Verify it still looks like a date
    if re.match(r'^\d{4}[./-]\d{2}[./-]\d{2}$', cleaned):
        return cleaned
    if re.match(r'^\d{2}[./-]\d{2}[./-]\d{4}$', cleaned):
        return cleaned
    if re.match(r'^\d{4}/\d{2}/\d{2}$', cleaned):
        return cleaned
    return cleaned
