import os
import io
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

INPUT_FOLDER = "data/raw/web-data/pdf"
OUTPUT_FOLDER = "data/processed/text_better"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def extract_direct_text(page):
    """Extract selectable PDF text."""
    text = page.get_text("text")
    return text.strip()


def preprocess_image_for_ocr(image):
    """
    Improve image for OCR:
    - grayscale
    - enlarge
    - increase contrast
    - sharpen
    - threshold
    """
    image = image.convert("L")  # grayscale

    # enlarge image
    new_size = (image.width * 2, image.height * 2)
    image = image.resize(new_size)

    # increase contrast
    image = ImageEnhance.Contrast(image).enhance(2.0)

    # sharpen
    image = image.filter(ImageFilter.SHARPEN)

    # threshold to black/white
    image = image.point(lambda x: 0 if x < 160 else 255, "1")

    return image


def page_to_image(page, zoom=3):
    """Render PDF page to image."""
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix)
    img_bytes = pix.tobytes("png")
    image = Image.open(io.BytesIO(img_bytes))
    return image


def ocr_image(image):
    """Run Tesseract OCR on PIL image."""
    config = "--psm 6"
    text = pytesseract.image_to_string(image, config=config)
    return text.strip()


def extract_ocr_full_page(page):
    """OCR on the full page after preprocessing."""
    image = page_to_image(page, zoom=3)
    processed = preprocess_image_for_ocr(image)
    return ocr_image(processed)


def extract_ocr_regions(page):
    """
    OCR on likely infographic regions.
    We crop right side and top/bottom areas because your PDFs
    often place infographic posters there.
    """
    image = page_to_image(page, zoom=3)
    width, height = image.size

    regions = []

    # right half
    regions.append(image.crop((width // 2, 0, width, height)))

    # top-right quadrant
    regions.append(image.crop((width // 2, 0, width, height // 2)))

    # bottom-right quadrant
    regions.append(image.crop((width // 2, height // 2, width, height)))

    # lower full width area (sometimes infographic footer labels are there)
    regions.append(image.crop((0, int(height * 0.65), width, height)))

    texts = []
    for idx, region in enumerate(regions, start=1):
        processed = preprocess_image_for_ocr(region)
        text = ocr_image(processed)
        if text:
            texts.append(f"[REGION OCR {idx}]\n{text}")

    return "\n\n".join(texts).strip()


def combine_texts(direct_text, full_ocr_text, region_ocr_text):
    parts = []

    if direct_text:
        parts.append("[DIRECT PDF TEXT]\n" + direct_text)

    if full_ocr_text:
        parts.append("[FULL PAGE OCR]\n" + full_ocr_text)

    if region_ocr_text:
        parts.append("[REGION OCR]\n" + region_ocr_text)

    return "\n\n".join(parts).strip()


def process_pdf(pdf_path, output_path):
    doc = fitz.open(pdf_path)
    all_pages = []

    for i, page in enumerate(doc):
        page_num = i + 1
        print(f"  Processing page {page_num}...")

        direct_text = extract_direct_text(page)
        full_ocr_text = extract_ocr_full_page(page)
        region_ocr_text = extract_ocr_regions(page)

        combined_text = combine_texts(direct_text, full_ocr_text, region_ocr_text)

        page_block = f"\n--- PAGE {page_num} ---\n{combined_text}\n"
        all_pages.append(page_block)

    doc.close()

    final_text = "\n".join(all_pages)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_text)


def process_all_pdfs():
    for filename in os.listdir(INPUT_FOLDER):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_FOLDER, filename)
            txt_name = os.path.splitext(filename)[0] + ".txt"
            output_path = os.path.join(OUTPUT_FOLDER, txt_name)

            print(f"\nProcessing PDF: {filename}")
            process_pdf(pdf_path, output_path)
            print(f"Saved TXT: {output_path}")


if __name__ == "__main__":
    process_all_pdfs()