"""Siemens PO Extractor.

Raw text pattern (from pdfplumber):
    Header (page 1):
        Purchase order 采购订单
        PO number/date 采购订单号/日期 ... 4511697495 / 24.10.2025
        Your vendor number with us 供应商代码 ... 4000039123
        Salesperson (卖方联系人):Deni Yang

    Line items (page 2+):
        00010 A5E37602377 IC_DDR3L_2Gb_x16_+95°C_FBGA_96 NJB
        1.500 Piece 190,00/100 2.850,00
        ISS IS43TR16128DL-125KBLI-TR
        Deliv. date Day 11.02.2026
        Your material number IS43TR16128DL-125KBLI-TR

    European number format: 1.500 = 1500, 190,00 = 190.00, 2.850,00 = 2850.00
"""
import re
from typing import List
from .base import BaseExtractor
from .registry import ExtractorRegistry
from ..models.po_model import (
    PurchaseOrder, PurchaseInfo, VendorInfo, AddressInfo, LineItem, ScheduleLine
)
from ..pipeline.symbol_validator import validate_number, validate_date


def parse_european_number(s: str) -> str:
    """Convert European number format to standard.
    1.500 -> 1500, 190,00 -> 190.00, 2.850,00 -> 2850.00, 83.979,00 -> 83979.00
    """
    s = s.strip()
    # Pattern: digits with dots as thousands sep and comma as decimal
    if re.match(r'^\d{1,3}(\.\d{3})*(,\d+)?$', s):
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s and '.' not in s:
        # Simple case: 190,00 -> 190.00
        s = s.replace(',', '.')
    return s


@ExtractorRegistry.register("siemens")
class SiemensExtractor(BaseExtractor):

    def extract(self, raw_text: str, pages: List[str]) -> PurchaseOrder:
        po = PurchaseOrder(vendor_id="siemens")
        self._extract_header(raw_text, po)
        self._extract_vendor(raw_text, po)
        self._extract_addresses(raw_text, po)
        self._extract_line_items(raw_text, po)
        self.apply_learned(po, raw_text)
        return po

    def _extract_header(self, text: str, po: PurchaseOrder):
        info = po.purchase_info

        # PO number: 4511697495 / 24.10.2025
        m = re.search(r'(\d{10})\s*/\s*(\d{2}\.\d{2}\.\d{4})', text)
        if m:
            info.po_number = m.group(1)
            info.date = m.group(2)

        # Buyer: Siemens Industrial Automation Products Ltd., Chengdu
        m = re.search(r'(Siemens\s+(?:Industrial\s+Automation\s+Products|Numerical\s+Control)\s+Ltd\.?,\s*\w+)', text)
        if m:
            info.buyer = m.group(1).strip()

        # Contact: Min Zhou/CN DI FA... on line after Contact Person label
        # Skip the company name line, look for Name/CN pattern
        m = re.search(r'(\w+\s+\w+)/CN\s+DI', text)
        if m:
            info.contact = m.group(1).strip()

        # Buyer phone from contact line: (28) 62387326
        m = re.search(r'/CN\s+.+?/\(?(\d+)\)?\s*(\d+)', text)
        if m:
            po.bill_to.phone = f'({m.group(1)}) {m.group(2)}'

        # Payment: 90 days after receipt of invoice, net
        m = re.search(r'(\d+)\s*days?\s+after\s+receipt\s+of\s+invoice[,\s]*net', text, re.IGNORECASE)
        if m:
            info.payment_terms = f"{m.group(1)} days after receipt of invoice, net"

        info.currency = 'USD'

        # Trade terms: DAP Chengdu or FOB Hongkong
        m = re.search(r'(DAP\s+\w+|FOB\s+\w+)', text, re.IGNORECASE)
        if m:
            info.trade_terms = m.group(1)

        # Total: "Total Net Value excl. Tax 总价(不含税) USD 2.700,00"
        m = re.search(r'Total\s+Net\s+Value.*?(?:USD|EUR|CNY)\s*([\d.,]+)', text, re.IGNORECASE)
        if m:
            info.total_amount = parse_european_number(m.group(1))

    def _extract_vendor(self, text: str, po: PurchaseOrder):
        v = po.vendor_info

        # Vendor code: on a line near "供应商代码" label (may have intervening text)
        # Use non-greedy match within 200 chars to avoid catching PO number
        m = re.search(r'(?:供应商代码|vendor\s*number).{0,200}?\n\s*(\d{10})\s*(?:\n|$)', text, re.IGNORECASE | re.DOTALL)
        if m:
            v.vendor_code = m.group(1)

        # Vendor Name: extract from text or fallback to generic
        vm = re.search(r'(?:Vendor|Supplier|卖方|供应商)[:\s]+([^\n]+)', text, re.IGNORECASE)
        v.name = vm.group(1).strip() if vm else 'Supplier'

        # Seller contact: Salesperson (卖方联系人):Deni Yang
        m = re.search(r'(?:卖方联系人|Salesperson)[:\s)]*([\w]+\s+[\w]+)', text)
        if m:
            v.contact = m.group(1).strip()

        # Tel/Fax: 86-027-87509686
        m = re.search(r'Tel/Fax\s*No\s*(?:\(电话/传真\))?\s*[:\s]*(\d[\d\-]+)', text)
        if m:
            v.phone = m.group(1).strip()

        # Fax from footer: Fax: 0086 28 6238 7000
        m = re.search(r'\bFax[:\s]+(0086[\d\s]+)', text)
        if m:
            v.fax = re.sub(r'\s+', ' ', m.group(1)).strip()

    def _extract_addresses(self, text: str, po: PurchaseOrder):
        # Bill to: 西门子(中国)有限公司 GBS P2P CN财务部发票中心
        bill = po.bill_to
        m = re.search(r'(西门子.*?发票中心)', text)
        if m:
            bill.company_name = m.group(1)

        m = re.search(r'(上海市.*?楼)', text)
        if m:
            bill.address = m.group(1)

        m = re.search(r'(gss\.\S+@siemens\.com)', text)
        if m:
            bill.email = m.group(1)

        # Ship to
        ship = po.ship_to
        m = re.search(r'Please\s+deliver\s+to.*?\n.*?Company\s*\n\s*(Siemens.+?)(?:\n)', text, re.DOTALL)
        if m:
            ship.company_name = m.group(1).strip()
        elif po.purchase_info.buyer:
            ship.company_name = po.purchase_info.buyer

        # Ship-to address
        m = re.search(r'(No\.?\s*\d+.*?(?:CHENGDU|Nanjing|CHINA))', text, re.DOTALL | re.IGNORECASE)
        if m:
            ship.address = re.sub(r'\s+', ' ', m.group(1)).strip()

        # Ship-to contact: Your person responsible : Deni Yang
        m = re.search(r'person\s+responsible\s*:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if m:
            ship.contact = m.group(1).strip()

        # Bill-to phone: 电话：4006476777-2-1
        m = re.search(r'电话[:：]\s*(\d[\d\-]+)', text)
        if m and not bill.phone:
            bill.phone = m.group(1).strip()

        # Bill-to fax from footer
        m = re.search(r'传真[:：]\s*(0086[\d\s]+)', text)
        if m:
            bill.fax = re.sub(r'\s+', ' ', m.group(1)).strip()

    def _extract_line_items(self, text: str, po: PurchaseOrder):
        """Parse Siemens line items.

        Pattern:
            00010 A5E37602377 IC_DDR3L_2Gb_x16_+95°C_FBGA_96 NJB
            1.500 Piece 190,00/100 2.850,00
            ISS IS43TR16128DL-125KBLI-TR
            Deliv. date Day 11.02.2026
        """
        # Split text into chunks per item
        # Item lines start with 5-digit number at line start followed by A5E
        item_starts = list(re.finditer(r'^(\d{5})\s+(A5E\d+)\s+(.+)', text, re.MULTILINE))

        for idx, m in enumerate(item_starts):
            # Get text block for this item (until next item or end)
            start = m.start()
            end = item_starts[idx + 1].start() if idx + 1 < len(item_starts) else len(text)
            block = text[start:end]

            item = LineItem(
                item_no=m.group(1),
                product_code=m.group(2),
                description=m.group(3).strip(),
            )

            # Quantity + price line: 1.500 Piece 190,00/100 2.850,00
            qp = re.search(r'([\d.]+)\s+(?:Piece|Stk|St)\s+([\d.,]+)\s*/\s*(\d+)\s+([\d.,]+)', block)
            if qp:
                item.quantity = parse_european_number(qp.group(1))
                item.unit = 'Piece'
                item.unit_price = parse_european_number(qp.group(2))
                item.price_unit = f"/{qp.group(3)}"
                item.net_price = parse_european_number(qp.group(4))

            # Supplier material: ISS IS43TR16128DL-125KBLI-TR
            sm = re.search(r'ISS\s+(\S+)', block)
            if sm:
                item.supplier_material = sm.group(1)

            # Delivery date: Deliv. date Day 11.02.2026
            dm = re.search(r'Deliv\.\s*date\s*(?:Day)?\s*(\d{2}\.\d{2}\.\d{4})', block)
            if dm:
                item.schedule_lines.append(ScheduleLine(
                    delivery_date=validate_date(dm.group(1)),
                    quantity=item.quantity,
                ))

            po.line_items.append(item)
