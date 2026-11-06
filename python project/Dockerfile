FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends poppler-utils tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt flask-requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -r flask-requirements.txt

COPY . .

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} app:app"]
