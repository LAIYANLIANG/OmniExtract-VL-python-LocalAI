"""Extractor factory registry - the heart of the factory pattern."""
from .base import BaseExtractor
from typing import Dict, Type


class ExtractorRegistry:
    """
    Central registry for vendor-specific extractors.

    Usage:
        @ExtractorRegistry.register("byd")
        class BYDExtractor(BaseExtractor):
            def extract(self, raw_text, pages): ...

        # Later:
        extractor = ExtractorRegistry.get_extractor("byd")
        result = extractor.extract(raw_text, pages)
    """
    _registry: Dict[str, Type[BaseExtractor]] = {}

    @classmethod
    def register(cls, vendor_id: str):
        """Decorator to register an extractor class for a vendor_id."""
        def decorator(extractor_class: Type[BaseExtractor]):
            if vendor_id in cls._registry:
                raise ValueError(f"Vendor '{vendor_id}' is already registered.")
            cls._registry[vendor_id] = extractor_class
            return extractor_class
        return decorator

    @classmethod
    def get_extractor(cls, vendor_id: str) -> BaseExtractor:
        """Instantiate and return the extractor for a given vendor_id."""
        if vendor_id not in cls._registry:
            raise KeyError(
                f"No extractor registered for vendor '{vendor_id}'. "
                f"Available: {list(cls._registry.keys())}"
            )
        return cls._registry[vendor_id]()

    @classmethod
    def list_vendors(cls):
        """Return list of registered vendor IDs."""
        return list(cls._registry.keys())
