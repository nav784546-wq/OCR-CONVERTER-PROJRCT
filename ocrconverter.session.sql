 CREATE DATABASE ocr_converter;
 CREATE TABLE IF NOT EXISTS ocr_documents (
    id TEXT PRIMARY KEY,
    source_filename TEXT NOT NULL,
    uploaded_pdf BYTEA NOT NULL,
    result_pdf BYTEA NOT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
insert 