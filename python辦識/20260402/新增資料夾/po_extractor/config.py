"""Global configuration."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.normpath(os.path.join(BASE_DIR, ".."))

# Default input / output directories
DEFAULT_INPUT_DIR = os.path.join(WORKSPACE_DIR, "import_doc")
DEFAULT_OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "output_doc")
DEFAULT_FINISH_DIR = os.path.join(WORKSPACE_DIR, "import_doc", "finish")
DEFAULT_CORRECTED_DIR = os.path.join(WORKSPACE_DIR, "corrected")
LEARNED_PATTERNS_PATH = os.path.join(WORKSPACE_DIR, "learned_patterns.json")

# Auto-generate extractor threshold: how many corrected samples needed
AUTO_EXTRACTOR_THRESHOLD = 3

LOG_LEVEL = "INFO"

# pdfplumber text length threshold: below this = image-based PDF
IMAGE_PDF_TEXT_THRESHOLD = 50

# Vendor display name mapping (vendor_id -> folder name)
# Used to create output subfolders per vendor
VENDOR_FOLDER_MAP = {
    "byd": "BYD",
    "kaifa": "Kaifa",
    "siemens": "SIEMENS",
    "desay_sv": "DESAY_SV",
    # New vendors will auto-generate folder names from vendor_id
}
