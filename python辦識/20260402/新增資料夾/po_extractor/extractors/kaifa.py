"""Kaifa Technology PO Extractor.

Two sub-formats observed:

Format A (KFML - Malaysia):
    PO Number 4501027279
    Date 2025/09/12
    Item PN / Description Quantity UM Net Price Net Amount
    00010 100819801 399,999 EA 1,685.00 67,399.83
                                         PER/10,000
    IC;ASSY...
    schedule:
    2025/12/19 399,999 EA

Format B (KFSU - Suzhou):
    PO Number: 4501032812
    Date 10/09/2025
    Item KaifaPartNo./Description Quantity UM Net Price Net Amount
    0010 EDS13-00000852 1,500 EA 19,500.00 2,925.00
                                          HK10
    IC;IC 1Mx16 SRAM...                   per /10,000
    Total excl. Tax 2,925.00
"""
import re
from typing import List
from .base import BaseExtractor
from .registry import ExtractorRegistry
from ..models.po_model import (
    PurchaseOrder, PurchaseInfo, VendorInfo, AddressInfo, LineItem, ScheduleLine
)
from ..pipeline.symbol_validator import validate_number, validate_date


@ExtractorRegistry.register("kaifa")
class KaifaExtractor(BaseExtractor):

    def extract(self, raw_text: str, pages: List[str]) -> PurchaseOrder:
        po = PurchaseOrder(vendor_id="kaifa")
        self._extract_header(raw_text, po)
        self._extract_vendor(raw_text, po)
        self._extract_addresses(raw_text, po)
        self._extract_line_items(raw_text, po)
        self.apply_learned(po, raw_text)
        return po

    def _extract_header(self, text: str, po: PurchaseOrder):
        info = po.purchase_info

        # PO Number: 4501032812 or PO Number 4501027279
        m = re.search(r'PO\s*Number[:\s]*(\d{10})', text)
        if m:
            info.po_number = m.group(1)

        # Date: 2025/09/12 or 10/09/2025
        m = re.search(r'Date\s+(\d{1,4}[/]\d{1,2}[/]\d{2,4})', text)
        if m:
            info.date = m.group(1)

        # Buyer: KAIFA TECHNOLOGY (H.K.) LTD. or Kaifa Technology (H.K) Ltd
        m = re.search(r'((?:KAIFA|Kaifa)\s+TECHNOLOGY\s+\(H\.?\s*K\.?\)\.?\s*LTD\.?)', text, re.IGNORECASE)
        if m:
            info.buyer = m.group(1).strip()

        # Payment Term: Net 060 Days from Invoice
        m = re.search(r'Payment\s*Term[s]?\s+(Net\s+\d+\s+Days[^\n]*)', text, re.IGNORECASE)
        if m:
            info.payment_terms = m.group(1).strip()

        # Currency
        m = re.search(r'Currency[:\s]*(USD|EUR|CNY)', text, re.IGNORECASE)
        if m:
            info.currency = m.group(1).upper()
        elif 'USD' in text:
            info.currency = 'USD'

        # Incoterms: DAP KFML or DAP KFSU
        m = re.search(r'(?:INCOTERMS|Incoterms)\s+(DAP\s+\w+|FOB\s+\w+)', text, re.IGNORECASE)
        if m:
            info.trade_terms = m.group(1).strip()

        # Total: Total excl. Tax 2,925.00  or  Total excl. Tax: 8,195,706.84
        m = re.search(r'Total\s+excl\.?\s*Tax[:\s]+([\d,]+\.?\d*)', text, re.IGNORECASE)
        if m:
            info.total_amount = m.group(1)

        # Buyer/Phone: Jacelyn Lau or Wei Shi / 68345
        m = re.search(r'Buyer/Phone\s+(.+?)(?:\n|$)', text)
        if m:
            raw = m.group(1).strip()
            # Format: 施伟Wei Shi / 68345 or Jacelyn Lau
            pm = re.search(r'([\u4e00-\u9fff]+)?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)\s*/\s*(\d+)', raw)
            if pm:
                info.contact = (pm.group(1) or '') + pm.group(2)
                info.contact = info.contact.strip()
                info.phone = pm.group(3)
            else:
                pm2 = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+)', raw)
                if pm2:
                    info.contact = pm2.group(1)

        # Company phone: Phone: (852) 2425 8505
        m = re.search(r'Phone[:\s]+(\([\d]+\)[\d\s]+)', text)
        if m:
            bill_phone = re.sub(r'\s+', ' ', m.group(1)).strip()
            po.bill_to.phone = bill_phone

    def _extract_vendor(self, text: str, po: PurchaseOrder):
        v = po.vendor_info

        # Vendor No.: 24023 or Vendor No. / Currency:24023 USD
        m = re.search(r'Vendor\s*No\.?\s*(?:/\s*Currency)?[:\s]*(\d+)', text, re.IGNORECASE)
        if m:
            v.vendor_code = m.group(1)

        # Vendor Name: extract from text or fallback to generic
        vm = re.search(r'Vendor\s*(?:Name)?[:\s]+([^\n]+)', text, re.IGNORECASE)
        v.name = vm.group(1).strip() if vm else 'Supplier'

        # Vendor Fax
        m = re.search(r'Vendor\s*Fax[\uff1a:\s]*([\d\-+()\s]+)', text, re.IGNORECASE)
        if m:
            v.fax = m.group(1).strip()

        # Currency from Vendor No. / Currency:24023 USD
        if not po.purchase_info.currency:
            m = re.search(r'Currency[:\s]*\d+\s+(USD|EUR|CNY)', text, re.IGNORECASE)
            if m:
                po.purchase_info.currency = m.group(1).upper()

    def _extract_addresses(self, text: str, po: PurchaseOrder):
        bill = po.bill_to
        m = re.search(r'((?:KAIFA|Kaifa)\s+TECHNOLOGY\s+\(H\.?\s*K\.?\)\.?\s*LTD\.?)', text, re.IGNORECASE)
        if m:
            bill.company_name = m.group(1).strip()

        # Bill-to address
        m = re.search(r'(?:2201\s+.+?HONG\s+KONG)', text, re.DOTALL | re.IGNORECASE)
        if m:
            bill.address = re.sub(r'\s+', ' ', m.group(0)).strip()

        # Ship To
        ship = po.ship_to
        m = re.search(r'Ship\s*To:\s*\n(.+?)(?=\n\s*(?:Item|CHINA|MALAYSIA)\s*\n)', text, re.DOTALL | re.IGNORECASE)
        if m:
            lines = [l.strip() for l in m.group(1).split('\n') if l.strip()]
            if lines:
                ship.company_name = lines[0]
                ship.address = ' '.join(lines[1:]) if len(lines) > 1 else ''

        # Also try the explicit ship-to patterns
        if not ship.company_name:
            m = re.search(r'Ship\s*To:\s*\n\s*(.+)', text)
            if m:
                ship.company_name = m.group(1).strip()

    def _extract_line_items(self, text: str, po: PurchaseOrder):
        """Parse Kaifa line items.

        Format A (KFML):
            00010 100819801 399,999 EA 1,685.00 67,399.83
                                                PER/10,000
        Format B (KFSU):
            0010 EDS13-00000852 1,500 EA 19,500.00 2,925.00
                                                   HK10
                                          per /10,000
        """
        # Match item lines: item_no  part_no  quantity  unit  net_price  net_amount
        pattern = re.compile(
            r'^(\d{4,5})\s+'              # item no (0010 or 00010)
            r'(\S+)\s+'                   # part number
            r'([\d,]+)\s+'               # quantity
            r'(EA|PCS|ST)\s+'            # unit
            r'([\d,]+\.\d+)\s+'          # net price (unit price * price_unit)
            r'([\d,]+\.\d+)',            # net amount
            re.MULTILINE
        )

        lines = text.split('\n')
        text_block = text

        for m in pattern.finditer(text_block):
            item = LineItem(
                item_no=m.group(1),
                product_code=m.group(2),
                quantity=validate_number(m.group(3), text),
                unit=m.group(4),
                unit_price=validate_number(m.group(5), text),
                net_price=validate_number(m.group(6), text),
            )

            # Look after match for PER/10,000 or per /10,000
            after = text_block[m.end():m.end() + 500]

            # Price unit
            pm = re.search(r'(?:PER|per)\s*/\s*([\d,]+)', after, re.IGNORECASE)
            if pm:
                item.price_unit = f"PER/{pm.group(1)}"

            # Description: IC;ASSY... or IC;IC 1Mx16...
            dm = re.search(r'(IC[;:].+?)(?:\n(?:MPN|Please|Manufacturer|Requisition|--)|$)', after, re.DOTALL)
            if dm:
                desc = re.sub(r'\s+', ' ', dm.group(1)).strip()
                item.description = desc

            # Delivery schedule: 2025/12/19 399,999 EA
            sched_pattern = re.compile(r'(\d{4}/\d{2}/\d{2})\s+([\d,]+)\s*(EA|PCS|ST)', re.IGNORECASE)
            for sm in sched_pattern.finditer(after):
                item.schedule_lines.append(ScheduleLine(
                    delivery_date=validate_date(sm.group(1)),
                    quantity=validate_number(sm.group(2), text),
                ))
                break  # Usually just one schedule line per item

            po.line_items.append(item)
