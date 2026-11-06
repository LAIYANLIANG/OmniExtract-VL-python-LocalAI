"""BYD PO Extractor.

BYD PO PDF raw text pattern (from pdfplumber):
    Header per page:
        供应商名称/SUPPLIER: [Supplier Name]... 订购日期/Date: 2025.02.11
        联系人/ATTN: [Contact Name] 订购单号/Order No: 3100544305
        电话/TEL: 075588319800 供应商编号/SUPPLIER NO.： 20011726
        币种/CURRENCY: USD
    Line items:
        10 13427633-00 NOR FLASH_IS25LP512M-RMLA3_512Mbit_-40°C PCS 880 2.69 0% 2,367.2
        /[Brand] SWJ0 0033 按要求 2025.06.01
    Footer (last page):
        未税金额合计/TOTAL AMOUNT WITHOUT TAX: 18,690
        贸易条件 COMMERCE TERM：DAPHK
        付款方式 PAYMENT TERMS： 供应商发票日起30天付款
"""
import re
from typing import List
from .base import BaseExtractor
from .registry import ExtractorRegistry
from ..models.po_model import (
    PurchaseOrder, PurchaseInfo, VendorInfo, AddressInfo, LineItem, ScheduleLine
)
from ..pipeline.symbol_validator import validate_number, validate_date


@ExtractorRegistry.register("byd")
class BYDExtractor(BaseExtractor):

    def extract(self, raw_text: str, pages: List[str]) -> PurchaseOrder:
        po = PurchaseOrder(vendor_id="byd")
        self._extract_header(raw_text, po)
        self._extract_vendor(raw_text, po)
        self._extract_addresses(raw_text, po)
        self._extract_line_items(raw_text, po)
        self.apply_learned(po, raw_text)
        return po

    def _extract_header(self, text: str, po: PurchaseOrder):
        info = po.purchase_info

        # PO Number: 订购单号/Order No: 3100544305
        m = re.search(r'(?:订购单号|Order\s*No)[.:：\s]*(\d{10})', text)
        if m:
            info.po_number = m.group(1)

        # Date: 订购日期/Date: 2025.02.11  or  2025/10/22
        m = re.search(r'(?:订购日期(?:/Date)?|Date)[.:：\s]*([\d./]+)', text)
        if m:
            info.date = m.group(1)

        # Buyer
        info.buyer = 'BYD (H.K.) CO., LIMITED'

        # Contact: 联系人/ATTN: 包蕾
        m = re.search(r'(?:联系人|ATTN)[.:：/\s]*(.+?)\s*(?:订购单号|Order\s*No)', text)
        if m:
            info.contact = m.group(1).strip()

        # Currency: 币种/CURRENCY: USD
        m = re.search(r'(?:币种|CURRENCY)[.:：\s]*(USD|CNY|EUR|RMB)', text, re.IGNORECASE)
        if m:
            info.currency = m.group(1).upper()

        # Payment terms from footer
        m = re.search(r'(?:付款方式|PAYMENT\s*TERMS)[.:：\s]*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if m:
            info.payment_terms = m.group(1).strip()

        # Trade terms from footer: 贸易条件 COMMERCE TERM：DAPHK
        m = re.search(r'(?:贸易条件|COMMERCE\s*TERM)[.:：\s]*(\S+)', text, re.IGNORECASE)
        if m:
            info.trade_terms = m.group(1)

        # Total: 未税金额合计/TOTAL AMOUNT WITHOUT TAX: 18,690
        m = re.search(r'(?:未税金额合计|TOTAL\s*AMOUNT\s*WITHOUT\s*TAX)[.:：\s]*([\d,]+\.?\d*)', text, re.IGNORECASE)
        if m:
            info.total_amount = m.group(1)

    def _extract_vendor(self, text: str, po: PurchaseOrder):
        v = po.vendor_info

        # Supplier No: 供应商编号/SUPPLIER NO.： 20011726
        m = re.search(r'(?:供应商编号|SUPPLIER\s*NO)[.：:\s]*(\d+)', text)
        if m:
            v.vendor_code = m.group(1)

        # Supplier name: 供应商名称/SUPPLIER: [Supplier Name]...
        m = re.search(r'(?:供应商名称|SUPPLIER)[.:：\s]*(.+?)(?:\s*订购日期|\s*Date)', text, re.IGNORECASE)
        if m:
            v.name = m.group(1).strip()

        # Phone: 电话/TEL: 075588319800
        m = re.search(r'(?:电话|TEL)[.:：\s]*([\d]+)', text)
        if m:
            v.phone = m.group(1)

    def _extract_addresses(self, text: str, po: PurchaseOrder):
        bill = po.bill_to
        bill.company_name = 'BYD (H.K.) CO., LIMITED'

        # Address: Flat/RM: ...
        m = re.search(r'Flat/RM[.:：\s]*(.+?)(?:\n\s*TEL)', text, re.DOTALL)
        if m:
            bill.address = re.sub(r'\s+', ' ', m.group(1)).strip()

        # Phone
        m = re.search(r'TEL[.:：\s]*([\d\s\-]+)', text)
        if m:
            bill.phone = m.group(1).strip()

        # Fax
        m = re.search(r'FAX[.:：\s]*(\([^)]+\)\s*[\d\s]+)', text)
        if m:
            bill.fax = m.group(1).strip()

        # Ship-to: 交货地点 delivery contact
        ship = po.ship_to
        # Delivery contact
        m = re.search(r'(?:交货地点|PLACE\s*OF\s*DELIVERY)', text, re.IGNORECASE)
        if m:
            after = text[m.end():m.end() + 300]
            cm = re.search(r'联系人[：:]\s*(.+?)(?:联系电话|电话)', after)
            if cm:
                ship.contact = cm.group(1).strip()
            pm = re.search(r'(?:联系电话|电话)[：:]\s*(\d+)', after)
            if pm:
                ship.phone = pm.group(1)

    def _extract_line_items(self, text: str, po: PurchaseOrder):
        """Parse BYD line items.

        Pattern per item spans 2 lines:
            10 13427633-00 NOR FLASH_IS25LP512M-RMLA3_512Mbit_-40°C PCS 880 2.69 0% 2,367.2
            /[Brand] SWJ0 0033 按要求 2025.06.01
        """
        # Match: item_no  part_no  description  unit  qty  price  tax%  total
        # Then next line has: /brand factory storage quality delivery_date
        pattern = re.compile(
            r'^(\d{2,3})\s+'           # item no (10, 20, ..., 100, 110...)
            r'(\d{8}-\d{2})\s+'        # part no (13427633-00)
            r'(.+?)\s+'               # description
            r'(PCS|EA|ST)\s+'          # unit
            r'([\d,]+)\s+'            # quantity
            r'([\d.]+)\s+'            # unit price
            r'(\d+%)\s+'              # tax rate
            r'([\d,.]+)',             # total price
            re.MULTILINE
        )

        date_pattern = re.compile(r'(\d{4}\.\d{2}\.\d{2})')

        for m in pattern.finditer(text):
            item = LineItem(
                item_no=m.group(1),
                product_code=m.group(2),
                description=m.group(3).strip(),
                unit=m.group(4),
                quantity=validate_number(m.group(5), text),
                unit_price=validate_number(m.group(6), text),
                net_price=validate_number(m.group(8), text),
            )

            # Look for delivery date in the next ~200 chars after the match
            after = text[m.end():m.end() + 200]
            # Look for supplier material on continuation line: /[Brand] ...
            sm = re.search(r'/([\w\u4e00-\u9fff]+)', after)
            if sm:
                item.supplier_material = sm.group(1)

            dm = date_pattern.search(after)
            if dm:
                item.schedule_lines.append(ScheduleLine(
                    delivery_date=validate_date(dm.group(1)),
                    quantity=item.quantity,
                ))

            po.line_items.append(item)
