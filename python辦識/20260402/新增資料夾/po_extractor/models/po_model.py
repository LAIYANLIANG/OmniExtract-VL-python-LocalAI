"""Unified PO data model."""
from dataclasses import dataclass, field, asdict, fields
from typing import List, Optional
import json


def _normalize_all_strings(obj):
    """Recursively normalize all string fields in a dataclass using symbol validator."""
    from po_extractor.pipeline.symbol_validator import normalize_text_symbols, validate_date
    import re

    for f in fields(obj):
        val = getattr(obj, f.name)
        if isinstance(val, str) and val:
            # Normalize all variant symbols to ASCII
            cleaned = normalize_text_symbols(val)
            setattr(obj, f.name, cleaned)
        elif isinstance(val, list):
            for item in val:
                if hasattr(item, '__dataclass_fields__'):
                    _normalize_all_strings(item)
        elif hasattr(val, '__dataclass_fields__'):
            _normalize_all_strings(val)


@dataclass
class ScheduleLine:
    """Delivery schedule line."""
    schedule_no: str = ""
    delivery_date: str = ""
    quantity: str = ""


@dataclass
class LineItem:
    """PO line item."""
    item_no: str = ""
    product_code: str = ""
    description: str = ""
    quantity: str = ""
    unit: str = ""
    unit_price: str = ""
    price_unit: str = ""
    net_price: str = ""
    supplier_material: str = ""
    schedule_lines: List[ScheduleLine] = field(default_factory=list)


@dataclass
class AddressInfo:
    """Address block (bill-to / ship-to)."""
    company_name: str = ""
    address: str = ""
    contact: str = ""
    phone: str = ""
    fax: str = ""
    email: str = ""


@dataclass
class VendorInfo:
    """Supplier information."""
    vendor_code: str = ""
    name: str = ""
    address: str = ""
    country: str = ""
    contact: str = ""
    phone: str = ""
    fax: str = ""
    email: str = ""


@dataclass
class PurchaseInfo:
    """Purchase order header."""
    po_number: str = ""
    date: str = ""
    buyer: str = ""
    contact: str = ""
    payment_terms: str = ""
    currency: str = ""
    trade_terms: str = ""
    total_amount: str = ""


@dataclass
class PurchaseOrder:
    """Top-level PO model - unified output format."""
    vendor_id: str = ""
    purchase_info: PurchaseInfo = field(default_factory=PurchaseInfo)
    vendor_info: VendorInfo = field(default_factory=VendorInfo)
    bill_to: AddressInfo = field(default_factory=AddressInfo)
    ship_to: AddressInfo = field(default_factory=AddressInfo)
    line_items: List[LineItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        # Apply full-text symbol normalization to ALL string fields before output
        _normalize_all_strings(self)
        return asdict(self)

    def to_json(self, ensure_ascii=False, indent=2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii, indent=indent)
