"""
PowerPoint parser — extracts slide text and speaker notes (Layer 2).
"""
import logging
from pathlib import Path
from ingestion.ocr import detect_language

log = logging.getLogger(__name__)


def parse(path: Path) -> list[dict]:
    """
    Parse a .pptx file.
    Returns one ParsedDoc dict per non-empty slide (text + notes combined).
    """
    docs: list[dict] = []
    try:
        from pptx import Presentation  # type: ignore[import-untyped]

        prs = Presentation(str(path))
        for i, slide in enumerate(prs.slides, 1):
            parts: list[str] = []

            # All text frames on the slide
            for shape in slide.shapes:
                if shape.has_text_frame:
                    from pptx.shapes.base import BaseShape  # type: ignore[import-untyped]
                    from pptx.util import Emu  # type: ignore[import-untyped]
                    tf = getattr(shape, 'text_frame', None)
                    if tf is not None:
                        for para in tf.paragraphs:
                            line = ' '.join(run.text for run in para.runs).strip()
                            if line:
                                parts.append(line)

            # Speaker notes
            if slide.has_notes_slide:
                notes_slide = slide.notes_slide
                ntf = getattr(notes_slide, 'notes_text_frame', None)
                notes = ntf.text.strip() if ntf is not None else ''
                if notes:
                    parts.append(f'[Notes] {notes}')

            text = '\n'.join(parts).strip()
            if not text:
                continue

            lang = detect_language(text[:300])
            docs.append({
                'text':     text,
                'source':   str(path),
                'page':     i,
                'language': lang,
                'doc_type': 'pptx',
            })

    except Exception as e:
        log.error(f'PPTX parse error for {path.name}: {e}', exc_info=True)

    return docs
