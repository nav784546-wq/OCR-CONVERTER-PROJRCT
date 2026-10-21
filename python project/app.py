"""
Flask web app for the PDF-to-image converter.

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

import io
import os
import uuid
import psycopg
from flask import Flask, abort, request, jsonify, send_file, send_from_directory
import ocr_core

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB upload limit


def get_display_name(filename):
    return os.path.splitext(os.path.basename(filename))[0]


def is_pdf(file):
    """Identify a PDF from its signature, not its filename extension."""
    signature = file.stream.read(5)
    file.stream.seek(0)
    return signature == b"%PDF-"


def get_database_url():
    database_url = os.environ.get("postgresql://codespace@localhost:5432/ocr_converter")
    if not database_url:
        raise RuntimeError("postgresql://codespace@localhost:5432/ocr_converter environment variable is not set.")
    return database_url

def save_document(job_id, source_filename, uploaded_pdf, result_pdf):
    with psycopg.connect(get_database_url()) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ocr_documents (
                id TEXT PRIMARY KEY,
                source_filename TEXT NOT NULL,
                uploaded_pdf BYTEA NOT NULL,
                result_pdf BYTEA NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            INSERT INTO ocr_documents
                (id, source_filename, uploaded_pdf, result_pdf)
            VALUES (%s, %s, %s, %s)
            """,
            (job_id, source_filename, uploaded_pdf, result_pdf),
        )


def get_result_pdf(job_id):
    with psycopg.connect(get_database_url()) as connection:
        row = connection.execute(
            "SELECT result_pdf FROM ocr_documents WHERE id = %s",
            (job_id,),
        ).fetchone()
    return row[0] if row else None


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
    upload_name = os.path.basename(file.filename) or "document.pdf"
    if not upload_name.lower().endswith(".pdf"):
        upload_name = f"{upload_name}.pdf"
    pdf_path = os.path.join(job_upload_dir, upload_name)
    file.save(pdf_path)
    source_filename = get_display_name(file.filename)

    try:
        (
            image_filenames,
            zip_path,
            pdf_out_path,
            ocr_pdf_path,
            text_path,
            page_count,
        ) = ocr_core.convert(
            pdf_path, job_result_dir
        )
    except Exception as e:
        app.logger.exception("Could not convert or OCR the PDF")
        return jsonify({"error": f"PDF conversion or OCR failed: {e}"}), 500

    try:
        with open(pdf_path, "rb") as uploaded_pdf_file:
            uploaded_pdf = uploaded_pdf_file.read()
        with open(pdf_out_path, "rb") as result_pdf_file:
            result_pdf = result_pdf_file.read()
        save_document(job_id, source_filename, uploaded_pdf, result_pdf)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except psycopg.Error:
        app.logger.exception("Could not save converted documents to PostgreSQL")
        return jsonify(
            {
                "error": (
                    "Could not save the converted documents to PostgreSQL. "
                    "Check the database configuration and server log."
                )
            }
        ), 500

    return jsonify(
        {
            "job_id": job_id,
            "page_count": page_count,
            "image_filenames": image_filenames,
            "zip_filename": os.path.basename(zip_path),
            "pdf_filename": os.path.basename(pdf_out_path),
            "ocr_pdf_filename": os.path.basename(ocr_pdf_path),
            "text_filename": os.path.basename(text_path),
            "source_filename": source_filename,
        }
    )


@app.route("/download/<job_id>/<filename>")
def download(job_id, filename):
    if filename.endswith("_scanned.pdf"):
        try:
            result_pdf = get_result_pdf(job_id)
        except RuntimeError as e:
            return jsonify({"error": str(e)}), 500
        except psycopg.Error:
            app.logger.exception("Could not retrieve scanned PDF from PostgreSQL")
            return jsonify(
                {
                    "error": (
                        "Could not retrieve the scanned PDF from PostgreSQL. "
                        "Check the database configuration and server log."
                    )
                }
            ), 500
        if result_pdf is None:
            abort(404)
        return send_file(
            io.BytesIO(result_pdf),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    job_result_dir = os.path.join(RESULTS_DIR, job_id)
    return send_from_directory(job_result_dir, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
