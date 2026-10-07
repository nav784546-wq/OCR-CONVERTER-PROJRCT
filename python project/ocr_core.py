"""
Core OCR pipeline — same logic as the original CLI script, refactored
into importable functions so the Flask web app can call it directly.

PIPELINE:
  PDF page --> image (pdf2image + poppler)
            --> plain-text OCR (pytesseract)
            --> plain text (.txt)
            --> page images assembled into a scanned PDF (reportlab)
"""

import os
import platform
import shutil
from pdf2image import convert_from_path
import pytesseract
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# --- Tool path setup ---
# On Windows, Tesseract/Poppler often aren't on PATH, so we point to the
# typical install locations directly. On macOS/Linux they're normally
# already on PATH (via brew/apt), so we leave them alone unless missing.
WINDOWS_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
WINDOWS_POPPLER_PATH = r"C:\poppler\Library\bin"

POPPLER_PATH = None  # None = pdf2image looks on system PATH


def find_windows_poppler_path():
    """Find Poppler's command-line tools, including inside an extracted release folder."""
    required_tools = {"pdfinfo.exe", "pdftoppm.exe"}
    for directory, _, filenames in os.walk(r"C:\poppler"):
        if required_tools.issubset({name.lower() for name in filenames}):
            return directory
    return WINDOWS_POPPLER_PATH


if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = WINDOWS_TESSERACT_PATH
    POPPLER_PATH = find_windows_poppler_path()
elif shutil.which("tesseract") is None:
    # Fallback if tesseract isn't found on PATH even on Mac/Linux —
    # edit this path to wherever `which tesseract` points on your machine.
    pass


def pdf_to_images(pdf_path, dpi=300):
    """Convert each PDF page into a high-res PIL image."""
    return convert_from_path(pdf_path, dpi=dpi, poppler_path=POPPLER_PATH)


def extract_plain_text(images):
    """Run OCR and return text and word counts for each page."""
    full_text = []
    page_word_counts = []
    for i, img in enumerate(images, start=1):
        text = pytesseract.image_to_string(img)
        full_text.append(f"--- Page {i} ---\n{text.strip()}\n")
        page_word_counts.append(len(text.split()))
    return "\n".join(full_text), page_word_counts


def build_scanned_pdf(images, output_path):
    """Create a PDF containing only the scanned page images, without OCR text."""
    c = canvas.Canvas(output_path)
    for img in images:
        img_w, img_h = img.size
        c.setPageSize((img_w, img_h))
        c.drawImage(ImageReader(img), 0, 0, width=img_w, height=img_h)
        c.showPage()
    c.save()


def convert(pdf_path, output_dir):
    """Run the full pipeline on one PDF file. Returns (txt_path, pdf_path, page_count, word_counts)."""
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]

    images = pdf_to_images(pdf_path)

    text, word_counts = extract_plain_text(images)
    txt_path = os.path.join(output_dir, f"{base_name}_ocr.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    pdf_out_path = os.path.join(output_dir, f"{base_name}_scanned.pdf")
    build_scanned_pdf(images, pdf_out_path)

    return txt_path, pdf_out_path, len(images), word_counts, text
