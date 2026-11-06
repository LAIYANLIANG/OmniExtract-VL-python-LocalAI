"""
PO PDF Feature Extractor - Learning CLI

Usage:
    py -m po_extractor.learn                    # Learn from corrected/ folder
    py -m po_extractor.learn --generate         # Also generate new extractors
    py -m po_extractor.learn --status           # Show learning status
    py -m po_extractor.learn --show-patterns    # Display learned patterns

Workflow:
    1. Run extraction:   py -m po_extractor.main
    2. Copy JSON to corrected/<Vendor>/ and fix incorrect fields
    3. Run learning:     py -m po_extractor.learn
    4. Re-run extraction for improved results
"""
import argparse
import os
import sys
import json
import logging

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_DIR = os.path.dirname(_PACKAGE_DIR)
if _WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, _WORKSPACE_DIR)

from po_extractor.config import (
    DEFAULT_CORRECTED_DIR, DEFAULT_OUTPUT_DIR,
    LEARNED_PATTERNS_PATH, AUTO_EXTRACTOR_THRESHOLD
)
from po_extractor.pipeline.pattern_learner import learn_from_corrections, load_learned_patterns
from po_extractor.pipeline.extractor_generator import check_and_generate_extractors

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def show_status():
    """Show current learning status."""
    print("=" * 60)
    print("  PO Extractor - Learning Status")
    print("=" * 60)

    # Corrected files
    corrected_dir = DEFAULT_CORRECTED_DIR
    if os.path.exists(corrected_dir):
        total = 0
        for vendor in sorted(os.listdir(corrected_dir)):
            vp = os.path.join(corrected_dir, vendor)
            if os.path.isdir(vp):
                count = len([f for f in os.listdir(vp) if f.endswith('.json')])
                if count > 0:
                    threshold_note = ""
                    if count >= AUTO_EXTRACTOR_THRESHOLD:
                        threshold_note = " ✓ 可自動生成 extractor"
                    else:
                        need = AUTO_EXTRACTOR_THRESHOLD - count
                        threshold_note = f" (還需 {need} 份才可自動生成)"
                    print(f"  corrected/{vendor}/: {count} 份{threshold_note}")
                    total += count
        if total == 0:
            print(f"  corrected/: (空)")
        else:
            print(f"  共計: {total} 份校正檔案")
    else:
        print(f"  corrected/: 不存在 (請先建立)")
        print(f"  路徑: {corrected_dir}")

    print()

    # Learned patterns
    if os.path.exists(LEARNED_PATTERNS_PATH):
        patterns = load_learned_patterns()
        vendor_count = sum(1 for k in patterns if not k.startswith('_'))
        total_patterns = sum(
            len(pats) for vid, fields in patterns.items()
            if not vid.startswith('_')
            for pats in fields.values()
        )
        print(f"  learned_patterns.json: {vendor_count} 供應商, {total_patterns} 個 patterns")
        for vid in sorted(k for k in patterns if not k.startswith('_')):
            field_count = len(patterns[vid])
            sample_max = max(
                (p.get('samples', 0) for pats in patterns[vid].values() for p in pats),
                default=0
            )
            print(f"    {vid}: {field_count} 欄位, 最高 {sample_max} 樣本")
    else:
        print("  learned_patterns.json: 尚未建立")

    print()
    print("  使用方式:")
    print("    1. 從 output_doc/<Vendor>/ 複製 JSON 到 corrected/<Vendor>/")
    print("    2. 在 corrected/ 中的 JSON 裡修正錯誤欄位")
    print("    3. 執行: py -m po_extractor.learn")
    print("    4. 重新處理 PDF 即可使用學習成果")
    print("=" * 60)


def show_patterns():
    """Display all learned patterns."""
    if not os.path.exists(LEARNED_PATTERNS_PATH):
        print("No learned patterns yet.")
        return

    patterns = load_learned_patterns()
    for vid in sorted(k for k in patterns if not k.startswith('_')):
        print(f"\n{'='*60}")
        print(f"  Vendor: {vid}")
        print(f"{'='*60}")
        for field_path, pat_list in sorted(patterns[vid].items()):
            for pat in pat_list:
                print(f"  {field_path}:")
                print(f"    Pattern:  {pat['pattern'][:80]}")
                print(f"    Label:    {pat.get('label', '')}")
                print(f"    Samples:  {pat.get('samples', 0)}")
                print(f"    Updated:  {pat.get('last_updated', '')}")
                print()

    # Keywords
    if '_keywords' in patterns:
        print(f"\n{'='*60}")
        print(f"  Learned Keywords (for classification)")
        print(f"{'='*60}")
        for vid, kws in sorted(patterns['_keywords'].items()):
            print(f"  {vid}: {kws}")


def main():
    parser = argparse.ArgumentParser(
        description='PO Extractor - Pattern Learning from Corrections'
    )
    parser.add_argument('--status', '-s', action='store_true',
                        help='Show learning status')
    parser.add_argument('--show-patterns', '-p', action='store_true',
                        help='Display all learned patterns')
    parser.add_argument('--generate', '-g', action='store_true',
                        help='Also generate extractors for vendors with enough samples')
    parser.add_argument('--corrected', '-c', default=DEFAULT_CORRECTED_DIR,
                        help=f'Corrected JSON directory (default: corrected/)')
    parser.add_argument('--output', '-o', default=DEFAULT_OUTPUT_DIR,
                        help=f'Original output directory (default: output_doc/)')

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.show_patterns:
        show_patterns()
        return

    # Ensure corrected directory exists
    if not os.path.exists(args.corrected):
        os.makedirs(args.corrected, exist_ok=True)
        print(f"Created: {args.corrected}")
        print(f"\n請將修正後的 JSON 放入 corrected/<Vendor>/ 資料夾:")
        print(f"  1. 從 output_doc/<Vendor>/ 複製 JSON 到 corrected/<Vendor>/")
        print(f"  2. 修正 JSON 中的錯誤欄位")
        print(f"  3. 重新執行: py -m po_extractor.learn")
        return

    print("=" * 60)
    print("  PO Extractor - Learning from Corrections")
    print("=" * 60)
    print(f"  Corrected: {os.path.abspath(args.corrected)}")
    print(f"  Original:  {os.path.abspath(args.output)}")
    print("=" * 60)

    # Run learning
    stats = learn_from_corrections(args.corrected, args.output)

    if stats.get('files_processed', 0) == 0:
        print("\n沒有找到可學習的校正檔案。")
        print(f"請將修正後的 JSON 放入: {os.path.abspath(args.corrected)}/<Vendor>/")
        return

    # Optionally generate extractors
    if args.generate:
        print(f"\n--- 檢查是否可自動生成 extractor (門檻: {AUTO_EXTRACTOR_THRESHOLD} 份) ---")
        generated = check_and_generate_extractors(args.corrected)
        if generated:
            print(f"\n✓ 已自動生成 {len(generated)} 個 extractor: {generated}")
            print("  下次執行時將自動使用新的 extractor。")
        else:
            print("  目前沒有供應商達到自動生成門檻。")

    print("\n✓ 學習完成！下次抽取時將自動套用學習成果。")


if __name__ == '__main__':
    main()
