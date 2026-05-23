"""
HTTP client for the OCR microservice at :8765 (Layer 2).
"""
import base64
import logging
import requests
from pathlib import Path
from config import OCR_SERVICE_URL

log  = logging.getLogger(__name__)
_http = requests.Session()


def ocr_image(image_path: Path, lang: str = 'sin+tam+eng') -> tuple[str, str]:
    """
    OCR an image file via the microservice.

    Returns:
        (text, language_tag) — e.g. ('Hello', 'eng')
    """
    with open(image_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()
    return _call_ocr(img_b64, lang)


def ocr_bytes(image_bytes: bytes, lang: str = 'sin+tam+eng') -> tuple[str, str]:
    """
    OCR raw image bytes via the microservice.

    Returns:
        (text, language_tag)
    """
    img_b64 = base64.b64encode(image_bytes).decode()
    return _call_ocr(img_b64, lang)


def detect_language(text: str) -> str:
    """
    Detect the script/language of *text* via the microservice.

    Returns:
        Tesseract language code: 'sin', 'tam', or 'eng'.
        Falls back to 'sin+tam+eng' on short text or service errors.
    """
    if len(text.strip()) < 20:
        return 'sin+tam+eng'
    try:
        resp = _http.post(
            f'{OCR_SERVICE_URL}/ocr/detect-lang',
            json={'text': text[:500]},
            timeout=10,
        )
        if resp.ok:
            return resp.json().get('language', 'sin+tam+eng')
    except Exception as e:
        log.warning(f'Language detection failed: {e}')
    return 'sin+tam+eng'


def _call_ocr(img_b64: str, lang: str) -> tuple[str, str]:
    try:
        resp = _http.post(
            f'{OCR_SERVICE_URL}/ocr/image',
            json={'image_b64': img_b64, 'lang': lang},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('text', ''), data.get('language', lang)
    except Exception as e:
        log.error(f'OCR service error: {e}')
        return '', lang
