"""Convert PDF pages to images and create OCR text and searchable PDF outputs."""

from io import BytesIO
import os
import platform
import shutil
import zipfile

from pdf2image import convert_from_path
from pypdf import PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import pytesseract

WINDOWS_POPPLER_PATH = r"C:\poppler\Library\bin"
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


def configure_poppler_path():
    """Detect Poppler's location across OS install layouts."""
    global POPPLER_PATH

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


configure_poppler_path()


def pdf_to_images(pdf_path, dpi=300):
    """Convert each PDF page into a high-res PIL image."""
    if shutil.which("pdftoppm") is None and POPPLER_PATH is None:
        raise RuntimeError(
            "Poppler utilities (pdftoppm/pdfinfo) were not found. "
            "Install Poppler or add its bin folder to PATH."
        )
    return convert_from_path(pdf_path, dpi=dpi, poppler_path=POPPLER_PATH)


def build_scanned_pdf(images, output_path):
    """Create a PDF containing only the scanned page images, without OCR text."""
    c = canvas.Canvas(output_path)
    for img in images:
        img_w, img_h = img.size
        c.setPageSize((img_w, img_h))
        c.drawImage(ImageReader(img), 0, 0, width=img_w, height=img_h)
        c.showPage()
    c.save()


def save_page_images(images, output_dir, base_name):
    """Save each rendered page as a PNG and package the images into a ZIP."""
    image_filenames = []
    zip_path = os.path.join(output_dir, f"{base_name}_images.zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for page_number, image in enumerate(images, start=1):
            filename = f"{base_name}_page_{page_number:03}.png"
            image_path = os.path.join(output_dir, filename)
            image.save(image_path, format="PNG")
            archive.write(image_path, arcname=filename)
            image_filenames.append(filename)
    return image_filenames, zip_path


def build_ocr_outputs(images, output_dir, base_name):
    """Create a searchable PDF and extracted text from rendered page images."""
    pdf_path = os.path.join(output_dir, f"{base_name}_ocr.pdf")
    text_path = os.path.join(output_dir, f"{base_name}_ocr.txt")
    pdf_writer = PdfWriter()
    page_text = []

    for page_number, image in enumerate(images, start=1):
        pdf_bytes = pytesseract.image_to_pdf_or_hocr(image, extension="pdf")
        pdf_writer.append(BytesIO(pdf_bytes))
        text = pytesseract.image_to_string(image).strip()
        page_text.append(f"--- Page {page_number} ---\n{text}")

    with open(pdf_path, "wb") as pdf_file:
        pdf_writer.write(pdf_file)
    with open(text_path, "w", encoding="utf-8") as text_file:
        text_file.write("\n\n".join(page_text))

    return pdf_path, text_path


def convert(pdf_path, output_dir):
    """Convert a PDF into page images, an image-only PDF, and OCR outputs."""
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    images = pdf_to_images(pdf_path)
    try:
        image_filenames, zip_path = save_page_images(images, output_dir, base_name)
        pdf_out_path = os.path.join(output_dir, f"{base_name}_scanned.pdf")
        build_scanned_pdf(images, pdf_out_path)
        ocr_pdf_path, text_path = build_ocr_outputs(images, output_dir, base_name)
        return image_filenames, zip_path, pdf_out_path, ocr_pdf_path, text_path, len(images)
    finally:
        for image in images:
            image.close()
