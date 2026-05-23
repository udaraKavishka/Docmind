"""
Image parser — OCR via the microservice for PNG, JPEG, TIFF, BMP (Layer 2).
"""
import logging
from pathlib import Path
from ingestion.ocr import ocr_image

log = logging.getLogger(__name__)


def parse(path: Path) -> list[dict]:
    """
    OCR an image file and return a single ParsedDoc dict.
    Returns [] if the OCR service yields no text.
    """
    try:
        text, lang = ocr_image(path)
        if not text.strip():
            log.info(f'No text found in image: {path.name}')
            return []

        return [{
            'text':     text,
            'source':   str(path),
            'page':     0,
            'language': lang,
            'doc_type': 'image',
        }]
    except Exception as e:
        log.error(f'Image parse error for {path.name}: {e}', exc_info=True)
        return []
