"""
ml_pipeline/ocr_engine.py — Vision & OCR Fallback Engine for GyanSetu.

Provides robust multi-stage optical character recognition and image pre-processing for:
1. Scanned, non-selectable PDF documents.
2. Embedded PowerPoint pictures, diagrams, charts, and chalkboard snapshots.
3. Standalone images (PNG, JPG, TIFF).

Features:
- ImagePreprocessor: Grayscale conversion, contrast enhancement, adaptive binarization, noise filtering.
- High-resolution PyMuPDF rasterization (300 DPI).
- Dual-engine fallback:
  1. Local Tesseract (via pytesseract).
  2. Groq Vision LLM (llama-3.2-11b-vision-preview) fallback when local binary is absent.
  3. Graceful degradation without raising unhandled exceptions.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
import io
import os
from typing import Any, Optional, Union

from PIL import Image, ImageEnhance, ImageFilter

# Optional dependency: pytesseract
try:
    import pytesseract
    _PYTESSERACT_AVAILABLE = True
except ImportError:
    _PYTESSERACT_AVAILABLE = False


@dataclass
class OCRResult:
    """Standardized output of OCR extraction."""
    text: str
    success: bool
    engine_used: str  # "tesseract", "groq_vision", "fallback_none"
    confidence: float
    char_count: int
    error: Optional[str] = None


class ImagePreprocessor:
    """Preprocesses images to maximize OCR character recognition accuracy."""

    @staticmethod
    def enhance_for_ocr(
        image: Image.Image,
        contrast_factor: float = 1.8,
        binarize: bool = True,
        threshold: int = 145,
    ) -> Image.Image:
        """
        Applies grayscale conversion, contrast boosting, and binarization.
        Ideal for scanned documents, low-contrast text, and chalkboard captures.
        """
        # Convert to grayscale
        gray = image.convert("L")

        # Contrast enhancement
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(contrast_factor)

        # Optional binarization (convert pixels < threshold to 0, else 255)
        if binarize:
            table = [0 if i < threshold else 255 for i in range(256)]
            binary = enhanced.point(table, "1")
            return binary.convert("L")

        return enhanced


class VisionOCREngine:
    """Multi-backend OCR engine with pre-processing and graceful fallbacks."""

    def __init__(
        self,
        tesseract_cmd: Optional[str] = None,
        use_groq_vision_fallback: bool = True,
    ):
        self.use_groq_vision_fallback = use_groq_vision_fallback
        self.tesseract_available = False

        if _PYTESSERACT_AVAILABLE:
            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            elif os.path.exists("/opt/homebrew/bin/tesseract"):
                pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
            elif os.path.exists("/usr/local/bin/tesseract"):
                pytesseract.pytesseract.tesseract_cmd = "/usr/local/bin/tesseract"
            elif os.path.exists("/usr/bin/tesseract"):
                pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

            try:
                # Test if tesseract binary can be executed
                pytesseract.get_tesseract_version()
                self.tesseract_available = True
            except Exception:
                self.tesseract_available = False

    def ocr_image(
        self,
        image_input: Union[Image.Image, bytes, str],
        preprocess: bool = True,
        lang: str = "eng",
    ) -> OCRResult:
        """
        Performs OCR on an image (PIL Image, raw bytes, or file path).
        """
        # 1. Load image
        try:
            if isinstance(image_input, Image.Image):
                img = image_input
            elif isinstance(image_input, (bytes, bytearray)):
                img = Image.open(io.BytesIO(image_input))
            elif isinstance(image_input, str) and os.path.exists(image_input):
                img = Image.open(image_input)
            else:
                return OCRResult(
                    text="",
                    success=False,
                    engine_used="fallback_none",
                    confidence=0.0,
                    char_count=0,
                    error="Invalid image input format or file does not exist",
                )
        except Exception as e:
            return OCRResult(
                text="",
                success=False,
                engine_used="fallback_none",
                confidence=0.0,
                char_count=0,
                error=f"Failed to open image: {e}",
            )

        # 2. Preprocess if requested
        processed_img = ImagePreprocessor.enhance_for_ocr(img) if preprocess else img

        # 3. Attempt Primary Backend: Tesseract
        if self.tesseract_available:
            try:
                text = pytesseract.image_to_string(processed_img, lang=lang)
                cleaned_text = text.strip()
                if cleaned_text:
                    return OCRResult(
                        text=cleaned_text,
                        success=True,
                        engine_used="tesseract",
                        confidence=0.92,
                        char_count=len(cleaned_text),
                    )
            except Exception as e:
                pass

        # 4. Attempt Secondary Backend: Groq Vision Fallback
        if self.use_groq_vision_fallback:
            groq_res = self._ocr_with_groq_vision(processed_img)
            if groq_res.success and groq_res.text.strip():
                return groq_res

        # 5. Graceful fallback if no engine extracted text
        return OCRResult(
            text="",
            success=False,
            engine_used="fallback_none",
            confidence=0.0,
            char_count=0,
            error="No OCR text could be extracted from the image",
        )

    def _ocr_with_groq_vision(self, img: Image.Image) -> OCRResult:
        """Fallback OCR using Groq's multimodal vision model (llama-3.2-11b-vision-preview)."""
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return OCRResult(
                text="",
                success=False,
                engine_used="fallback_none",
                confidence=0.0,
                char_count=0,
                error="GROQ_API_KEY not set for Vision OCR fallback",
            )

        try:
            from openai import OpenAI
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            client = OpenAI(
                api_key=api_key,
                base_url=os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            )
            prompt = (
                "Extract all visible text from this image exactly as written. "
                "Preserve formulas, numbers, tables, and bullet points. "
                "Output ONLY the extracted raw text without any conversation or commentary."
            )

            response = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                        ],
                    }
                ],
                temperature=0.1,
                max_tokens=1000,
            )
            extracted = response.choices[0].message.content or ""
            cleaned = extracted.strip()
            return OCRResult(
                text=cleaned,
                success=bool(cleaned),
                engine_used="groq_vision",
                confidence=0.95 if cleaned else 0.0,
                char_count=len(cleaned),
            )
        except Exception as e:
            return OCRResult(
                text="",
                success=False,
                engine_used="groq_vision_failed",
                confidence=0.0,
                char_count=0,
                error=str(e),
            )

    def ocr_pdf_page(self, fitz_page: Any, dpi: int = 300) -> OCRResult:
        """
        Renders a PyMuPDF (fitz) page to high-res pixmap and performs OCR.
        """
        try:
            pixmap = fitz_page.get_pixmap(dpi=dpi)
            img = Image.open(io.BytesIO(pixmap.tobytes("png")))
            return self.ocr_image(img, preprocess=True)
        except Exception as e:
            return OCRResult(
                text="",
                success=False,
                engine_used="fallback_none",
                confidence=0.0,
                char_count=0,
                error=f"PDF page rendering failed: {e}",
            )

    def ocr_pptx_shape(self, shape: Any) -> OCRResult:
        """
        Extracts image bytes from a PowerPoint shape (e.g. Picture or Diagram) and performs OCR.
        """
        try:
            if hasattr(shape, "image") and hasattr(shape.image, "blob"):
                img_bytes = shape.image.blob
                return self.ocr_image(img_bytes, preprocess=True)
            return OCRResult(
                text="",
                success=False,
                engine_used="fallback_none",
                confidence=0.0,
                char_count=0,
                error="Shape does not contain an extractable image blob",
            )
        except Exception as e:
            return OCRResult(
                text="",
                success=False,
                engine_used="fallback_none",
                confidence=0.0,
                char_count=0,
                error=f"PPTX shape OCR failed: {e}",
            )


# Default singleton instance
_default_ocr_engine = VisionOCREngine()


def get_ocr_engine() -> VisionOCREngine:
    """Returns the shared VisionOCREngine instance."""
    global _default_ocr_engine
    return _default_ocr_engine
