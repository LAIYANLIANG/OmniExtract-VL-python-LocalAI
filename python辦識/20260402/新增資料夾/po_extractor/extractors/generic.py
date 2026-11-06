"""Generic / Auto-Tune Extractor.

Fallback extractor for unrecognized vendor formats.
Uses broad heuristic regex patterns to extract common PO fields
(PO number, dates, amounts, line items) from any PO PDF.

When a new vendor is encountered:
  1. This extractor attempts best-effort extraction
  2. Raw text is preserved in the output for manual review
  3. User can later create a dedicated extractor for higher accuracy
"""
import re
from typing import List
from .base import BaseExtractor
from .registry import ExtractorRegistry
from ..models.po_model import (
    PurchaseOrder, PurchaseInfo, VendorInfo, AddressInfo, LineItem, ScheduleLine
)
from ..pipeline.symbol_validator import validate_number


@ExtractorRegistry.register("generic")
class GenericExtractor(BaseExtractor):
    """Best-effort extractor using common PO patterns."""

    # Common PO number patterns across vendors
    PO_NUMBER_PATTERNS = [
        r'(?:PO|P\.O\.?|Purchase\s*Order|订单号|订购单号|Order\s*No)[.:：#\s]*(\d{8,12})',
        r'(?:采购订单|采购单)[.:：#\s]*(\d{8,12})',
        r'\b(\d{10})\b',  # fallback: 10-digit number
    ]

    # Common date patterns
    DATE_PATTERNS = [
        r'(\d{4}[-/.]\d{2}[-/.]\d{2})',              # 2025-01-15, 2025.01.15, 2025/01/15
        r'(\d{2}[-/.]\d{2}[-/.]\d{4})',              # 15.01.2025, 15/01/2025
        r'(\d{2}/\d{2}/\d{4})',                      # MM/DD/YYYY
        r'(\w{3,9}\s+\d{1,2},?\s+\d{4})',           # January 15, 2025
    ]

    # Common currency patterns
    CURRENCY_PATTERNS = [
        r'(?:Currency|币种|货币)[.:：\s]*(USD|EUR|CNY|RMB|JPY|GBP|HKD)',
        r'\b(USD|EUR|CNY|RMB)\b',
    ]

    # Common total amount patterns
    TOTAL_PATTERNS = [
        r'(?:Total|合计|总[金价]额|Amount)[^:\n]*[.:：\s]*([\d,]+\.?\d*)',
        r'(?:Net\s*Value|净[金价]额)[^:\n]*[.:：\s]*([\d,]+\.?\d*)',
    ]

    # Generic line item: sequence_no  product_code  description  qty  unit  price  amount
    ITEM_PATTERNS = [
        # Numeric item no + alphanumeric product code + qty + unit + price
        re.compile(
            r'^(\d{1,5})\s+'               # item no
            r'(\S+)\s+'                     # product code
            r'(.+?)\s+'                     # description
            r'([\d,]+\.?\d*)\s+'            # quantity
            r'(PCS|EA|ST|Piece|PC|SET|KG|M|LOT|UNIT)\s+'  # unit
            r'([\d,]+\.?\d*)',              # unit price or amount
            re.MULTILINE | re.IGNORECASE
        ),
        # 5-digit item no (SAP style: 00010, 00020)
        re.compile(
            r'^(\d{5})\s+'
            r'(\S+)\s+'
            r'(.{5,60}?)\s+'
            r'([\d,]+\.?\d*)\s+'
            r'(\w{1,5})\s+'
            r'([\d,]+\.?\d*)',
            re.MULTILINE
        ),
    ]

    def extract(self, raw_text: str, pages: List[str]) -> PurchaseOrder:
        po = PurchaseOrder(vendor_id="generic")
        self._extract_header(raw_text, po)
        self._extract_line_items(raw_text, po)
        self.apply_learned(po, raw_text)
        return po

    def _extract_header(self, text: str, po: PurchaseOrder):
        info = po.purchase_info

        # PO Number - try patterns in priority order
        for pattern in self.PO_NUMBER_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                info.po_number = m.group(1)
                break

        # Date - find the first date near a date keyword, else first date found
        date_with_keyword = None
        date_any = None
        for pattern in self.DATE_PATTERNS:
            if not date_any:
                m = re.search(pattern, text)
                if m:
                    date_any = m.group(1)
            # Also check near date keywords
            kw_pattern = r'(?:Date|日期|Dated)[.:：\s]*' + pattern
            m = re.search(kw_pattern, text, re.IGNORECASE)
            if m and not date_with_keyword:
                date_with_keyword = m.group(1)
        info.date = date_with_keyword or date_any or ""

        # Currency
        for pattern in self.CURRENCY_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                info.currency = m.group(1).upper()
                break

        # Total
        for pattern in self.TOTAL_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                info.total_amount = m.group(1)
                break

        # Buyer - heuristic: look for company names near "buyer", "bill to", "purchaser"
        m = re.search(r'(?:Buyer|买方|采购方|Bill\s*To)[.:：\s]*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if m:
            info.buyer = m.group(1).strip()[:100]

        # Payment terms
        m = re.search(r'(?:Payment\s*Terms?|付款方式|付款条件)[.:：\s]*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if m:
            info.payment_terms = m.group(1).strip()[:100]

        # Trade terms
        m = re.search(r'(?:Incoterms?|Trade\s*Terms?|贸易条[件款])[.:：\s]*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if m:
            info.trade_terms = m.group(1).strip()[:60]

        # Vendor info - heuristic
        v = po.vendor_info
        m = re.search(r'(?:Supplier|Vendor|供应商)[.:：\s]*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if m:
            v.name = m.group(1).strip()[:100]

    def _extract_line_items(self, text: str, po: PurchaseOrder):
        for pattern in self.ITEM_PATTERNS:
            matches = list(pattern.finditer(text))
            if len(matches) >= 1:
                for m in matches:
                    item = LineItem(
                        item_no=m.group(1),
                        product_code=m.group(2),
                        description=m.group(3).strip(),
                        quantity=validate_number(m.group(4), text),
                        unit=m.group(5),
                        unit_price=validate_number(m.group(6), text),
                    )
                    po.line_items.append(item)
                break  # use the first pattern that finds items
