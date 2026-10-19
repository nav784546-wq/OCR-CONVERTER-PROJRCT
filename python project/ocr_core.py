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

WINDOWS_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
WINDOWS_POPPLER_PATH = r"C:\poppler\Library\bin"
COMMON_TESSERACT_PATHS = [
    WINDOWS_TESSERACT_PATH,
    "/usr/local/bin/tesseract",
    "/usr/bin/tesseract",
    "/opt/homebrew/bin/tesseract",
    "/opt/local/bin/tesseract",
]
COMMON_POPPLER_PATHS = [
    WINDOWS_POPPLER_PATH,
    "/usr/local/bin",
    "/usr/bin",
    "/opt/homebrew/bin",
    "/opt/local/bin",
]

POPPLER_PATH = None


def find_windows_poppler_path():
    """Find Poppler's command-line tools, including inside an extracted release folder."""
    required_tools = {"pdfinfo.exe", "pdftoppm.exe"}
    for directory, _, filenames in os.walk(r"C:\poppler"):
        if required_tools.issubset({name.lower() for name in filenames}):
            return directory
    return WINDOWS_POPPLER_PATH


def find_executable(candidate_paths):
    for path in candidate_paths:
        if not path:
            continue
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return shutil.which(os.path.basename(candidate_paths[0])) if candidate_paths else None


def configure_ocr_paths():
    """Detect usable OCR dependencies across OS install layouts."""
    global POPPLER_PATH

    tesseract_path = shutil.which("tesseract")
    if tesseract_path is None:
        tesseract_path = find_executable(COMMON_TESSERACT_PATHS)

    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    if platform.system() == "Windows":
        POPPLER_PATH = find_windows_poppler_path()
        return

    poppler_path = shutil.which("pdftoppm")
    if poppler_path is None:
        for candidate in COMMON_POPPLER_PATHS:
            if os.path.isdir(candidate):
                pdftoppm = os.path.join(candidate, "pdftoppm")
                pdfinfo = os.path.join(candidate, "pdfinfo")
                if os.path.exists(pdftoppm) and os.path.exists(pdfinfo):
                    POPPLER_PATH = candidate
                    break
    else:
        POPPLER_PATH = os.path.dirname(poppler_path)


configure_ocr_paths()


def pdf_to_images(pdf_path, dpi=300):
    """Convert each PDF page into a high-res PIL image."""
    if shutil.which("pdftoppm") is None and POPPLER_PATH is None:
        raise RuntimeError(
            "Poppler utilities (pdftoppm/pdfinfo) were not found. "
            "Install Poppler or add its bin folder to PATH."
        )
    if shutil.which("tesseract") is None and not pytesseract.pytesseract.tesseract_cmd:
        raise RuntimeError(
            "Tesseract OCR was not found. Install Tesseract OCR or add it to PATH."
        )
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
