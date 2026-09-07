"""
ml_pipeline/tests/test_ocr_engine.py — Unit tests for Vision & OCR Fallback Engine.
"""
from __future__ import annotations

import io
from PIL import Image, ImageDraw

from ml_pipeline.ocr_engine import (
    ImagePreprocessor,
    VisionOCREngine,
    get_ocr_engine,
    OCRResult,
)


def test_image_preprocessor_contrast_and_binarization():
    """Verifies that ImagePreprocessor converts to grayscale and enhances contrast."""
    # Create RGB image with faint gray text background
    img = Image.new("RGB", (200, 100), color=(220, 220, 220))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Test Preprocessing", fill=(80, 80, 80))

    enhanced = ImagePreprocessor.enhance_for_ocr(img, contrast_factor=2.0, binarize=True, threshold=150)
    assert enhanced.mode == "L"
    assert enhanced.size == (200, 100)


def test_vision_ocr_engine_synthetic_text_extraction():
    """Renders synthetic text into a clean PIL image and tests Tesseract OCR."""
    engine = get_ocr_engine()
    if not engine.tesseract_available:
        # If running in environment without tesseract binary, ensure fallback works
        res = engine.ocr_image(b"invalid_bytes", preprocess=False)
        assert res.success is False
        return

    # Draw clear black text on white canvas
    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 35), "STATISTICS FOR APPLICATIONS", fill=(0, 0, 0))

    res = engine.ocr_image(img, preprocess=True)
    assert isinstance(res, OCRResult)
    assert res.success is True
    assert res.engine_used == "tesseract"
    assert "STATISTICS" in res.text.upper() or "APPLICATIONS" in res.text.upper()


def test_vision_ocr_engine_invalid_input_graceful_handling():
    """Verifies that unreadable or invalid inputs return failure rather than crashing."""
    engine = get_ocr_engine()
    res = engine.ocr_image(b"not_an_image_file_bytes")
    assert isinstance(res, OCRResult)
    assert res.success is False
    assert res.char_count == 0
    assert res.error is not None


def test_vision_ocr_engine_pptx_shape_without_image():
    """Verifies that PPTX shapes without image blobs fail gracefully."""
    class DummyShape:
        text = "Just a text box"

    engine = get_ocr_engine()
    res = engine.ocr_pptx_shape(DummyShape())
    assert res.success is False
    assert "image blob" in res.error.lower()
