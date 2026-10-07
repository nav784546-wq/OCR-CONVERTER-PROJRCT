"""
Flask web app for the PDF -> OCR converter.

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
import ocr_core

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB upload limit


def get_display_name(filename):
    return os.path.splitext(os.path.basename(filename))[0]


def is_pdf(file):
    """Identify a PDF from its signature, not its filename extension."""
    signature = file.stream.read(5)
    file.stream.seek(0)
    return signature == b"%PDF-"


def is_pdf(file):
    """Identify a PDF from its signature, not its filename extension."""
    signature = file.stream.read(5)
    file.stream.seek(0)
    return signature == b"%PDF-"

@app.route("/style.css")
def stylesheet():
    return send_from_directory(BASE_DIR, "style.css")


@app.route("/script.js")
def javascript():
    return send_from_directory(BASE_DIR, "script.js")

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")





@app.route("/convert", methods=["POST"])
def convert():
    if "pdf_file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["pdf_file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a .pdf file."}), 400
    if not is_pdf(file):
        return jsonify({"error": "Please upload a valid PDF file."}), 400

    # unique id per job so concurrent users / repeat uploads don't collide
    job_id = uuid.uuid4().hex[:10]
    job_upload_dir = os.path.join(UPLOAD_DIR, job_id)
    job_result_dir = os.path.join(RESULTS_DIR, job_id)
    os.makedirs(job_upload_dir, exist_ok=True)

    # pdf2image works reliably with a .pdf suffix even when the upload lacks one.
    upload_name = os.path.basename(file.filename)
    if not upload_name.lower().endswith(".pdf"):
        upload_name = f"{upload_name or 'document'}.pdf"
    pdf_path = os.path.join(job_upload_dir, file.filename)
    pdf_path = os.path.join(job_upload_dir, upload_name)
    file.save(pdf_path)
    source_filename = get_display_name(file.filename)

    try:
        txt_path, pdf_out_path, page_count, word_counts, text = ocr_core.convert(
            pdf_path, job_result_dir
        )
    except Exception as e:
        return jsonify({"error": f"OCR processing failed: {e}"}), 500

    return jsonify(
        {
            "job_id": job_id,
            "page_count": page_count,
            "word_counts": word_counts,
            "total_words": sum(word_counts),
            "preview": text[:2000],
            "txt_filename": os.path.basename(txt_path),
            "pdf_filename": os.path.basename(pdf_out_path),
            "source_filename": source_filename,
        }
    )


@app.route("/download/<job_id>/<filename>")
def download(job_id, filename):
    job_result_dir = os.path.join(RESULTS_DIR, job_id)
    return send_from_directory(job_result_dir, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
