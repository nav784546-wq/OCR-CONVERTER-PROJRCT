"""Convert PDF pages to images and create OCR text and searchable PDF outputs."""

import os
import platform
import shutil
import tempfile
import zipfile

from pdf2image import convert_from_path, pdfinfo_from_path
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


def pdf_to_images(pdf_path, dpi=300, first_page=None, last_page=None):
    """Convert a selected range of PDF pages into high-res PIL images."""
    if shutil.which("pdftoppm") is None and POPPLER_PATH is None:
        raise RuntimeError(
            "Poppler utilities (pdftoppm/pdfinfo) were not found. "
            "Install Poppler or add its bin folder to PATH."
        )
    return convert_from_path(
        pdf_path,
        dpi=dpi,
        first_page=first_page,
        last_page=last_page,
        poppler_path=POPPLER_PATH,
    )


def convert(pdf_path, output_dir):
    """Convert a PDF page-by-page into images and OCR outputs."""
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    page_count = pdfinfo_from_path(pdf_path, poppler_path=POPPLER_PATH)["Pages"]
    image_filenames = []
    zip_path = os.path.join(output_dir, f"{base_name}_images.zip")
    pdf_out_path = os.path.join(output_dir, f"{base_name}_scanned.pdf")
    ocr_pdf_path = os.path.join(output_dir, f"{base_name}_ocr.pdf")
    text_path = os.path.join(output_dir, f"{base_name}_ocr.txt")
    pdf_writer = PdfWriter()

    try:
        with tempfile.TemporaryDirectory(dir=output_dir) as temp_dir:
            with (
                zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive,
                open(pdf_out_path, "wb") as scanned_pdf_file,
                open(text_path, "w", encoding="utf-8") as text_file,
            ):
                scanned_pdf = canvas.Canvas(scanned_pdf_file)

                for page_number in range(1, page_count + 1):
                    images = pdf_to_images(
                        pdf_path,
                        first_page=page_number,
                        last_page=page_number,
                    )
                    if len(images) != 1:
                        for image in images:
                            image.close()
                        raise RuntimeError(
                            f"Expected one rendered image for page {page_number}, "
                            f"but got {len(images)}."
                        )

                    image = images[0]
                    try:
                        filename = f"{base_name}_page_{page_number:03}.png"
                        image_path = os.path.join(output_dir, filename)
                        image.save(image_path, format="PNG")
                        archive.write(image_path, arcname=filename)
                        image_filenames.append(filename)

                        img_w, img_h = image.size
                        scanned_pdf.setPageSize((img_w, img_h))
                        scanned_pdf.drawImage(
                            ImageReader(image), 0, 0, width=img_w, height=img_h
                        )
                        scanned_pdf.showPage()

                        page_pdf_path = os.path.join(
                            temp_dir, f"page_{page_number:06}.pdf"
                        )
                        with open(page_pdf_path, "wb") as page_pdf_file:
                            page_pdf_file.write(
                                pytesseract.image_to_pdf_or_hocr(
                                    image, extension="pdf"
                                )
                            )
                        pdf_writer.append(page_pdf_path)

                        if page_number > 1:
                            text_file.write("\n\n")
                        text_file.write(
                            f"--- Page {page_number} ---\n"
                            f"{pytesseract.image_to_string(image).strip()}"
                        )
                    finally:
                        image.close()

                scanned_pdf.save()

            with open(ocr_pdf_path, "wb") as ocr_pdf_file:
                pdf_writer.write(ocr_pdf_file)
    finally:
        pdf_writer.close()

    return (
        image_filenames,
        zip_path,
        pdf_out_path,
        ocr_pdf_path,
        text_path,
        page_count,
    )
