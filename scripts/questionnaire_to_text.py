# -*- coding: utf-8 -*-
"""
questionnaire_to_text.py
========================
APF Nancy Chatbot - Extract text from Questionnaire PDFs

What it does:
  - Reads GAQ-P and GAQ-PP PDF files from data/raw/Questionare_data/
  - Extracts text using PyMuPDF
  - Saves extracted text to data/processed/questionnaires/text/

Usage:
    python scripts/questionnaire_to_text.py

Input:  data/raw/Questionare_data/*.pdf
Output: data/processed/questionnaires/text/*.txt
"""

import sys
from pathlib import Path
import fitz  # PyMuPDF

# Optional OCR fallback
try:
    import pytesseract
    from PIL import Image
    import io
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# ── CONFIG ────────────────────────────────────────────────────────────────────
INPUT_DIR  = "data/raw/Questionare_data"
OUTPUT_DIR = "data/processed/questionnaires/text"

# Expected files
EXPECTED_FILES = [
    "CSEP-PATH_GAQ_P_UK_version.pdf",        # GAQ-P pregnancy
    "CSEP-PATH_GAQ_P_HCP_UK__230123.pdf",    # GAQ-P HCP form
    "CSEP-PATH_GAQ_PP_Guidelines.pdf",       # GAQ-PP postpartum
]

# ── HELPERS ───────────────────────────────────────────────────────────────────

def extract_text_pymupdf(pdf_path: str) -> str:
    """Extract text from PDF using PyMuPDF page by page."""
    doc   = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            pages.append(f"--- PAGE {i+1} ---\n{text.strip()}")
    doc.close()
    return "\n\n".join(pages)


def extract_text_ocr(pdf_path: str) -> str:
    """Extract text using OCR as fallback."""
    if not OCR_AVAILABLE:
        return ""
    doc   = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        pix  = page.get_pixmap(dpi=300)
        img  = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img)
        if text.strip():
            pages.append(f"--- PAGE {i+1} ---\n{text.strip()}")
    doc.close()
    return "\n\n".join(pages)


def process_pdf(pdf_path: str, output_dir: str) -> dict:
    """Process a single questionnaire PDF."""
    pdf_name = Path(pdf_path).stem
    out_file = Path(output_dir) / f"{pdf_name}.txt"

    # Skip if already processed
    if out_file.exists():
        return {"status": "skipped", "file": pdf_name}

    # Try PyMuPDF first
    text   = extract_text_pymupdf(pdf_path)
    method = "pymupdf"

    # Fall back to OCR if text too short
    if len(text.split()) < 50 and OCR_AVAILABLE:
        text   = extract_text_ocr(pdf_path)
        method = "ocr"

    if not text.strip():
        return {"status": "failed", "file": pdf_name}

    # Save to txt file
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(text)

    return {
        "status"    : "success",
        "file"      : pdf_name,
        "method"    : method,
        "word_count": len(text.split()),
        "out_file"  : str(out_file),
    }


def main():
    print("\n" + "="*60)
    print("  APF Questionnaire PDF → Text Extractor")
    print("="*60)
    print(f"  Input  : {INPUT_DIR}")
    print(f"  Output : {OUTPUT_DIR}")
    print(f"  OCR    : {'available ✅' if OCR_AVAILABLE else 'not available ⚠️'}")

    # Check input directory
    if not Path(INPUT_DIR).exists():
        print(f"\n[ERROR] Input folder not found: {INPUT_DIR}")
        print(f"  Please create: data/raw/Questionare_data/")
        print(f"  And add these files:")
        for f in EXPECTED_FILES:
            print(f"    - {f}")
        sys.exit(1)

    # Create output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Get all PDF files
    pdf_files = list(Path(INPUT_DIR).glob("*.pdf"))
    if not pdf_files:
        print(f"\n[ERROR] No PDF files found in {INPUT_DIR}")
        sys.exit(1)

    # Check for expected files
    print(f"\n  Checking expected files:")
    found_files = [f.name for f in pdf_files]
    for expected in EXPECTED_FILES:
        status = "✅" if expected in found_files else "❌ MISSING"
        print(f"    {status} {expected}")

    print(f"\n  Found {len(pdf_files)} PDF files")
    print(f"\n  {'File':<55} {'Status':>8} {'Words':>6}")
    print(f"  {'-'*71}")

    # Process each PDF
    success = 0
    skipped = 0
    failed  = 0

    for pdf_file in sorted(pdf_files):
        result = process_pdf(str(pdf_file), OUTPUT_DIR)
        name   = result["file"][:53]

        if result["status"] == "success":
            success += 1
            words   = result.get("word_count", 0)
            method  = result.get("method", "")
            print(f"  {name:<55} {'✅':>8} {words:>6}")
        elif result["status"] == "skipped":
            skipped += 1
            print(f"  {name:<55} {'⏭️ skip':>8}")
        else:
            failed += 1
            print(f"  {name:<55} {'❌ fail':>8}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  ✅ EXTRACTION COMPLETE!")
    print(f"{'='*60}")
    print(f"  Success : {success}")
    print(f"  Skipped : {skipped}")
    print(f"  Failed  : {failed}")
    print(f"  Output  : {OUTPUT_DIR}")
    print(f"\n  Next step → run:")
    print(f"  python scripts/questionnaire_to_json.py")


if __name__ == "__main__":
    main()
