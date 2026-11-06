"""DESAY SV (德赛西威) PO Extractor.

Raw text pattern (from pdfplumber):
    Header:
        订单号: 3600217031
        日期: 2025-12-2500:00:00
        联系人: 李欢
        电子邮件: huan.li2@desaysv.com
        供应商代码: 3341
        付款方式: N90
        货币： USD
        贸易条款: FOB HK

    Line items:
        00010 90700000014A IS25LP080D- 10000.00 140.00 1400.00
                         JULA3-TR
        NOR IS25LP080D- ST 1000 0%
        JULA3-TR USON
        2x3mm8Mbit
        计划行号 计划行： 计划交货日期 计划数量
        0001 90700000014A 2026-03-23 5000.00 ST
        0002 90700000014A 2026-03-24 5000.00 ST

    Footer:
        未税金额：26490.00
"""
import re
from typing import List
from .base import BaseExtractor
from .registry import ExtractorRegistry
from ..models.po_model import (
    PurchaseOrder, PurchaseInfo, VendorInfo, AddressInfo, LineItem, ScheduleLine
)
from ..pipeline.symbol_validator import validate_number, validate_date


@ExtractorRegistry.register("desay_sv")
class DesaySVExtractor(BaseExtractor):

    def extract(self, raw_text: str, pages: List[str]) -> PurchaseOrder:
        po = PurchaseOrder(vendor_id="desay_sv")
        self._extract_header(raw_text, po)
        self._extract_vendor(raw_text, po)
        self._extract_addresses(raw_text, po)
        self._extract_line_items(raw_text, po)
        self.apply_learned(po, raw_text)
        return po

    def _extract_header(self, text: str, po: PurchaseOrder):
        info = po.purchase_info

        # 订单号: 3600217031
        m = re.search(r'订单号[:\s：]*(\d{10})', text)
        if m:
            info.po_number = m.group(1)

        # 日期: 2025-12-2500:00:00  (note: no space before time)
        m = re.search(r'日期[:\s：]*([\d-]+?)(?:\d{2}:\d{2}:\d{2}|$|\s)', text)
        if m:
            info.date = m.group(1).strip()

        # 联系人: 李欢
        m = re.search(r'联系人[:\s：]*(\S+)', text)
        if m:
            info.contact = m.group(1)

        # 付款方式: N90
        m = re.search(r'付款方式[:\s：]*(\S+)', text)
        if m:
            info.payment_terms = m.group(1)

        # 货币: USD
        m = re.search(r'货币[：:\s]*(USD|CNY|EUR|RMB)', text, re.IGNORECASE)
        if m:
            info.currency = m.group(1).upper()

        # 贸易条款: FOB HK
        m = re.search(r'贸易条款[:\s：]*(FOB\s*\S+|DAP\s*\S+)', text, re.IGNORECASE)
        if m:
            info.trade_terms = m.group(1).strip()

        # Buyer
        if '德赛西威' in text:
            info.buyer = '惠州市德赛西威汽车电子股份有限公司'

        # 未税金额：26490.00
        m = re.search(r'未税金额[：:\s]*([\d,.]+)', text)
        if m:
            info.total_amount = m.group(1)

    def _extract_vendor(self, text: str, po: PurchaseOrder):
        v = po.vendor_info

        # 供应商代码: 3341
        m = re.search(r'供应商代码[:\s：]*(\d+)', text)
        if m:
            v.vendor_code = m.group(1)

        # 名称
        m = re.search(r'名称[：:\s]*(INTEGRATED\s*SILICON\s*SOLUTION[^\n]*)', text, re.IGNORECASE)
        if m:
            v.name = re.sub(r'\s+', ' ', m.group(1)).strip()
        else:
            v.name = 'INTEGRATED SILICON SOLUTION (CAYMAN), INC'

        # 地址
        m = re.search(r'地址[：:\s]*(PO\s*BOX[^\n]+)', text, re.IGNORECASE)
        if m:
            v.address = m.group(1).strip()

        # 国家
        m = re.search(r'国家[：:\s]*(\S+)', text)
        if m:
            v.country = m.group(1)

        # Email
        m = re.search(r'电子邮件[:\s：]*(\S+@\S+)', text)
        if m:
            v.email = m.group(1)

    def _extract_addresses(self, text: str, po: PurchaseOrder):
        bill = po.bill_to
        # 开票至 section
        m = re.search(r'开票至\s*\n?\s*(惠州市德赛西威[^\n]*)', text)
        if m:
            bill.company_name = m.group(1).strip()
        elif '德赛西威' in text:
            bill.company_name = '惠州市德赛西威汽车电子股份有限公司'

        # Bill-to address: various formats
        m = re.search(r'((?:\d+,\s*)?Hechang[^\n]+(?:China|Huizhou)[^\n]*)', text, re.IGNORECASE)
        if not m:
            m = re.search(r'(No\.\s*\d+.*?Huizhou[^\n]*)', text, re.IGNORECASE)
        if not m:
            # Try Chinese address: 惠州市...
            m = re.search(r'(惠州市[^\n]{5,})', text)
        if m:
            bill.address = m.group(1).strip()

        # Ship to
        ship = po.ship_to
        ship.company_name = bill.company_name

        # Ship-to contact: Attention:Ms.Wang or Attention: xxx
        m = re.search(r'Attention\s*[:\s]*(\S+)', text)
        if m:
            ship.contact = m.group(1)

        # Ship-to phone: Telephone:(852)24827617
        m = re.search(r'Telephone\s*[:\s]*(\(?[\d)]+[\d\s()-]+)', text)
        if m:
            ship.phone = m.group(1).strip()

        # Ship-to fax: FaxNumber:(852)24710474
        m = re.search(r'FaxNumber\s*[:\s]*(\(?[\d)]+[\d\s()-]+)', text)
        if m:
            ship.fax = m.group(1).strip()

        # Ship-to address from delivery section
        m = re.search(r'(Room\s+\d+.*?(?:HONG\s*KONG|Hong\s*Kong))', text, re.DOTALL | re.IGNORECASE)
        if m:
            ship.address = re.sub(r'\s+', ' ', m.group(1)).strip()

    def _extract_line_items(self, text: str, po: PurchaseOrder):
        """Parse DESAY SV line items.

        Each item block starts with 5-digit item number:
            00010 90700000014A IS25LP080D- 10000.00 140.00 1400.00
        Followed by description lines, then schedule lines:
            0001 90700000014A 2026-03-23 5000.00 ST
        """
        # Find all item start positions
        item_pattern = re.compile(
            r'^(\d{5})\s+'                   # item no
            r'(\d{10,11}[A-Z]?)\s+'         # product code (90700000014A)
            r'(\S+)\s+'                      # supplier material (start, may wrap)
            r'([\d.]+)\s+'                  # quantity
            r'([\d.]+)\s+'                  # unit price
            r'([\d.]+)',                    # net price
            re.MULTILINE
        )

        item_matches = list(item_pattern.finditer(text))

        for idx, m in enumerate(item_matches):
            # Get block for this item
            start = m.start()
            end = item_matches[idx + 1].start() if idx + 1 < len(item_matches) else len(text)
            block = text[start:end]

            item = LineItem(
                item_no=m.group(1),
                product_code=m.group(2),
                supplier_material=m.group(3),
                quantity=validate_number(m.group(4), text),
                unit_price=validate_number(m.group(5), text),
                net_price=validate_number(m.group(6), text),
            )

            # Get unit: ST after quantity or in description area
            um = re.search(r'\bST\b', block)
            if um:
                item.unit = 'ST'

            # Price unit: 1000 after ST
            pu = re.search(r'ST\s+(\d+)', block)
            if pu:
                item.price_unit = f"/{pu.group(1)}"

            # Build description from lines between item header and schedule
            desc_lines = []
            for line in block.split('\n')[1:]:
                line = line.strip()
                if not line:
                    continue
                if re.match(r'^\d{4}\s+\d{10}', line):
                    break  # schedule line
                if '计划行号' in line or '计划行：' in line:
                    continue
                desc_lines.append(line)
            if desc_lines:
                # First few lines are description, stop at "ST" unit line
                desc_parts = []
                for dl in desc_lines:
                    if re.match(r'^(NOR|DDR|SDRAM|SRAM|eMMC|LPDDR)', dl):
                        desc_parts.append(dl)
                    elif desc_parts:
                        desc_parts.append(dl)
                item.description = ' '.join(desc_parts).strip() if desc_parts else ''

            # Extract schedule lines: 0001 90700000014A 2026-03-23 5000.00 ST
            sched_pattern = re.compile(
                r'^(\d{4})\s+'              # schedule no
                r'\S+\s+'                   # product code (repeated)
                r'(\d{4}-\d{2}-\d{2})\s+'  # delivery date
                r'([\d.]+)\s*ST',          # quantity
                re.MULTILINE
            )
            for sm in sched_pattern.finditer(block):
                item.schedule_lines.append(ScheduleLine(
                    schedule_no=sm.group(1),
                    delivery_date=validate_date(sm.group(2)),
                    quantity=validate_number(sm.group(3), text),
                ))

            po.line_items.append(item)
