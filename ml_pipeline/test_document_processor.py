"""
Test for ML-002 (document_processor.process_document).

Generates its own PDF/PPTX fixtures in a temp directory at test-run time
so no binary files need to live in the repo. Run directly:

    python ml_pipeline/test_document_processor.py
"""
import os
import tempfile

import pymupdf as fitz  # PyMuPDF's current import name
from pptx import Presentation

from ml_pipeline.document_processor import process_document

SAMPLE_TEXT = "Stratified sampling divides the population into homogeneous subgroups."


def _make_fixture_pdf(dir_path: str) -> str:
    path = os.path.join(dir_path, "fixture.pdf")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), SAMPLE_TEXT)
    doc.save(path)
    doc.close()
    return path


def _make_fixture_pptx(dir_path: str) -> str:
    path = os.path.join(dir_path, "fixture.pptx")
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Sampling Design"
    slide.placeholders[1].text = SAMPLE_TEXT
    prs.save(path)
    return path


def _make_empty_pptx(dir_path: str) -> str:
    path = os.path.join(dir_path, "empty.pptx")
    prs = Presentation()
    prs.slides.add_slide(prs.slide_layouts[6])  # blank layout, no text
    prs.save(path)
    return path


def run_tests() -> bool:
    all_passed = True
    with tempfile.TemporaryDirectory() as tmp:
        # PDF extraction
        pdf_path = _make_fixture_pdf(tmp)
        pdf_text = process_document(pdf_path)
        ok = "Stratified sampling" in pdf_text
        print(f"[{'PASS' if ok else 'FAIL'}] PDF extraction: {pdf_text[:60]!r}")
        all_passed &= ok

        # PPTX extraction
        pptx_path = _make_fixture_pptx(tmp)
        pptx_text = process_document(pptx_path)
        ok = "Stratified sampling" in pptx_text and "Sampling Design" in pptx_text
        print(f"[{'PASS' if ok else 'FAIL'}] PPTX extraction: {pptx_text[:60]!r}")
        all_passed &= ok

        # Empty document -> "" not an exception
        empty_path = _make_empty_pptx(tmp)
        empty_text = process_document(empty_path)
        ok = empty_text == ""
        print(f"[{'PASS' if ok else 'FAIL'}] Empty PPTX returns '' : {empty_text!r}")
        all_passed &= ok

        # Missing file -> FileNotFoundError
        try:
            process_document(os.path.join(tmp, "does_not_exist.pdf"))
            ok = False
        except FileNotFoundError:
            ok = True
        print(f"[{'PASS' if ok else 'FAIL'}] Missing file raises FileNotFoundError")
        all_passed &= ok

        # Unsupported extension -> ValueError
        bad_path = os.path.join(tmp, "notes.txt")
        with open(bad_path, "w") as f:
            f.write("plain text file")
        try:
            process_document(bad_path)
            ok = False
        except ValueError:
            ok = True
        print(f"[{'PASS' if ok else 'FAIL'}] Unsupported extension raises ValueError")
        all_passed &= ok

    return all_passed


if __name__ == "__main__":
    import sys
    success = run_tests()
    print("\nML-002 TEST SUITE:", "PASS" if success else "FAIL")
    sys.exit(0 if success else 1)
