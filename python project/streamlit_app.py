"""Streamlit interface for the PDF OCR converter."""

import os
import tempfile

import streamlit as st
from werkzeug.utils import secure_filename

import ocr_core


MAX_UPLOAD_BYTES = 100 * 1024 * 1024

st.set_page_config(page_title="PDF OCR Converter", page_icon="📄")
st.title("PDF OCR Converter")
st.write(
    "Upload a PDF to create a searchable OCR PDF, an image-only PDF, "
    "extracted text, and a ZIP of page images."
)

uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"],
    max_upload_size=100,
)

if st.button("Convert PDF", disabled=uploaded_file is None):
    st.session_state.pop("ocr_result", None)
    if uploaded_file is None:
        st.error("Please choose a PDF file.")
    elif uploaded_file.size > MAX_UPLOAD_BYTES:
        st.error("The upload is larger than the 100 MB limit.")
    else:
        pdf_bytes = uploaded_file.getvalue()
        if not pdf_bytes.startswith(b"%PDF-"):
            st.error("Please upload a valid PDF file.")
        else:
            source_name = os.path.splitext(
                secure_filename(uploaded_file.name.replace("\\", "/"))
            )[0] or "document"
            try:
                with st.spinner("Converting pages and recognizing text..."):
                    with tempfile.TemporaryDirectory() as temp_dir:
                        pdf_path = os.path.join(temp_dir, f"{source_name}.pdf")
                        output_dir = os.path.join(temp_dir, "results")
                        with open(pdf_path, "wb") as pdf_file:
                            pdf_file.write(pdf_bytes)

                        (
                            image_filenames,
                            zip_path,
                            scanned_pdf_path,
                            ocr_pdf_path,
                            text_path,
                            page_count,
                        ) = ocr_core.convert(pdf_path, output_dir)

                        with open(zip_path, "rb") as result_file:
                            images_zip = result_file.read()
                        with open(scanned_pdf_path, "rb") as result_file:
                            scanned_pdf = result_file.read()
                        with open(ocr_pdf_path, "rb") as result_file:
                            searchable_pdf = result_file.read()
                        with open(text_path, "rb") as result_file:
                            extracted_text = result_file.read()

                st.session_state["ocr_result"] = {
                    "page_count": page_count,
                    "image_count": len(image_filenames),
                    "images_zip": images_zip,
                    "zip_name": os.path.basename(zip_path),
                    "scanned_pdf": scanned_pdf,
                    "scanned_pdf_name": os.path.basename(scanned_pdf_path),
                    "searchable_pdf": searchable_pdf,
                    "searchable_pdf_name": os.path.basename(ocr_pdf_path),
                    "text": extracted_text,
                    "text_name": os.path.basename(text_path),
                }
            except Exception as error:
                st.error(f"PDF conversion or OCR failed: {error}")

result = st.session_state.get("ocr_result")
if result:
    st.success(
        f"Converted {result['page_count']} pages into "
        f"{result['image_count']} page images."
    )
    download_columns = st.columns(2)
    with download_columns[0]:
        st.download_button(
            "Download page images (.zip)",
            data=result["images_zip"],
            file_name=result["zip_name"],
            mime="application/zip",
            use_container_width=True,
        )
        st.download_button(
            "Download image-only PDF",
            data=result["scanned_pdf"],
            file_name=result["scanned_pdf_name"],
            mime="application/pdf",
            use_container_width=True,
        )
    with download_columns[1]:
        st.download_button(
            "Download searchable OCR PDF",
            data=result["searchable_pdf"],
            file_name=result["searchable_pdf_name"],
            mime="application/pdf",
            use_container_width=True,
        )
        st.download_button(
            "Download extracted text",
            data=result["text"],
            file_name=result["text_name"],
            mime="text/plain",
            use_container_width=True,
        )
    with st.expander("Preview extracted text"):
        st.text(result["text"].decode("utf-8"))
