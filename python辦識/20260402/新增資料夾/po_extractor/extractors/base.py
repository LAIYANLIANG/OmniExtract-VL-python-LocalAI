"""Base extractor abstract class."""
from abc import ABC, abstractmethod
from ..models.po_model import PurchaseOrder
from ..pipeline.pattern_applier import apply_learned_patterns
from typing import List


class BaseExtractor(ABC):
    """Abstract base class for all vendor-specific PO extractors."""

    @abstractmethod
    def extract(self, raw_text: str, pages: List[str]) -> PurchaseOrder:
        """
        Parse raw text into a structured PurchaseOrder.

        Args:
            raw_text: Full cleaned text of the PDF.
            pages: List of per-page text strings.

        Returns:
            PurchaseOrder dataclass instance.
        """
        ...

    def apply_learned(self, po: PurchaseOrder, raw_text: str) -> int:
        """Apply learned patterns to fill empty fields.

        Call this AFTER your built-in extraction to supplement
        with patterns learned from human corrections.
        Returns the number of fields filled.
        """
        return apply_learned_patterns(po, po.vendor_id, raw_text)
