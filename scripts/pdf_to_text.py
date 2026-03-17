"""
01_extract.py
=============
APF Chatbot — Step 1: PDF to Text Extraction
Smart hybrid approach:
  - ALWAYS extract text columns via PyMuPDF (sorted layout-aware)
  - ALWAYS detect image regions and run OCR on them separately
  - COMBINE text + OCR into one complete page output

This means pages like:
  [ TEXT COLUMN LEFT | INFOGRAPHIC RIGHT ]
  will capture BOTH the text AND the infographic content.

Usage:
    python scripts/01_extract.py

Output:
    data/processed/text/<pdf_name>.txt
    data/processed/text/<pdf_name>_report.txt
"""

import os
import fitz           # PyMuPDF
import pytesseract
from PIL import Image
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────

INPUT_DIR  = "data/raw/web-data/pdf"
OUTPUT_DIR = "data/processed/text"

# DPI for rendering pages/images for OCR — higher = better quality but slower
OCR_DPI = 300

# Minimum pixel area for an image region to be worth OCR-ing
# Filters out tiny logos, icons, decorative elements
MIN_IMAGE_AREA = 15000  # pixels squared (e.g. ~120x120 minimum)

# Tesseract path — only needed on Windows if not in PATH
# Example: r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_PATH = None

# ── SETUP ─────────────────────────────────────────────────────────────────────

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── LAYER 1: Extract text via PyMuPDF (layout-aware) ─────────────────────────

def extract_text_layer(page: fitz.Page) -> str:
    """
    Extract all selectable text from the page using PyMuPDF.
    Sorts text blocks top-to-bottom, left-to-right to preserve
    reading order even on 2-column layouts.
    """
    blocks = page.get_text("blocks")  # each block: (x0,y0,x1,y1,text,block_no,block_type)

    # block_type 0 = text, 1 = image
    text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]

    # Sort top → bottom, then left → right
    text_blocks_sorted = sorted(text_blocks, key=lambda b: (round(b[1] / 20) * 20, b[0]))

    lines = [b[4].strip() for b in text_blocks_sorted]
    return "\n".join(lines).strip()


# ── LAYER 2: Detect image regions + OCR ──────────────────────────────────────

def extract_image_layer(pdf_path: str, page_num: int) -> str:
    """
    Detect all image regions on the page.
    Crop each image region and run OCR on it.
    Returns combined OCR text from all image regions.
    """
    doc = fitz.open(pdf_path)
    pg  = doc[page_num]

    # Get list of image bounding boxes on this page
    image_list = pg.get_images(full=True)

    if not image_list:
        doc.close()
        return ""

    ocr_results = []

    for img_index, img_info in enumerate(image_list):
        xref = img_info[0]  # image xref

        # Get bounding boxes of this image on the page
        img_rects = pg.get_image_rects(xref)

        for rect in img_rects:
            # Check if image region is large enough to be worth OCR
            width  = rect.x1 - rect.x0
            height = rect.y1 - rect.y0
            area   = width * height

            if area < MIN_IMAGE_AREA:
                continue  # skip tiny icons/logos

            # Render just this image region at high DPI
            clip_mat = fitz.Matrix(OCR_DPI / 72, OCR_DPI / 72)
            pix = pg.get_pixmap(matrix=clip_mat, clip=rect)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Run OCR on this cropped region
            try:
                ocr_text = pytesseract.image_to_string(img, lang="eng").strip()
                if ocr_text and len(ocr_text.split()) > 3:  # skip noise
                    ocr_results.append(f"[IMAGE CONTENT]\n{ocr_text}")
            except Exception as e:
                print(f"      [OCR warning] image {img_index+1} on page {page_num+1}: {e}")

    doc.close()
    return "\n\n".join(ocr_results).strip()


# ── LAYER 3: Full page OCR fallback ──────────────────────────────────────────

def extract_fullpage_ocr(pdf_path: str, page_num: int) -> str:
    """
    Render the entire page as an image and run OCR.
    Used as last resort when text layer gives almost nothing.
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        mat = fitz.Matrix(OCR_DPI / 72, OCR_DPI / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        text = pytesseract.image_to_string(img, lang="eng")
        return text.strip()
    except Exception as e:
        print(f"      [Full OCR error] page {page_num+1}: {e}")
        return ""


# ── MAIN PAGE PROCESSOR ───────────────────────────────────────────────────────

def process_page(pdf_path: str, page: fitz.Page, page_num: int) -> dict:
    """
    Process a single page using the smart combined approach:
    1. Extract text layer (always)
    2. Extract image regions via OCR (always)
    3. Combine both
    4. If combined result is still too low → full page OCR fallback
    """
    result = {
        "page_num"    : page_num + 1,
        "text_words"  : 0,
        "image_words" : 0,
        "ocr_fallback": False,
        "content"     : "",
    }

    # Layer 1 — text extraction
    text_content = extract_text_layer(page)
    text_words   = len(text_content.split()) if text_content else 0

    # Layer 2 — image region OCR (always runs)
    image_content = extract_image_layer(pdf_path, page_num)
    image_words   = len(image_content.split()) if image_content else 0

    # Combine text + image content
    parts = []
    if text_content:
        parts.append(text_content)
    if image_content:
        parts.append(image_content)

    combined = "\n\n".join(parts).strip()
    combined_words = len(combined.split()) if combined else 0

    # Layer 3 — full page OCR fallback if combined is still very low
    if combined_words < 20:
        print(f"      → Low content ({combined_words} words) — running full page OCR...")
        fallback = extract_fullpage_ocr(pdf_path, page_num)
        fallback_words = len(fallback.split()) if fallback else 0
        if fallback_words > combined_words:
            combined = fallback
            combined_words = fallback_words
            result["ocr_fallback"] = True

    result["text_words"]  = text_words
    result["image_words"] = image_words
    result["content"]     = combined

    return result


# ── PDF PROCESSOR ─────────────────────────────────────────────────────────────

def process_pdf(pdf_path: str) -> dict:
    """
    Process all pages in a PDF.
    Saves full text + report to output directory.
    """
    pdf_name = Path(pdf_path).stem
    print(f"\n{'='*65}")
    print(f"  {pdf_name}")
    print(f"{'='*65}")

    all_pages     = []
    report_lines  = [
        f"EXTRACTION REPORT: {pdf_name}",
        "=" * 65,
        f"{'Page':<6} {'Text Words':<14} {'Image Words':<14} {'OCR Fallback':<14} {'Total'}",
        "-" * 65,
    ]

    try:
        doc         = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"  Pages: {total_pages}\n")

        for page_num in range(total_pages):
            page = doc[page_num]
            print(f"  Page {page_num+1:2d}/{total_pages} ...", end=" ", flush=True)

            result = process_page(pdf_path, page, page_num)

            total_words = len(result["content"].split()) if result["content"] else 0
            fallback_str = "YES" if result["ocr_fallback"] else "no"

            print(
                f"text={result['text_words']:3d}w  "
                f"image={result['image_words']:3d}w  "
                f"total={total_words:3d}w"
                + (" [OCR fallback]" if result["ocr_fallback"] else "")
            )

            report_lines.append(
                f"{page_num+1:<6} {result['text_words']:<14} "
                f"{result['image_words']:<14} {fallback_str:<14} {total_words}"
            )

            # Build page block for output file
            page_block = (
                f"\n{'─'*60}\n"
                f"PAGE {page_num+1}\n"
                f"{'─'*60}\n"
                f"{result['content']}"
            )
            all_pages.append(page_block)

        doc.close()

    except Exception as e:
        print(f"\n  [ERROR] {e}")
        report_lines.append(f"\nERROR: {e}")

    # ── Save output text file ─────────────────────────────────────────────────
    full_text = "\n".join(all_pages)

    out_txt = os.path.join(OUTPUT_DIR, f"{pdf_name}.txt")
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(f"SOURCE FILE : {pdf_name}\n")
        f.write(f"TOTAL PAGES : {total_pages}\n")
        f.write("=" * 60 + "\n")
        f.write(full_text)

    # ── Save report file ──────────────────────────────────────────────────────
    report_lines.append("-" * 65)
    report_lines.append(f"\nOutput: {out_txt}")
    out_report = os.path.join(OUTPUT_DIR, f"{pdf_name}_report.txt")
    with open(out_report, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\n  ✅  Saved : {out_txt}")
    print(f"  📋  Report: {out_report}")

    return {"pdf": pdf_name, "pages": total_pages, "output": out_txt}


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 65)
    print("  APF PDF Extractor — Step 1 (Smart Hybrid)")
    print("=" * 65)
    print(f"  Input  : {INPUT_DIR}")
    print(f"  Output : {OUTPUT_DIR}")
    print(f"  Strategy: Text layer + Image OCR (always both) + fallback")

    pdf_files = sorted(Path(INPUT_DIR).glob("*.pdf"))

    if not pdf_files:
        print(f"\n❌  No PDFs found in: {INPUT_DIR}")
        return

    print(f"\n  Found {len(pdf_files)} PDF(s):")
    for p in pdf_files:
        print(f"    - {p.name}")

    results = []
    for pdf_path in pdf_files:
        r = process_pdf(str(pdf_path))
        results.append(r)

    # ── Final summary ─────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print("  ✅  ALL DONE")
    print(f"{'='*65}")
    print(f"  PDFs processed : {len(results)}")
    print(f"  Output folder  : {OUTPUT_DIR}")
    print(f"\n  Files created:")
    for r in results:
        print(f"    {r['pdf']}.txt  ({r['pages']} pages)")

    print(f"\n  ➡️   Next step: run  scripts/02_clean.py")
    print()


if __name__ == "__main__":
    main()