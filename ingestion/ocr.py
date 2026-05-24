"""
HTTP client for the OCR microservice at :8765 (Layer 2).
"""
import base64
import logging
import requests
from pathlib import Path
from config import OCR_SERVICE_URL, OCR_MIN_DPI, OCR_MIN_TEXT_LEN

log  = logging.getLogger(__name__)
_http = requests.Session()


def ocr_image(
    image_path: Path,
    lang: str = 'sin+tam+eng',
    aggressive: bool = False,
) -> tuple[str, str]:
    """
    OCR an image file via the microservice.

    Args:
        image_path: Path to the image file
        lang:       Tesseract language string (default: 'sin+tam+eng')
        aggressive: Use aggressive preprocessing for low-DPI or noisy scans

    Returns:
        (text, language_tag) — e.g. ('Hello', 'eng')
    """
    with open(image_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()
    return _call_ocr(img_b64, lang, aggressive=aggressive)


def ocr_bytes(
    image_bytes: bytes,
    lang: str = 'sin+tam+eng',
    aggressive: bool = False,
) -> tuple[str, str]:
    """
    OCR raw image bytes via the microservice.

    Args:
        image_bytes: Raw image data (PNG, JPEG, PPM, etc.)
        lang:        Tesseract language string
        aggressive:  Use aggressive preprocessing for low-DPI or noisy scans

    Returns:
        (text, language_tag)
    """
    img_b64 = base64.b64encode(image_bytes).decode()
    return _call_ocr(img_b64, lang, aggressive=aggressive)


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


def _call_ocr(img_b64: str, lang: str, aggressive: bool = False) -> tuple[str, str]:
    """
    Core OCR helper. Automatically retries with aggressive preprocessing when:
      - The image DPI is below OCR_MIN_DPI (300), OR
      - The extracted text is shorter than OCR_MIN_TEXT_LEN (20 chars).
    The aggressive retry fires at most once (guarded by the `aggressive` flag).
    The result with more text is returned.
    """
    endpoint = '/ocr/image/aggressive' if aggressive else '/ocr/image'
    try:
        resp = _http.post(
            f'{OCR_SERVICE_URL}{endpoint}',
            json={'image_b64': img_b64, 'lang': lang},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data.get('text', '')
        dpi  = data.get('dpi', 0)
        lang_out = data.get('language', lang)

        # ── Auto-retry with aggressive pipeline on poor-quality results ──
        if not aggressive and (
            (dpi and dpi < OCR_MIN_DPI) or
            len(text.strip()) < OCR_MIN_TEXT_LEN
        ):
            log.info(
                f'Low quality result (dpi={dpi}, chars={len(text.strip())}) '
                f'— retrying with aggressive preprocessing'
            )
            agg_text, agg_lang = _call_ocr(img_b64, lang, aggressive=True)
            if len(agg_text.strip()) > len(text.strip()):
                log.info(
                    f'Aggressive retry improved result: '
                    f'{len(text.strip())} → {len(agg_text.strip())} chars'
                )
                return agg_text, agg_lang
            else:
                log.info('Aggressive retry did not improve result — keeping standard output')

        return text, lang_out
    except Exception as e:
        log.error(f'OCR service error ({endpoint}): {e}')
        return '', lang
