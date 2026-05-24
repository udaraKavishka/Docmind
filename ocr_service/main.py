"""
DocMind OCR Microservice — Layer 2
====================================
FastAPI service at :8765 that wraps Tesseract + OpenCV preprocessing.

Endpoints:
  POST /ocr/image       — OCR a base64-encoded image, returns text + language
  POST /ocr/image/aggressive — same, but with stronger preprocessing for poor scans
  POST /ocr/detect-lang — detect the language of a text sample
  GET  /health          — liveness check

Architecture note (from L2_OCR_Parser.md):
  Go binary calls this service over HTTP so that Tesseract and OpenCV stay in
  Python where they are best supported, while Go code remains pure and testable.
"""

import base64
import io
import logging
import sys
import os

# Allow importing config from the project root regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
import pytesseract
from fastapi import FastAPI, HTTPException
from langdetect import LangDetectException, detect
from PIL import Image
from pydantic import BaseModel
from config import OCR_MIN_DPI as MIN_DPI, OCR_MIN_TEXT_LEN as MIN_TEXT_LEN

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ocr_service")

app = FastAPI(title="DocMind OCR Service", version="2.0")

# ── Constants ─────────────────────────────────────────────────────────────────
LANG_MAP     = {"si": "sin", "ta": "tam", "en": "eng"}
DEFAULT_LANG = "sin+tam+eng"
# MIN_DPI and MIN_TEXT_LEN imported from config.py — shared with ingestion/ocr.py


# ── Pydantic models ───────────────────────────────────────────────────────────

class OCRRequest(BaseModel):
    image_b64: str
    lang: str = DEFAULT_LANG


class LangRequest(BaseModel):
    text: str


# ── Preprocessing ─────────────────────────────────────────────────────────────

def preprocess(pil_img: Image.Image) -> np.ndarray:
    """
    Standard preprocessing pipeline (L2 spec):
      1. Convert to grayscale
      2. Otsu thresholding (automatic black/white separation)
      3. Non-local means denoising (removes scanner grain)

    Suitable for clean scans at ≥ 300 DPI.
    """
    img  = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.fastNlMeansDenoising(thresh, h=10)


def preprocess_aggressive(pil_img: Image.Image) -> np.ndarray:
    """
    Aggressive preprocessing for poor-quality or low-DPI scans (L2 spec):
      1. Upscale if width < 1000 px (improves Tesseract LSTM accuracy)
      2. Adaptive Gaussian thresholding (handles uneven lighting)
      3. Morphological closing (joins broken strokes in degraded fonts)
      4. Non-local means denoising

    Use for noisy or low-resolution input where standard preprocessing fails.
    """
    img  = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    h, w = gray.shape
    if w < 1000:
        gray = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        log.info(f"Upscaled image from {w}×{h} to {w*2}×{h*2} for better OCR")

    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 2,
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    return cv2.fastNlMeansDenoising(closed, h=7)


def check_dpi(pil_img: Image.Image) -> int:
    """
    Extract DPI from image metadata (L2 spec).
    Falls back to 72 if not embedded. Warn when below MIN_DPI (300).
    """
    dpi = pil_img.info.get("dpi", (72, 72))
    return int(dpi[0])


# ── Language detection ────────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    """
    Detect script/language via langdetect and map to Tesseract lang codes.
    Falls back to DEFAULT_LANG ('sin+tam+eng') on short or ambiguous text.
    """
    if len(text.strip()) < MIN_TEXT_LEN:
        return DEFAULT_LANG
    try:
        lang = detect(text)
        return LANG_MAP.get(lang, DEFAULT_LANG)
    except LangDetectException:
        return DEFAULT_LANG


# ── Core OCR helper ───────────────────────────────────────────────────────────

def _run_ocr(pil_img: Image.Image, lang: str, aggressive: bool = False) -> dict:
    """
    Run the full OCR pipeline on a PIL image.

    1. Check DPI — log a warning if < MIN_DPI (does not block processing)
    2. Preprocess with standard or aggressive pipeline
    3. Run Tesseract with LSTM engine (--oem 3) and page segmentation (--psm 6)
    4. Detect language of extracted text

    Returns {"text": str, "language": str, "dpi": int}
    """
    dpi = check_dpi(pil_img)
    if dpi < MIN_DPI:
        log.warning(f"Low DPI detected: {dpi} — OCR accuracy may be reduced (recommended: ≥{MIN_DPI})")

    processed_arr = preprocess_aggressive(pil_img) if aggressive else preprocess(pil_img)
    processed_pil = Image.fromarray(processed_arr)

    text = pytesseract.image_to_string(
        processed_pil,
        lang=lang,
        config="--psm 6 --oem 3",
    ).strip()

    language = detect_language(text[:500]) if text else DEFAULT_LANG
    log.info(f"OCR complete — {len(text)} chars, lang={language}, dpi={dpi}, aggressive={aggressive}")
    return {"text": text, "language": language, "dpi": dpi}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/ocr/image")
def ocr_image(req: OCRRequest):
    """
    Standard OCR — suitable for clean scans at ≥ 300 DPI.
    Uses Otsu thresholding + NL-means denoising.
    """
    try:
        img_bytes   = base64.b64decode(req.image_b64)
        pil_img     = Image.open(io.BytesIO(img_bytes))
        result      = _run_ocr(pil_img, req.lang, aggressive=False)
        return result
    except Exception as e:
        log.error(f"/ocr/image error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/image/aggressive")
def ocr_image_aggressive(req: OCRRequest):
    """
    Aggressive OCR — for poor-quality, noisy, or low-DPI scans.
    Upscales small images, uses adaptive thresholding + morphological closing.
    """
    try:
        img_bytes = base64.b64decode(req.image_b64)
        pil_img   = Image.open(io.BytesIO(img_bytes))
        result    = _run_ocr(pil_img, req.lang, aggressive=True)
        return result
    except Exception as e:
        log.error(f"/ocr/image/aggressive error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/detect-lang")
def detect_lang_endpoint(req: LangRequest):
    """Detect the language of a text sample."""
    return {"language": detect_language(req.text)}


@app.get("/health")
def health():
    """Liveness check — returns OK if Tesseract is reachable."""
    try:
        pytesseract.get_tesseract_version()
        return {"status": "ok", "tesseract": "available"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Tesseract unavailable: {e}")
