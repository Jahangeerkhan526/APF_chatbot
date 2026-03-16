import os
import fitz  # PyMuPDF

INPUT_FOLDER = "data/raw/web-data/pdf"
OUTPUT_FOLDER = "data/processed/text"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = []

    for page in doc:
        text = page.get_text()
        full_text.append(text)

    doc.close()
    return "\n".join(full_text)

def process_all_pdfs():
    for filename in os.listdir(INPUT_FOLDER):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_FOLDER, filename)
            print(f"Processing: {filename}")

            extracted_text = extract_text_from_pdf(pdf_path)

            txt_name = os.path.splitext(filename)[0] + ".txt"
            txt_path = os.path.join(OUTPUT_FOLDER, txt_name)

            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)

            print(f"Saved: {txt_path}")

if __name__ == "__main__":
    process_all_pdfs()