"""
PDF parser — digital text via pdfplumber; scanned pages via OCR microservice (Layer 2).
Auto-detects scanned vs digital by checking text density per page.
"""
import subprocess
import tempfile
import logging
from pathlib import Path
from ingestion.ocr import ocr_bytes, detect_language

log = logging.getLogger(__name__)

# Pages with fewer than this many characters are treated as scanned
_MIN_DIGITAL_CHARS = 50


def parse(path: Path) -> list[dict]:
    """
    Parse a PDF file, page by page.
    Returns one ParsedDoc dict per page that yields text.
    """
    docs: list[dict] = []
    try:
        import pdfplumber  # type: ignore[import-untyped]
        with pdfplumber.open(str(path)) as pdf:
            # Detect overall language from the first digital page
            sample_text = ''
            for page in pdf.pages[:3]:
                t = (page.extract_text() or '').strip()
                if len(t) >= _MIN_DIGITAL_CHARS:
                    sample_text = t
                    break

            lang = detect_language(sample_text[:300]) if sample_text else 'sin+tam+eng'

            for i, page in enumerate(pdf.pages, 1):
                text = (page.extract_text() or '').strip()

                # Also extract any tables as markdown
                tables = page.extract_tables() or []
                for table in tables:
                    table_md = _table_to_markdown(table)
                    if table_md:
                        text = (text + '\n\n' + table_md).strip()

                if len(text) >= _MIN_DIGITAL_CHARS:
                    # Digital page
                    docs.append({
                        'text':     text,
                        'source':   str(path),
                        'page':     i,
                        'language': lang,
                        'doc_type': 'pdf',
                    })
                else:
                    # Scanned page — fall back to OCR
                    ocr_text = _ocr_pdf_page(path, i)
                    if ocr_text:
                        page_lang = detect_language(ocr_text[:300])
                        docs.append({
                            'text':     ocr_text,
                            'source':   str(path),
                            'page':     i,
                            'language': page_lang,
                            'doc_type': 'pdf',
                        })

    except Exception as e:
        log.error(f'PDF parse error for {path.name}: {e}', exc_info=True)

    return docs


def _ocr_pdf_page(pdf_path: Path, page_num: int) -> str:
    """Render a single PDF page to a raster image then OCR it via the microservice."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = Path(tmpdir) / 'page'
            subprocess.run(
                [
                    'pdftoppm', '-r', '300',
                    '-f', str(page_num), '-l', str(page_num),
                    str(pdf_path), str(prefix),
                ],
                check=True, capture_output=True, timeout=60,
            )
            images = sorted(Path(tmpdir).glob('*'))
            if not images:
                return ''
            text, _ = ocr_bytes(images[0].read_bytes())
            return text
    except FileNotFoundError:
        log.warning('pdftoppm not found — install poppler-utils for scanned PDF support')
        return ''
    except Exception as e:
        log.warning(f'OCR failed for page {page_num} of {pdf_path.name}: {e}')
        return ''


def _table_to_markdown(table: list[list]) -> str:
    """Convert a pdfplumber table (list of rows) to a markdown table string."""
    if not table:
        return ''
    rows = [[str(cell or '') for cell in row] for row in table]
    header = rows[0]
    sep    = ['---'] * len(header)
    lines  = [
        '| ' + ' | '.join(header) + ' |',
        '| ' + ' | '.join(sep) + ' |',
    ]
    for row in rows[1:]:
        padded = row + [''] * max(0, len(header) - len(row))
        lines.append('| ' + ' | '.join(padded[:len(header)]) + ' |')
    return '\n'.join(lines)
