"""
PO PDF Feature Extractor - CLI Entry Point

Usage:
    py -m po_extractor.main                         # scan import_doc/, output to output_doc/<vendor>/
    py -m po_extractor.main --input <path>           # custom input path
    py -m po_extractor.main --output <path>          # custom output root
    py -m po_extractor.main --list-vendors

Default behaviour:
    - Input:  import_doc/  (scans recursively)
    - Output: output_doc/<VendorFolder>/<po_file>.json
    - Finish: import_doc/finish/<VendorFolder>/<processed_pdf>
"""
import argparse
import os
import sys
import json
import logging

# Add the workspace root (parent of po_extractor/) to sys.path
_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_DIR = os.path.dirname(_PACKAGE_DIR)
if _WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, _WORKSPACE_DIR)

from po_extractor.pipeline.step2_extract import extract_text_from_pdf
from po_extractor.pipeline.step3_clean import clean_text_preserve_structure
from po_extractor.pipeline.step4_classify import classify_vendor
from po_extractor.extractors.registry import ExtractorRegistry
# This import triggers all extractors to register themselves
import po_extractor.extractors  # noqa: F401
from po_extractor.config import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR, DEFAULT_FINISH_DIR, VENDOR_FOLDER_MAP
from po_extractor.pipeline.confidence_scorer import score_purchase_order
import shutil


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_vendor_folder(vendor_id: str) -> str:
    """Map vendor_id to output folder name."""
    if vendor_id in VENDOR_FOLDER_MAP:
        return VENDOR_FOLDER_MAP[vendor_id]
    # Auto-generate folder name for new/unknown vendors
    return vendor_id.upper().replace(' ', '_')


def move_to_finish(pdf_path: str, vendor_id: str, finish_root: str):
    """Move processed PDF to finish/<VendorFolder>/."""
    vendor_folder = get_vendor_folder(vendor_id)
    finish_dir = os.path.join(finish_root, vendor_folder)
    os.makedirs(finish_dir, exist_ok=True)
    dest = os.path.join(finish_dir, os.path.basename(pdf_path))
    shutil.move(pdf_path, dest)
    logger.info(f"  Moved to: {os.path.relpath(dest)}")


def process_single_pdf(pdf_path: str, output_root: str, finish_root: str = None) -> dict:
    """Process one PDF file through the full pipeline.

    Output is saved to: output_root/<VendorFolder>/<filename>.json
    Processed PDF is moved to: finish_root/<VendorFolder>/
    """
    logger.info(f"Processing: {os.path.basename(pdf_path)}")

    # Step 2: Extract text
    result = extract_text_from_pdf(pdf_path)
    if result["is_image_pdf"]:
        logger.warning(f"  Image-based PDF detected, OCR not yet implemented: {pdf_path}")
        return {"error": "image_pdf_not_supported", "file": pdf_path}

    # Step 3: Clean text
    cleaned_text = clean_text_preserve_structure(result["full_text"])
    cleaned_pages = [clean_text_preserve_structure(p) for p in result["pages"]]

    # Step 4: Classify vendor
    vendor_id = classify_vendor(result["full_text"])

    if vendor_id == "unknown":
        # Auto-tune: use generic extractor for best-effort extraction
        vendor_id = "generic"
        logger.info(f"  Vendor not recognized, using auto-tune (generic) extractor")
    else:
        logger.info(f"  Vendor identified: {vendor_id}")

    # Get the right extractor from registry
    extractor = ExtractorRegistry.get_extractor(vendor_id)
    po = extractor.extract(cleaned_text, cleaned_pages)
    output = po.to_dict()

    # Score fields and flag for human review
    output = score_purchase_order(output, result["full_text"])
    if output.get('_review_required'):
        review_count = len(output.get('_review_fields', []))
        logger.warning(f"  ⚠ 需人工檢核 ({review_count} 欄位), 準確率: {output.get('_accuracy_pct', 0)}%")
    else:
        logger.info(f"  ✓ 準確率: {output.get('_accuracy_pct', 0)}%")

    # Build vendor subfolder path: output_root/<VendorFolder>/
    vendor_folder = get_vendor_folder(vendor_id)
    vendor_dir = os.path.join(output_root, vendor_folder)
    os.makedirs(vendor_dir, exist_ok=True)

    # Save JSON output
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = os.path.join(vendor_dir, f"{base_name}.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    logger.info(f"  Output saved: {os.path.relpath(output_path)}")

    # Move processed PDF to finish folder
    if finish_root:
        move_to_finish(pdf_path, vendor_id, finish_root)

    return output


def find_pdfs(input_path: str, recursive: bool = False) -> list:
    """Find all PDF files in the given path."""
    if os.path.isfile(input_path):
        return [input_path]

    pdf_files = []
    if recursive:
        for root, dirs, files in os.walk(input_path):
            for f in files:
                if f.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, f))
    else:
        for f in os.listdir(input_path):
            if f.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(input_path, f))

    return sorted(pdf_files)


def main():
    parser = argparse.ArgumentParser(
        description='PO PDF Feature Extractor - Extract structured data from PO PDFs'
    )
    parser.add_argument('--input', '-i', default=DEFAULT_INPUT_DIR,
                        help=f'PDF file or directory (default: import_doc/)')
    parser.add_argument('--output', '-o', default=DEFAULT_OUTPUT_DIR,
                        help=f'Output root directory (default: output_doc/)')
    parser.add_argument('--recursive', '-r', action='store_true', default=True,
                        help='Recursively scan subdirectories (default: True)')
    parser.add_argument('--no-recursive', dest='recursive', action='store_false',
                        help='Only scan top-level directory')
    parser.add_argument('--finish', '-f', default=DEFAULT_FINISH_DIR,
                        help=f'Finish directory for processed PDFs (default: import_doc/finish/)')
    parser.add_argument('--list-vendors', action='store_true',
                        help='List registered vendor extractors')

    args = parser.parse_args()

    if args.list_vendors:
        vendors = ExtractorRegistry.list_vendors()
        print(f"Registered extractors ({len(vendors)}):")
        for v in vendors:
            print(f"  - {v}")
        return

    if not os.path.exists(args.input):
        logger.error(f"Input path does not exist: {args.input}")
        logger.info(f"Please place PDF files in: {os.path.abspath(DEFAULT_INPUT_DIR)}")
        sys.exit(1)

    # Exclude finish/ subfolder when scanning
    pdf_files = [p for p in find_pdfs(args.input, args.recursive)
                 if not os.path.normpath(p).startswith(os.path.normpath(args.finish))]
    if not pdf_files:
        logger.error(f"No PDF files found in: {args.input}")
        logger.info(f"Place PDF files in: {os.path.abspath(DEFAULT_INPUT_DIR)}")
        sys.exit(1)

    logger.info(f"Found {len(pdf_files)} PDF file(s)")
    logger.info(f"Input:  {os.path.abspath(args.input)}")
    logger.info(f"Output: {os.path.abspath(args.output)}")
    logger.info(f"Finish: {os.path.abspath(args.finish)}")
    print("-" * 60)

    success = 0
    errors = 0
    vendor_counts = {}
    for pdf_path in pdf_files:
        try:
            result = process_single_pdf(pdf_path, args.output, args.finish)
            vid = result.get('vendor_id', 'unknown')
            vendor_counts[vid] = vendor_counts.get(vid, 0) + 1
            success += 1
        except Exception as e:
            logger.error(f"  FAILED: {pdf_path} - {e}")
            errors += 1

    print("-" * 60)
    logger.info(f"Done! {success} succeeded, {errors} failed out of {len(pdf_files)} files.")
    if vendor_counts:
        logger.info("Breakdown by vendor:")
        for vid, count in sorted(vendor_counts.items()):
            folder = get_vendor_folder(vid)
            logger.info(f"  {folder}: {count} file(s)")


if __name__ == '__main__':
    main()
