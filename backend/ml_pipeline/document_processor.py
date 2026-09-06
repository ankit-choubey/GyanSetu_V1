"""
ML-002 — Document extraction: PDF and PPTX -> plain text, now enhanced
with table extraction and OCR fallback for scanned PDF pages.

BACKWARD COMPATIBILITY: process_document(file_path) -> str preserves the
existing public API signature and return type. For documents containing
detected tables, the enhanced implementation now includes serialized
table content in the returned text — the output is not byte-for-byte
identical to the pre-enhancement version in that case. For documents
with no detected tables and no OCR trigger, output is unchanged.

New, additive capability: process_document_structured(file_path) ->
list[dict], giving per-page text/tables/content-type for downstream
MCQ/RAG use. process_document() is now implemented in terms of this.

Optional dependencies (pdfplumber for tables, pytesseract+Pillow for
OCR) degrade gracefully if not installed — table/OCR features are
skipped in that case.
"""
from __future__ import annotations

import os

import pymupdf as fitz  # PyMuPDF's current import name
from pptx import Presentation

SUPPORTED_EXTENSIONS = {".pdf", ".pptx"}

# A page with fewer than this many extractable characters is treated as
# "likely scanned" and becomes an OCR candidate. Chosen to be well below
# a normal text paragraph's length, so real text pages never trigger OCR.
OCR_TEXT_THRESHOLD = 20

# --- Optional dependencies: table extraction ---------------------------
try:
    import pdfplumber
    _PDFPLUMBER_AVAILABLE = True
except ImportError:
    _PDFPLUMBER_AVAILABLE = False

# --- Optional dependencies: OCR -----------------------------------------
try:
    import pytesseract
    from PIL import Image
    import io
    _OCR_AVAILABLE = True
except ImportError:
    _OCR_AVAILABLE = False


def _extract_pdf_page_tables(file_path: str, page_number: int) -> list[list[list[str]]]:
    """
    Returns tables found on the given 1-indexed page, each table as a
    list of rows (list of cell strings). Returns [] if pdfplumber isn't
    installed, or if this specific page can't be reliably parsed for
    tables — a table-extraction problem on one page must never fail
    extraction of the whole document.
    """
    if not _PDFPLUMBER_AVAILABLE:
        return []

    try:
        with pdfplumber.open(file_path) as pdf:
            if page_number - 1 >= len(pdf.pages):
                return []
            page = pdf.pages[page_number - 1]
            raw_tables = page.extract_tables() or []
    except Exception:
        # Deliberately broad: a malformed page or a pdfplumber internal
        # error must degrade to "no tables on this page", not crash the
        # document. See module docstring / requirement #1.
        return []

    tables = []
    for raw_table in raw_tables:
        cleaned = [[(cell or "").strip() for cell in row] for row in raw_table]
        if any(any(cell for cell in row) for row in cleaned):
            tables.append(cleaned)
    return tables


def _table_to_text(table: list[list[str]]) -> str:
    """Serializes a table (list of rows) into a simple pipe-delimited
    block, so it stays inside the plain-text contract while remaining
    visually distinguishable from prose for downstream MCQ/RAG use."""
    lines = ["[TABLE]"]
    lines.extend(" | ".join(row) for row in table)
    lines.append("[/TABLE]")
    return "\n".join(lines)


def _ocr_page(page) -> tuple[str, bool]:
    """
    Rasterizes a PyMuPDF page and runs OCR on it.
    Returns (text, ocr_succeeded). Never raises — OCR failures degrade
    to ("", False) so document extraction as a whole still completes.
    """
    if not _OCR_AVAILABLE:
        return "", False

    try:
        pixmap = page.get_pixmap(dpi=200)
        image = Image.open(io.BytesIO(pixmap.tobytes("png")))
        text = pytesseract.image_to_string(image)
        return text, True
    except Exception:
        # Covers TesseractNotFoundError (binary not installed) and any
        # other OCR-time failure. See requirement #2: "handle OCR
        # failures gracefully."
        return "", False


def _process_pdf_pages(file_path: str) -> list[dict]:
    """
    Core PDF pipeline. For each page: extract text via PyMuPDF; if the
    page looks scanned (very little/no text), attempt OCR; independently
    attempt table extraction via pdfplumber. Returns one dict per page.
    """
    doc = fitz.open(file_path)
    pages_out = []
    try:
        for i, page in enumerate(doc):
            page_number = i + 1
            text = page.get_text()
            content_type = "text"
            ocr_used = False

            if len(text.strip()) < OCR_TEXT_THRESHOLD:
                ocr_text, ocr_succeeded = _ocr_page(page)
                if ocr_succeeded and ocr_text.strip():
                    text = ocr_text
                    content_type = "ocr"
                    ocr_used = True
                elif not _OCR_AVAILABLE:
                    content_type = "empty_no_ocr_available"
                elif not ocr_succeeded:
                    content_type = "ocr_failed"
                else:
                    content_type = "empty"

            tables = _extract_pdf_page_tables(file_path, page_number)

            pages_out.append({
                "page": page_number,
                "content_type": content_type,
                "text": text.strip(),
                "tables": tables,
                "ocr_used": ocr_used,
            })
    finally:
        doc.close()

    return pages_out


def _process_pptx_slides(file_path: str) -> list[dict]:
    """PPTX pipeline — unchanged behavior from before, just reshaped into
    the same per-page dict structure for a consistent structured API.
    No table/OCR handling here — out of scope (spec targets PDF pages)."""
    presentation = Presentation(file_path)
    slides_out = []
    for i, slide in enumerate(presentation.slides):
        shape_texts = [
            shape.text for shape in slide.shapes
            if hasattr(shape, "text") and shape.text.strip()
        ]
        text = "\n".join(shape_texts)
        slides_out.append({
            "page": i + 1,
            "content_type": "text" if text.strip() else "empty",
            "text": text.strip(),
            "tables": [],
            "ocr_used": False,
        })
    return slides_out


def process_document_structured(file_path: str) -> list[dict]:
    """
    NEW in this enhancement. Returns per-page/per-slide structured
    results for downstream MCQ/RAG use:

        [{"page": int, "content_type": "text"|"table"|"ocr"|"empty"|
          "ocr_failed"|"empty_no_ocr_available", "text": str,
          "tables": list[list[list[str]]], "ocr_used": bool}, ...]

    "tables" is always a list (possibly empty) of tables, each a list
    of rows, each row a list of cell strings. Never raises for
    table/OCR problems on an individual page — see requirement #1/#2.

    Raises:
        FileNotFoundError: if file_path does not exist.
        ValueError: if the file extension isn't .pdf or .pptx.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"process_document_structured: no such file: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"process_document_structured: unsupported file type {ext!r} "
            f"(supported: {sorted(SUPPORTED_EXTENSIONS)})"
        )

    if ext == ".pdf":
        return _process_pdf_pages(file_path)
    return _process_pptx_slides(file_path)


def process_document(file_path: str) -> str:
    """
    process_document(file_path) -> str preserves the existing public API
    signature and return type. For documents containing detected tables,
    the enhanced implementation now includes serialized table content in
    the returned text. Existing callers (including Backend) need no code
    changes, but should be aware output text may now be longer/different
    for documents that contain tables.

    Now internally built on process_document_structured(): joins each
    page's text, with any detected tables serialized and appended after
    that page's text (see _table_to_text).

    Returns:
        Extracted text as a single string. "" for a valid-but-empty
        document — not an error.

    Raises:
        FileNotFoundError: if file_path does not exist.
        ValueError: if the file extension isn't .pdf or .pptx.
    """
    pages = process_document_structured(file_path)

    chunks = []
    for page in pages:
        if page["text"]:
            chunks.append(page["text"])
        for table in page["tables"]:
            chunks.append(_table_to_text(table))

    return "\n".join(chunks)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python ml_pipeline/document_processor.py <path-to-pdf-or-pptx>")
        sys.exit(1)
    text = process_document(sys.argv[1])
    print(f"Extracted {len(text)} characters.")
    print(text[:300])
