# Local PDF OCR Scanner

A local Flask app that extracts text from scanned PDFs with Tesseract. It
provides a plain-text preview and download, plus an image-only PDF download
without an OCR text layer.

## Requirements

- Python 3.10 or newer
- Tesseract OCR
- Poppler command-line tools (`pdfinfo.exe` and `pdftoppm.exe` on Windows)

On Windows, the app expects Tesseract at
`C:\Program Files\Tesseract-OCR\tesseract.exe`. It searches under
`C:\poppler` for the Poppler executables. If you install either tool elsewhere,
update the paths in `ocr_core.py`.

## Run locally on Windows

Open PowerShell in this folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Then open <http://127.0.0.1:5000> in your browser. Keep the PowerShell window
open while using the app; press Ctrl+C there to stop the server.

Uploads are limited to 25 MB. Uploaded PDFs and generated results are stored in
the local `uploads/` and `results/` folders; those documents are excluded from
Git.

This development server is intended for local use, not for public deployment.
