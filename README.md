# Local PDF-to-Image Converter

A local Flask app that converts each page of a PDF into a high-resolution PNG.
Preview the images in the browser, download them together as a ZIP, or download
an image-only PDF.

## Requirements

- Python 3.10 or newer
- Poppler command-line tools (`pdfinfo` / `pdftoppm`)

The app auto-detects common Poppler install locations on Windows, macOS, and
Linux. If Poppler is installed in a non-standard path, add it to your `PATH` or
update the explicit paths in `ocr_core.py`.

### Linux / macOS install examples

```bash
# Ubuntu / Debian
sudo apt-get update
sudo apt-get install -y poppler-utils

# macOS (Homebrew)
brew install poppler
```

## Run locally

Open a terminal in this folder and run:

```bash
cd "python project"
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

### PostgreSQL setup

The app stores the original PDF in the `uploaded_pdf` column and the generated
image-only PDF in the `result_pdf` column of the `ocr_documents` table. Create a
PostgreSQL database, then set `DATABASE_URL` before starting the app. The app
creates the table automatically on the first successful conversion.

### Current Codespace

PostgreSQL is installed locally in this Codespace. Run these commands to start
PostgreSQL, create the database if needed, and launch the app:

```bash
sudo service postgresql start
createdb ocr_converter   # skip if it already exists
cd "/workspaces/OCR-CONVERTER-PROJRCT/python project"
DATABASE_URL="postgresql://codespace@localhost:5432/ocr_converter" .venv/bin/python app.py
```

Use these settings for the SQLTools connection:
- Host: `localhost`
- Port: `5432`
- Database: `ocr_converter`
- User: `codespace`
- Password: leave blank

Password-free access is restricted to this database and loopback connections
for local development in this Codespace. Do not use this authentication setup
for a public or production database.

For a local PostgreSQL instance, for example:

```bash
createdb ocr_converter
export DATABASE_URL="postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/ocr_converter"
```

On PowerShell, set the connection string for the current terminal session with:

```powershell
$env:DATABASE_URL = "postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/ocr_converter"
```

Keep the connection string private and do not commit it to Git. After setting
`DATABASE_URL`, start the app:

```bash
python app.py
```

On Windows, use the equivalent `.venv\Scripts\python.exe` form instead.

Then open <http://127.0.0.1:5000> in your browser. Keep the terminal open while
using the app; press Ctrl+C there to stop the server.

Uploads are limited to 25 MB. Uploaded PDFs and generated results are stored in
the local `uploads/` and `results/` folders; those documents are excluded from
Git.

This development server is intended for local use, not for public deployment.
