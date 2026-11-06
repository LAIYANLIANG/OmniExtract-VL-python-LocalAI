"""
PO PDF Feature Extractor - Web Interface

Usage:
    py -m po_extractor.webapp
    Then open http://127.0.0.1:5000 in your browser.
"""
import os
import sys
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List

from flask import (
    Flask, render_template, request, jsonify,
    send_from_directory, redirect, url_for
)
from werkzeug.utils import secure_filename
from po_extractor.pipeline.confidence_scorer import score_purchase_order
from po_extractor.pipeline.learning_advisor import suggest_learning_opportunities, apply_learning_suggestions
from po_extractor.pipeline.knowledge_base import KnowledgeBase

# Ensure workspace root is on sys.path
_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_DIR = os.path.dirname(_PACKAGE_DIR)
if _WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, _WORKSPACE_DIR)

from po_extractor.pipeline.step2_extract import extract_text_from_pdf
from po_extractor.pipeline.step3_clean import clean_text_preserve_structure
from po_extractor.pipeline.step4_classify import classify_vendor
from po_extractor.extractors.registry import ExtractorRegistry
import po_extractor.extractors  # noqa: F401 - trigger registration
from po_extractor.config import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR, DEFAULT_FINISH_DIR, VENDOR_FOLDER_MAP
from po_extractor.config import DEFAULT_CORRECTED_DIR, LEARNED_PATTERNS_PATH

# Optional imports for enhanced pipeline (graceful degradation)
try:
    from po_extractor.pipeline.pipeline_orchestrator import process_po_document, get_orchestrator_instance
    HAS_ORCHESTRATOR = True
except ImportError:
    HAS_ORCHESTRATOR = False

try:
    from po_extractor.pipeline.step7_qwen_audit import QwenClient, audit_extraction_results
    from po_extractor.pipeline.qwen_learning_system import qwen_learning_system
    HAS_QWEN = True
except ImportError:
    HAS_QWEN = False
    qwen_learning_system = None

try:
    from po_extractor.pipeline.feedback_engine import FeedbackEngine
    HAS_FEEDBACK = True
except ImportError:
    HAS_FEEDBACK = False

import shutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    template_folder=os.path.join(_PACKAGE_DIR, 'templates'),
    static_folder=os.path.join(_PACKAGE_DIR, 'static'),
)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload

ALLOWED_EXTENSIONS = {'.pdf'}
IMPORT_DIR = DEFAULT_INPUT_DIR
OUTPUT_DIR = DEFAULT_OUTPUT_DIR
FINISH_DIR = DEFAULT_FINISH_DIR
CORRECTED_DIR = DEFAULT_CORRECTED_DIR


def get_vendor_folder(vendor_id: str) -> str:
    if vendor_id in VENDOR_FOLDER_MAP:
        return VENDOR_FOLDER_MAP[vendor_id]
    return vendor_id.upper().replace(' ', '_')


def track_field_sources(output_data: dict, pages: list) -> dict:
    """Track which page each field value appears on.
    
    Returns dict mapping field_path -> list of page numbers (1-based).
    """
    field_sources = {}
    
    def find_value_in_pages(value: str, pages: list) -> list:
        """Find which pages contain the given value."""
        if not value or not value.strip():
            return []
        
        found_pages = []
        for i, page_text in enumerate(pages):
            if value.strip() in page_text:
                found_pages.append(i + 1)  # 1-based page numbers
        
        return found_pages
    
    def traverse_dict(data, prefix=""):
        """Recursively traverse dict and track field sources."""
        for key, val in data.items():
            if key.startswith('_') or key == 'line_items':
                continue
                
            current_path = f"{prefix}.{key}" if prefix else key
            
            if isinstance(val, dict):
                traverse_dict(val, current_path)
            elif isinstance(val, str) and val.strip():
                sources = find_value_in_pages(val, pages)
                if sources:
                    field_sources[current_path] = sources
    
    # Track main fields
    traverse_dict(output_data)
    
    # Handle line_items separately
    line_items = output_data.get('line_items', [])
    for i, item in enumerate(line_items):
        if isinstance(item, dict):
            for key, val in item.items():
                if isinstance(val, str) and val.strip():
                    field_path = f"line_items.{i}.{key}"
                    sources = find_value_in_pages(val, pages)
                    if sources:
                        field_sources[field_path] = sources
    
    return field_sources


def process_pdf(pdf_path: str) -> dict:
    """Run the extraction pipeline on a single PDF. Returns result dict."""
    filename = os.path.basename(pdf_path)

    result = extract_text_from_pdf(pdf_path)
    if result["is_image_pdf"]:
        return {
            "filename": filename,
            "status": "error",
            "message": "Image-based PDF detected, OCR not yet supported",
        }

    cleaned_text = clean_text_preserve_structure(result["full_text"])
    cleaned_pages = [clean_text_preserve_structure(p) for p in result["pages"]]

    vendor_id = classify_vendor(result["full_text"])
    if vendor_id == "unknown":
        vendor_id = "generic"

    extractor = ExtractorRegistry.get_extractor(vendor_id)
    po = extractor.extract(cleaned_text, cleaned_pages)
    
    # Apply learned patterns to improve extraction results
    try:
        from po_extractor.pipeline.pattern_applier import apply_learned_patterns
        patterns_applied = apply_learned_patterns(po, vendor_id, result["full_text"])
        if patterns_applied > 0:
            logger.info(f"  Applied {patterns_applied} learned patterns for vendor {vendor_id}")
    except Exception as e:
        logger.warning(f"  Failed to apply learned patterns: {e}")
    
    output = po.to_dict()

    # Apply learned accuracy patterns before confidence scoring
    if HAS_QWEN and qwen_learning_system:
        try:
            output, patterns_applied = qwen_learning_system.apply_accuracy_patterns(
                output, result["full_text"], vendor_id
            )
            if patterns_applied > 0:
                logger.info(f"Applied {patterns_applied} accuracy patterns for {vendor_id}")
        except Exception as e:
            logger.warning(f"Failed to apply accuracy patterns: {e}")
    
    # Add confidence scoring and review flags
    output = score_purchase_order(output, result["full_text"])
    
    # Analyze learning opportunities
    try:
        learning_opportunities = suggest_learning_opportunities(
            output, result["full_text"], vendor_id
        )
        if learning_opportunities:
            # Apply high-priority suggestions automatically
            suggestion_stats = apply_learning_suggestions(learning_opportunities)
            logger.info(f"  Generated {len(learning_opportunities)} learning suggestions, applied {suggestion_stats['patterns_generated']} patterns")
            
            # Add learning suggestions to output for UI display
            output["_learning_suggestions"] = [
                {
                    "field": opp.field_path,
                    "type": opp.suggestion_type,
                    "details": opp.details,
                    "priority": opp.priority
                }
                for opp in learning_opportunities[:5]  # Top 5 suggestions
            ]
    except Exception as e:
        logger.warning(f"  Learning analysis failed: {e}")
    
    # Add page information
    output["_page_info"] = {
        "total_pages": len(result["pages"]),
        "pages": [
            {"page": i+1, "text": page_text} 
            for i, page_text in enumerate(result["pages"])
        ]
    }
    
    # Add field source tracking
    output["_field_sources"] = track_field_sources(output, result["pages"])

    # Step 7: Qwen3-VL audit verification (92% confidence threshold)
    qwen_audit_result = None
    qwen_triggered = False
    learning_record_id = None
    
    confidence_score = output.get('_accuracy_pct', 0) / 100.0  # Convert to 0-1 scale
    CONFIDENCE_THRESHOLD = 0.92  # 92% threshold
    
    if HAS_QWEN and confidence_score < CONFIDENCE_THRESHOLD:
        qwen_triggered = True
        
        # Record Qwen trigger event in learning system
        if qwen_learning_system:
            low_confidence_fields = [
                field for field, data in output.get('_confidence', {}).items()
                if isinstance(data, dict) and data.get('score', 100) < 92
            ]
            
            learning_record_id = qwen_learning_system.record_qwen_trigger(
                pdf_path=pdf_path,
                raw_text=result["full_text"],
                confidence_score=confidence_score,
                low_confidence_fields=low_confidence_fields,
                vendor_type=vendor_id,
                original_extraction=output.copy(),
                trigger_reason="low_confidence"
            )
            
            logger.info(f"Qwen觸發: 信心分數 {confidence_score:.1%} < {CONFIDENCE_THRESHOLD:.0%}, 記錄ID: {learning_record_id}")
        
        try:
            extraction_results = {"basic_extraction": output}
            qwen_audit_result = audit_extraction_results(
                extraction_results, 
                image_path=pdf_path
            )
            if qwen_audit_result.get("audit_executed"):
                # Apply Qwen corrections to output
                voting_results = qwen_audit_result.get("voting_results", {})
                corrections_applied = 0
                qwen_corrections = {}
                
                for field_path, vote in voting_results.items():
                    if vote.get("confidence", 0) > 0.8 and vote.get("correct_value"):
                        # Navigate nested dict to apply correction
                        parts = field_path.split(".")
                        target = output
                        for part in parts[:-1]:
                            if part.isdigit():
                                target = target[int(part)] if isinstance(target, list) else target
                            elif isinstance(target, dict):
                                target = target.get(part, {})
                        if isinstance(target, dict) and parts[-1] in target:
                            old_val = target[parts[-1]]
                            target[parts[-1]] = vote["correct_value"]
                            if old_val != vote["correct_value"]:
                                corrections_applied += 1
                                qwen_corrections[field_path] = {
                                    "old_value": old_val,
                                    "new_value": vote["correct_value"],
                                    "confidence": vote.get("confidence", 0)
                                }
                
                # Record Qwen corrections in learning system
                if qwen_learning_system and learning_record_id and qwen_corrections:
                    qwen_learning_system.update_qwen_corrections(learning_record_id, qwen_corrections)
                
                output["_qwen_audit"] = {
                    "executed": True,
                    "triggered_by": "low_confidence" if qwen_triggered else "manual",
                    "confidence_threshold": CONFIDENCE_THRESHOLD,
                    "actual_confidence": confidence_score,
                    "learning_record_id": learning_record_id,
                    "fields_audited": qwen_audit_result.get("total_fields_audited", 0),
                    "qwen_invoked": qwen_audit_result.get("qwen_invoked_count", 0),
                    "corrections_applied": corrections_applied,
                    "statistics": qwen_audit_result.get("statistics", {})
                }
                logger.info(f"  Qwen audit: {qwen_audit_result.get('total_fields_audited', 0)} fields audited, {corrections_applied} corrections applied")
            else:
                output["_qwen_audit"] = {
                    "executed": False,
                    "reason": qwen_audit_result.get("reason", "confidence_above_threshold")
                }
                logger.info(f"  Qwen audit skipped: {qwen_audit_result.get('reason', 'high confidence')}")
        except Exception as e:
            output["_qwen_audit"] = {"executed": False, "reason": f"error: {str(e)}"}
            logger.warning(f"  Qwen audit failed: {e}")
    else:
        # Qwen not triggered - either due to high confidence or unavailable
        if HAS_QWEN and confidence_score >= CONFIDENCE_THRESHOLD:
            output["_qwen_audit"] = {
                "executed": False,
                "reason": "high_confidence",
                "confidence_threshold": CONFIDENCE_THRESHOLD,
                "actual_confidence": confidence_score,
                "triggered_by": "none"
            }
            logger.info(f"  Qwen未觸發: 信心分數 {confidence_score:.1%} >= {CONFIDENCE_THRESHOLD:.0%}")
        else:
            output["_qwen_audit"] = {"executed": False, "reason": "qwen_module_not_available"}

    # 🎯 Qwen仲裁執行標註 (特別標記)
    qwen_executed_indicator = create_qwen_execution_indicator(output.get("_qwen_audit", {}), qwen_triggered, confidence_score)
    output["_qwen_execution_indicator"] = qwen_executed_indicator

    # Save to output_doc/<Vendor>/
    vendor_folder = get_vendor_folder(vendor_id)
    vendor_dir = os.path.join(OUTPUT_DIR, vendor_folder)
    os.makedirs(vendor_dir, exist_ok=True)

    base_name = os.path.splitext(filename)[0]
    json_filename = f"{base_name}.json"
    output_path = os.path.join(vendor_dir, json_filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Move processed PDF to finish/<Vendor>/
    finish_vendor_dir = os.path.join(FINISH_DIR, vendor_folder)
    os.makedirs(finish_vendor_dir, exist_ok=True)
    finish_dest = os.path.join(finish_vendor_dir, filename)
    if os.path.exists(pdf_path):
        shutil.move(pdf_path, finish_dest)
        logger.info(f"  Moved to finish: {os.path.relpath(finish_dest)}")

    return {
        "filename": filename,
        "status": "success",
        "vendor_id": vendor_id,
        "vendor_folder": vendor_folder,
        "po_number": output.get("purchase_info", {}).get("po_number", ""),
        "date": output.get("purchase_info", {}).get("date", ""),
        "total_amount": output.get("purchase_info", {}).get("total_amount", ""),
        "item_count": len(output.get("line_items", [])),
        "json_path": f"{vendor_folder}/{json_filename}",
        "accuracy_pct": output.get("_accuracy_pct", 0),
        "review_required": output.get("_review_required", False),
        "review_fields": output.get("_review_fields", []),
        "qwen_audit": output.get("_qwen_audit", {}),
    }


# ─── Routes ───────────────────────────────────────────────

@app.route('/')
def index():
    """Main upload page."""
    vendors = ExtractorRegistry.list_vendors()
    return render_template('index.html', vendors=vendors)


@app.route('/upload', methods=['POST'])
def upload():
    """Handle file uploads and process them."""
    if 'files' not in request.files:
        return jsonify({"error": "No files uploaded"}), 400

    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "No files selected"}), 400

    results = []
    for file in files:
        if not file.filename:
            continue

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": f"Unsupported file type: {ext}",
            })
            continue

        # Save to import_doc/
        safe_name = secure_filename(file.filename)
        if not safe_name:
            safe_name = f"{uuid.uuid4().hex[:8]}.pdf"
        os.makedirs(IMPORT_DIR, exist_ok=True)
        save_path = os.path.join(IMPORT_DIR, safe_name)
        file.save(save_path)
        logger.info(f"Uploaded: {safe_name}")

        # Process
        try:
            result = process_pdf(save_path)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {safe_name}: {e}")
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e),
            })

    return jsonify({"results": results})


@app.route('/process-all', methods=['POST'])
def process_all():
    """Scan import_doc/ and process all unprocessed PDFs."""
    if not os.path.exists(IMPORT_DIR):
        return jsonify({"error": "import_doc/ folder does not exist"}), 400

    pdf_files = []
    finish_norm = os.path.normpath(FINISH_DIR)
    for root, dirs, files in os.walk(IMPORT_DIR):
        # Skip the finish/ subfolder
        if os.path.normpath(root).startswith(finish_norm):
            continue
        for f in files:
            if f.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, f))

    if not pdf_files:
        return jsonify({"error": "No PDF files found in import_doc/"}), 400

    results = []
    for pdf_path in sorted(pdf_files):
        try:
            result = process_pdf(pdf_path)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed: {pdf_path} - {e}")
            results.append({
                "filename": os.path.basename(pdf_path),
                "status": "error",
                "message": str(e),
            })

    return jsonify({"results": results})


@app.route('/results')
def list_results():
    """List all JSON results grouped by vendor. Merges output_doc and corrected dirs.
    Returns: {
        "<vendor>": {
            "files": ["file1.json", "file2.json"], 
            "corrected_files": ["file1.json"]  # files that have corrections
        }
    }
    """
    vendor_data = {}
    
    # Scan output_doc (original files)
    if os.path.exists(OUTPUT_DIR):
        for vendor_folder in os.listdir(OUTPUT_DIR):
            vendor_path = os.path.join(OUTPUT_DIR, vendor_folder)
            if os.path.isdir(vendor_path):
                json_files = [f for f in os.listdir(vendor_path) if f.endswith('.json')]
                if json_files:
                    vendor_data[vendor_folder] = {
                        "files": sorted(json_files),
                        "corrected_files": []
                    }
    
    # Scan corrected directory and mark corrected files
    if os.path.exists(CORRECTED_DIR):
        for vendor_folder in os.listdir(CORRECTED_DIR):
            vendor_path = os.path.join(CORRECTED_DIR, vendor_folder)
            if os.path.isdir(vendor_path):
                json_files = [f for f in os.listdir(vendor_path) if f.endswith('.json')]
                if json_files:
                    if vendor_folder not in vendor_data:
                        vendor_data[vendor_folder] = {"files": [], "corrected_files": []}
                    
                    # Add corrected files to the list and mark them
                    for json_file in sorted(json_files):
                        if json_file not in vendor_data[vendor_folder]["files"]:
                            vendor_data[vendor_folder]["files"].append(json_file)
                        vendor_data[vendor_folder]["corrected_files"].append(json_file)
                    
                    # Re-sort files after adding corrected ones
                    vendor_data[vendor_folder]["files"] = sorted(vendor_data[vendor_folder]["files"])
    
    return jsonify(vendor_data)


@app.route('/download/<path:filepath>')
def download(filepath):
    """Download a JSON result file. Prefers corrected version if exists."""
    safe_path = os.path.normpath(filepath)
    if '..' in safe_path:
        return jsonify({"error": "Invalid path"}), 400
    
    # Check for corrected version first
    corrected_path = os.path.join(CORRECTED_DIR, safe_path)
    if os.path.isfile(corrected_path):
        return send_from_directory(CORRECTED_DIR, safe_path, as_attachment=True)
    
    # Fallback to original version
    return send_from_directory(OUTPUT_DIR, safe_path, as_attachment=True)


@app.route('/view/<path:filepath>')
def view_json(filepath):
    """View a JSON result file. Prefers corrected version if exists."""
    safe_path = os.path.normpath(filepath)
    if '..' in safe_path:
        return jsonify({"error": "Invalid path"}), 400
    
    # Check for corrected version first
    corrected_path = os.path.join(CORRECTED_DIR, safe_path)
    if os.path.isfile(corrected_path):
        with open(corrected_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Add flag to indicate this is a corrected version
        data['_is_corrected'] = True
        return jsonify(data)
    
    # Fallback to original version
    full_path = os.path.join(OUTPUT_DIR, safe_path)
    if not os.path.isfile(full_path):
        return jsonify({"error": "File not found"}), 404
    with open(full_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['_is_corrected'] = False
    return jsonify(data)


@app.route('/view-original/<path:filepath>')
def view_original(filepath):
    """Force view original version (from output_doc).""" 
    safe_path = os.path.normpath(filepath)
    if '..' in safe_path:
        return jsonify({"error": "Invalid path"}), 400
    
    full_path = os.path.join(OUTPUT_DIR, safe_path)
    if not os.path.isfile(full_path):
        return jsonify({"error": "Original file not found"}), 404
    
    with open(full_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['_is_corrected'] = False
    data['_is_original_view'] = True
    return jsonify(data)


@app.route('/view-corrected/<path:filepath>')
def view_corrected(filepath):
    """Force view corrected version (from corrected/)."""
    safe_path = os.path.normpath(filepath) 
    if '..' in safe_path:
        return jsonify({"error": "Invalid path"}), 400
    
    corrected_path = os.path.join(CORRECTED_DIR, safe_path)
    if not os.path.isfile(corrected_path):
        return jsonify({"error": "Corrected file not found"}), 404
    
    with open(corrected_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['_is_corrected'] = True
    data['_is_corrected_view'] = True  
    return jsonify(data)


@app.route('/pdf-pages/<path:filepath>')
def get_pdf_pages(filepath):
    """Get PDF pages text for a specific file.
    
    Args:
        filepath: Path like "VENDOR/filename.json"
        
    Returns:
        JSON with page information if available in the output JSON,
        or tries to extract from the archived PDF in finish/ folder.
    """
    safe_path = os.path.normpath(filepath)
    if '..' in safe_path:
        return jsonify({"error": "Invalid path"}), 400
    
    # First try to get page info from existing JSON
    json_path = os.path.join(OUTPUT_DIR, safe_path)
    if os.path.isfile(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if '_page_info' in data:
                return jsonify(data['_page_info'])
    
    # Fallback: try to find and extract from PDF in finish/ folder
    base_name = os.path.splitext(os.path.basename(safe_path))[0]
    vendor_folder = os.path.dirname(safe_path)
    
    # Search for PDF in finish/<vendor>/
    finish_vendor_dir = os.path.join(FINISH_DIR, vendor_folder)
    if os.path.exists(finish_vendor_dir):
        for file in os.listdir(finish_vendor_dir):
            if file.lower().endswith('.pdf') and os.path.splitext(file)[0] == base_name:
                pdf_path = os.path.join(finish_vendor_dir, file)
                try:
                    result = extract_text_from_pdf(pdf_path)
                    if not result['is_image_pdf']:
                        return jsonify({
                            "total_pages": len(result["pages"]),
                            "pages": [
                                {"page": i+1, "text": page_text} 
                                for i, page_text in enumerate(result["pages"])
                            ]
                        })
                except Exception as e:
                    logger.error(f"Failed to extract PDF pages: {e}")
    
    return jsonify({"error": "PDF pages not found"}), 404


# ─── Correction & Learning Routes ─────────────────────────

@app.route('/save-correction', methods=['POST'])
def save_correction():
    """Save a human-corrected JSON to corrected/<Vendor>/.

    Expects JSON body: { "filepath": "VENDOR/file.json", "data": { ... corrected PO dict ... } }
    """
    body = request.get_json()
    if not body or 'filepath' not in body or 'data' not in body:
        return jsonify({"error": "Missing filepath or data"}), 400

    filepath = os.path.normpath(body['filepath'])
    if '..' in filepath:
        return jsonify({"error": "Invalid path"}), 400

    # Save to corrected/<Vendor>/file.json
    corrected_path = os.path.join(CORRECTED_DIR, filepath)
    os.makedirs(os.path.dirname(corrected_path), exist_ok=True)

    with open(corrected_path, 'w', encoding='utf-8') as f:
        json.dump(body['data'], f, ensure_ascii=False, indent=2)

    logger.info(f"Correction saved: {filepath}")
    
    # Record learning event in knowledge base
    try:
        kb = KnowledgeBase()
        kb.record_learning_event(
            vendor_id=body['data'].get('vendor_id', 'unknown'),
            field_path='manual_correction',
            event_type='correction_applied',
            before_value='various_fields',
            after_value='corrected_values',
            confidence_before=50.0,  # Estimated
            confidence_after=100.0,  # Manual correction = perfect
            source_file=filepath,
            notes=f"Manual correction with {changedCount} field changes"
        )
    except Exception as e:
        logger.warning(f"Failed to record learning event: {e}")
    
    # Automatically trigger learning from this correction
    try:
        from po_extractor.pipeline.pattern_learner import learn_from_corrections
        logger.info("Auto-triggering pattern learning after correction...")
        stats = learn_from_corrections()
        logger.info(f"Learning completed: {stats.get('patterns_generated', 0)} patterns generated")
        
        return jsonify({
            "status": "saved_and_learned", 
            "path": filepath,
            "learning_stats": stats
        })
    except Exception as e:
        logger.error(f"Failed to auto-trigger learning: {e}")
        # Still return success for the correction save
        return jsonify({
            "status": "saved", 
            "path": filepath,
            "learning_error": str(e)
        })


@app.route('/learn', methods=['POST'])
def run_learning():
    """Trigger pattern learning from corrected/ folder."""
    from po_extractor.pipeline.pattern_learner import learn_from_corrections
    stats = learn_from_corrections()
    
    # Update knowledge base with learning results
    try:
        kb = KnowledgeBase()
        insights = kb.get_learning_insights(days=7)  # Last week's insights
        stats['knowledge_insights'] = insights['summary']
        stats['recommendations'] = insights['recommendations'][:3]  # Top 3 recommendations
    except Exception as e:
        logger.warning(f"Failed to get knowledge insights: {e}")
        
    return jsonify(stats)


@app.route('/learn/generate', methods=['POST'])
def run_generate():
    """Trigger learning + auto-generate extractors."""
    from po_extractor.pipeline.pattern_learner import learn_from_corrections
    from po_extractor.pipeline.extractor_generator import check_and_generate_extractors

    stats = learn_from_corrections()
    generated = check_and_generate_extractors()
    stats['generated_extractors'] = generated
    return jsonify(stats)


@app.route('/learn/status')
def learn_status():
    """Return learning status as JSON."""
    result = {
        'corrected_files': {},
        'learned_patterns': {},
        'total_patterns': 0,
    }

    # Count corrected files
    if os.path.exists(CORRECTED_DIR):
        for vendor in os.listdir(CORRECTED_DIR):
            vp = os.path.join(CORRECTED_DIR, vendor)
            if os.path.isdir(vp):
                count = len([f for f in os.listdir(vp) if f.endswith('.json')])
                if count > 0:
                    result['corrected_files'][vendor] = count

    # Count learned patterns
    if os.path.exists(LEARNED_PATTERNS_PATH):
        with open(LEARNED_PATTERNS_PATH, 'r', encoding='utf-8') as f:
            patterns = json.load(f)
        for vid in patterns:
            if vid.startswith('_'):
                continue
            field_count = len(patterns[vid])
            result['learned_patterns'][vid] = field_count
            result['total_patterns'] += sum(len(pats) for pats in patterns[vid].values())

    return jsonify(result)


@app.route('/pretrain', methods=['POST'])
def pretrain():
    """Pretrain from user-provided PDF and field data.
    
    Expected form data:
    - pdf: PDF file
    - vendor_id: Vendor ID (optional, will auto-detect if not provided)  
    - fields: JSON string of field data
    """
    try:
        # Get uploaded PDF
        if 'pdf' not in request.files:
            return jsonify({"error": "No PDF file provided"}), 400
            
        pdf_file = request.files['pdf']
        if not pdf_file.filename:
            return jsonify({"error": "No file selected"}), 400
            
        # Get vendor_id
        vendor_id = request.form.get('vendor_id', '').strip()
        
        # Get fields data
        fields_json = request.form.get('fields', '{}')
        try:
            fields_data = json.loads(fields_json)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid fields JSON format"}), 400
            
        if not fields_data:
            return jsonify({"error": "No field data provided"}), 400
        
        # Save PDF temporarily
        safe_filename = secure_filename(pdf_file.filename)
        if not safe_filename:
            safe_filename = f"pretrain_{uuid.uuid4().hex[:8]}.pdf"
        temp_pdf = os.path.join(IMPORT_DIR, safe_filename)
        pdf_file.save(temp_pdf)
        
        try:
            # Extract text
            result = extract_text_from_pdf(temp_pdf)
            if result["is_image_pdf"]:
                return jsonify({"error": "Image-based PDF not supported for pretraining"}), 400
            
            raw_text = result["full_text"]
            cleaned_text = clean_text_preserve_structure(raw_text)
            
            # Auto-detect vendor if not provided
            if not vendor_id:
                vendor_id = classify_vendor(raw_text)
                if vendor_id == "unknown":
                    vendor_id = "pretrain_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Learn from provided data
            from po_extractor.pipeline.pattern_learner import learn_from_pretrain
            stats = learn_from_pretrain(cleaned_text, fields_data, vendor_id, safe_filename)
            
            # Also save as corrected data for future learning
            base_name = os.path.splitext(safe_filename)[0]
            vendor_folder = get_vendor_folder(vendor_id)
            corrected_dir = os.path.join(CORRECTED_DIR, vendor_folder)
            os.makedirs(corrected_dir, exist_ok=True)
            
            # Create a basic PO structure with the provided fields
            corrected_po = {
                "vendor_id": vendor_id,
                "purchase_info": {},
                "vendor_info": {},
                "bill_to": {},
                "ship_to": {},
                "line_items": [],
                "_pretrained": True,
                "_pretrain_date": datetime.now().isoformat()
            }
            
            # Populate fields
            for field_path, value in fields_data.items():
                if value and value.strip():
                    setNestedValue(corrected_po, field_path, value.strip())
            
            corrected_path = os.path.join(corrected_dir, f"{base_name}.json")
            with open(corrected_path, 'w', encoding='utf-8') as f:
                json.dump(corrected_po, f, ensure_ascii=False, indent=2)
            
            # Move PDF to finish folder
            finish_vendor_dir = os.path.join(FINISH_DIR, vendor_folder)
            os.makedirs(finish_vendor_dir, exist_ok=True)
            finish_path = os.path.join(finish_vendor_dir, safe_filename)
            shutil.move(temp_pdf, finish_path)
            
            return jsonify({
                "status": "success",
                "vendor_id": vendor_id,
                "vendor_folder": vendor_folder,
                "patterns_learned": stats['patterns_generated'],
                "fields_processed": stats['fields_processed'],
                "patterns_failed": stats['patterns_failed'],
                "results": stats['results'],
                "corrected_saved": corrected_path
            })
            
        finally:
            # Clean up temp file if still exists
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)
                
    except Exception as e:
        logger.error(f"Pretrain failed: {e}")
        return jsonify({"error": str(e)}), 500


def setNestedValue(obj, path, value):
    """Helper function to set nested dictionary values."""
    parts = path.split('.')
    current = obj
    for i, part in enumerate(parts[:-1]):
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


@app.route('/learning/insights')
def get_learning_insights():
    """Get learning insights and recommendations."""
    try:
        kb = KnowledgeBase()
        insights = kb.get_learning_insights(days=30)
        return jsonify(insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/learning/tunnie-report')
def get_tunnie_report():
    """Get comprehensive TUNNIE-style learning report."""
    try:
        from po_extractor.pipeline.knowledge_base import get_tunnie_style_report
        report = get_tunnie_style_report()
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/learning/vendor/<vendor_id>')
def get_vendor_learning_summary(vendor_id):
    """Get learning summary for specific vendor."""
    try:
        kb = KnowledgeBase()
        summary = kb.get_learning_summary_for_vendor(vendor_id)
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/learning/problematic-patterns') 
def get_problematic_patterns():
    """Get patterns that need attention or retraining."""
    try:
        kb = KnowledgeBase()
        patterns = kb.get_problematic_patterns()
        return jsonify({"problematic_patterns": patterns})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/corrections')
def list_corrections():
    """List all corrected JSON files grouped by vendor."""
    vendor_data = {}
    if os.path.exists(CORRECTED_DIR):
        for vendor_folder in sorted(os.listdir(CORRECTED_DIR)):
            vendor_path = os.path.join(CORRECTED_DIR, vendor_folder)
            if os.path.isdir(vendor_path):
                json_files = [f for f in os.listdir(vendor_path) if f.endswith('.json')]
                if json_files:
                    vendor_data[vendor_folder] = sorted(json_files)
    return jsonify(vendor_data)


if __name__ == '__main__':
    os.makedirs(IMPORT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(CORRECTED_DIR, exist_ok=True)


# === Qwen3-VL Enhanced API Endpoints ===

@app.route('/qwen/process', methods=['POST'])
def qwen_enhanced_process():
    """使用完整七步管道處理PDF（包含Qwen審核）"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are supported"}), 400
    
    # 儲存檔案
    safe_name = secure_filename(file.filename)
    if not safe_name:
        safe_name = f"{uuid.uuid4().hex[:8]}.pdf"
    
    temp_path = os.path.join(IMPORT_DIR, safe_name)
    file.save(temp_path)
    
    try:
        # 使用七步管道處理
        result = process_po_document(
            temp_path,
            enable_qwen_audit=request.form.get('enable_qwen_audit', 'true').lower() == 'true',
            enable_layoutlm=request.form.get('enable_layoutlm', 'false').lower() == 'true'
        )
        
        # 儲存結果
        base_name = os.path.splitext(safe_name)[0]
        output_path = os.path.join(OUTPUT_DIR, f"{base_name}.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result['final_extraction'], f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "status": "success",
            "filename": safe_name,
            "processing_time": result['pipeline_stats']['total_time'],
            "steps_executed": result['pipeline_stats']['steps_executed'],
            "qwen_used": not result['steps_results']['step7'].get('skipped', True),
            "layoutlm_used": not result['steps_results']['step6'].get('skipped', True),
            "result_path": output_path,
            "pipeline_details": result['pipeline_stats']
        })
        
    except Exception as e:
        logger.error(f"Qwen enhanced processing failed: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        # 清理臨時檔案
        try:
            os.remove(temp_path)
        except:
            pass


@app.route('/qwen/audit', methods=['POST'])
def qwen_audit_results():
    """使用Qwen審核現有的提取結果"""
    data = request.get_json()
    if not data or 'extraction_results' not in data:
        return jsonify({"error": "No extraction results provided"}), 400
    
    try:
        # 初始化Qwen客戶端
        qwen_client = get_qwen_client()
        if not qwen_client or not qwen_client.is_available():
            return jsonify({"error": "Qwen client not available"}), 503
        
        extraction_results = data['extraction_results']
        image_paths = data.get('image_paths', [])
        
        # 執行Qwen審核
        from po_extractor.pipeline.step7_qwen_audit import qwen_audit_vote_results
        audit_result = qwen_audit_vote_results(
            {"final_decision": extraction_results},
            image_paths,
            original_pdf=data.get('original_pdf')
        )
        
        return jsonify({
            "status": "success",
            "audit_result": audit_result,
            "qwen_available": True
        })
        
    except Exception as e:
        logger.error(f"Qwen audit failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/qwen/feedback', methods=['POST'])
def submit_qwen_feedback():
    """提交用戶修正給Qwen進行學習"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        feedback_engine = FeedbackEngine()
        
        # 記錄用戶修正
        correction_event = {
            "timestamp": datetime.now().isoformat(),
            "user_corrections": data.get('corrections', {}),
            "original_extraction": data.get('original_extraction', {}),
            "document_path": data.get('document_path', ""),
            "correction_type": data.get('correction_type', "manual")
        }
        
        feedback_engine.record_learning_event(
            event_type="user_correction",
            details=correction_event
        )
        
        # 如果提供了圖片路徑，請求Qwen分析
        if data.get('image_paths') and data.get('corrections'):
            qwen_client = get_qwen_client()
            if qwen_client and qwen_client.is_available():
                try:
                    suggestions = qwen_client.diagnose_extraction_errors(
                        data['corrections'],
                        data['original_extraction'],
                        data['image_paths']
                    )
                    
                    if suggestions:
                        feedback_engine.apply_suggestions(suggestions)
                        
                        return jsonify({
                            "status": "success",
                            "message": "Feedback recorded and Qwen suggestions applied",
                            "suggestions_applied": len(suggestions),
                            "qwen_analysis": True
                        })
                except Exception as qwen_error:
                    logger.warning(f"Qwen analysis failed: {qwen_error}")
        
        return jsonify({
            "status": "success", 
            "message": "Feedback recorded successfully",
            "qwen_analysis": False
        })
        
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/qwen/status')
def qwen_status():
    """檢查Qwen系統狀態"""
    try:
        orchestrator = get_orchestrator_instance()
        health = orchestrator.get_pipeline_health()
        
        qwen_client = get_qwen_client()
        qwen_available = qwen_client and qwen_client.is_available()
        
        return jsonify({
            "qwen_available": qwen_available,
            "pipeline_health": health,
            "seven_step_pipeline": True,
            "voting_system": health.get('voting_system_status', False),
            "feedback_engine": health.get('feedback_engine_status', False)
        })
        
    except Exception as e:
        return jsonify({
            "qwen_available": False,
            "error": str(e),
            "seven_step_pipeline": False
        }), 500


@app.route('/qwen/config', methods=['GET', 'POST'])
def qwen_config():
    """獲取或更新Qwen配置"""
    config_path = "po_extractor/config/qwen_config.json"
    
    if request.method == 'GET':
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return jsonify(config)
        except FileNotFoundError:
            return jsonify({"error": "Config file not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'POST':
        try:
            new_config = request.get_json()
            if not new_config:
                return jsonify({"error": "No configuration data provided"}), 400
            
            # 備份舊配置
            import shutil
            try:
                shutil.copy(config_path, f"{config_path}.backup")
            except:
                pass
            
            # 儲存新配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                "status": "success",
                "message": "Configuration updated successfully"
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route('/learning/manual_corrections', methods=['POST'])
def record_manual_corrections():
    """記錄人工修正，用於Qwen學習系統"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        learning_record_id = data.get('learning_record_id')
        manual_corrections = data.get('manual_corrections', {})
        final_extraction = data.get('final_extraction', {})
        
        if not learning_record_id:
            return jsonify({"error": "learning_record_id is required"}), 400
        
        if not manual_corrections:
            return jsonify({"error": "manual_corrections is required"}), 400
            
        # 記錄人工修正到學習系統
        if HAS_QWEN and qwen_learning_system:
            qwen_learning_system.record_manual_corrections(
                learning_record_id, 
                manual_corrections, 
                final_extraction
            )
            
            # 獲取使用統計
            stats = qwen_learning_system.get_usage_statistics()
            
            return jsonify({
                "status": "success",
                "message": "Manual corrections recorded successfully",
                "learning_record_id": learning_record_id,
                "corrections_count": len(manual_corrections),
                "learning_stats": stats
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Qwen learning system not available"
            }), 503
            
    except Exception as e:
        logger.error(f"Recording manual corrections failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/learning/stats')
def get_learning_stats():
    """獲取Qwen學習系統統計"""
    try:
        if HAS_QWEN and qwen_learning_system:
            stats = qwen_learning_system.get_usage_statistics()
            return jsonify({
                "status": "success",
                "stats": stats,
                "threshold_config": {
                    "confidence_threshold": 0.92,
                    "description": "Qwen觸發閾值: 信心分數 < 92%"
                }
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Qwen learning system not available"
            }), 503
            
    except Exception as e:
        logger.error(f"Getting learning stats failed: {e}")
        return jsonify({"error": str(e)}), 500


def create_qwen_execution_indicator(qwen_audit_data: Dict[str, Any], qwen_triggered: bool, confidence_score: float) -> Dict[str, Any]:
    """
    創建Qwen執行指示器 - 明顯標註是否執行了Qwen仲裁
    
    根據多個數據點判斷：
    - executed狀態
    - qwen_invoked次數  
    - learning_record_id存在
    - 觸發原因
    - 信心分數
    """
    executed = qwen_audit_data.get("executed", False)
    qwen_invoked = qwen_audit_data.get("qwen_invoked", 0)
    learning_record_id = qwen_audit_data.get("learning_record_id")
    triggered_by = qwen_audit_data.get("triggered_by")
    
    # 特殊處理：如果是舊數據（沒有 qwen_audit_data 或只有默認值），顯示舊數據狀態
    # 舊數據的特徵：qwen_audit_data為空或只有默認值，且confidence_score為0（默認值）
    is_legacy_data = (
        confidence_score == 0 and (
            not qwen_audit_data or
            (not any(v for v in qwen_audit_data.values() if v is not None and v != 0 and v != False))
        )
    )
    
    if is_legacy_data:
        return {
            "status": "📜 LEGACY_DATA",
            "badge": "📜 舊數據 - 重新處理可獲得Qwen仲裁",
            "details": {
                "reason": "legacy_result_file",
                "note": "此結果由舊版系統生成，不包含Qwen仲裁功能"
            },
            "message": "📜 此為舊版本處理結果，重新上傳PDF可獲得Qwen仲裁功能",
            "css_class": "legacy-data-badge",
            "priority": "INFO"
        }
    
    # 判斷是否真的執行了Qwen仲裁
    actually_executed = (
        executed and 
        qwen_invoked > 0 and 
        learning_record_id is not None
    )
    
    if actually_executed:
        return {
            "status": "🤖 QWEN_EXECUTED",
            "badge": "🎯 已執行 Qwen3-VL-4B 仲裁",
            "details": {
                "confidence_score": f"{confidence_score:.1%}",
                "threshold": "92%", 
                "trigger_reason": triggered_by or "low_confidence",
                "api_calls": qwen_invoked,
                "learning_recorded": bool(learning_record_id),
                "record_id": learning_record_id
            },
            "message": f"✅ 信心分數 {confidence_score:.1%} < 92%，已觸發 Qwen3-VL 仲裁 ({qwen_invoked}次API調用)",
            "css_class": "qwen-executed-badge",
            "priority": "HIGH"
        }
    elif executed and qwen_invoked == 0:
        return {
            "status": "⚠️ QWEN_ATTEMPTED", 
            "badge": "⚠️ Qwen 嘗試執行但未完成",
            "details": {
                "confidence_score": f"{confidence_score:.1%}",
                "api_calls": 0,
                "reason": qwen_audit_data.get("reason", "unknown")
            },
            "message": "Qwen仲裁被觸發但未成功完成API調用",
            "css_class": "qwen-attempted-badge",
            "priority": "MEDIUM"
        }
    elif confidence_score >= 0.92:
        return {
            "status": "✅ HIGH_CONFIDENCE",
            "badge": "✅ 高信心分數 - 無需仲裁", 
            "details": {
                "confidence_score": f"{confidence_score:.1%}",
                "threshold": "92%",
                "reason": "high_confidence"
            },
            "message": f"✅ 信心分數 {confidence_score:.1%} >= 92%，前6步結果可信，跳過Qwen仲裁",
            "css_class": "high-confidence-badge", 
            "priority": "LOW"
        }
    else:
        return {
            "status": "❌ QWEN_UNAVAILABLE",
            "badge": "❌ Qwen 服務不可用",
            "details": {
                "confidence_score": f"{confidence_score:.1%}", 
                "reason": qwen_audit_data.get("reason", "service_unavailable")
            },
            "message": "需要Qwen仲裁但服務不可用",
            "css_class": "qwen-unavailable-badge",
            "priority": "HIGH"
        }


def get_qwen_client():
    """獲取Qwen客戶端實例（lazy loading）"""
    global qwen_client
    if qwen_client is None:
        try:
            config_path = "po_extractor/config/qwen_config.json"
            # 傳遞配置文件路徑而非配置內容
            qwen_client = QwenClient(config_path)
        except Exception as e:
            logger.error(f"Failed to initialize Qwen client: {e}")
            qwen_client = None
    return qwen_client


# Global Qwen client instance
qwen_client = None


if __name__ == '__main__':
    print("=" * 60)
    print("  PO PDF Feature Extractor - Web Interface")
    print(f"  Input:     {os.path.abspath(IMPORT_DIR)}")
    print(f"  Output:    {os.path.abspath(OUTPUT_DIR)}")
    print(f"  Corrected: {os.path.abspath(CORRECTED_DIR)}")
    print(f"  Finish:    {os.path.abspath(FINISH_DIR)}")
    print(f"  Vendors:   {', '.join(ExtractorRegistry.list_vendors())}")
    print("=" * 60)
    print("  🚀 Qwen3-VL Seven-Step Pipeline Ready!")
    print("  Open http://127.0.0.1:5000 in your browser")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=False)
