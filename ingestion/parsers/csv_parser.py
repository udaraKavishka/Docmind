"""
CSV / Excel parser — converts tabular data to a markdown table string (Layer 2).
"""
import csv
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def parse(path: Path) -> list[dict]:
    """
    Parse a .csv or .xlsx file.
    Returns a single ParsedDoc with the table represented as markdown.
    """
    try:
        ext  = path.suffix.lower()
        rows = _read_rows(path, ext)

        if not rows:
            return []

        text = _to_markdown(rows)
        if not text:
            return []

        return [{
            'text':     text,
            'source':   str(path),
            'page':     0,
            'language': 'eng',   # tabular data treated as English
            'doc_type': 'csv',
        }]
    except Exception as e:
        log.error(f'CSV parse error for {path.name}: {e}', exc_info=True)
        return []


def _read_rows(path: Path, ext: str) -> list[list[str]]:
    if ext == '.xlsx':
        import openpyxl
        wb   = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
        rows = []
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                rows.append([str(c) if c is not None else '' for c in row])
        return rows

    # CSV (default)
    with open(path, newline='', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f, skipinitialspace=True)
        return [row for row in reader if any(cell.strip() for cell in row)]


def _to_markdown(rows: list[list[str]]) -> str:
    if not rows:
        return ''
    header = rows[0]
    w      = len(header)
    lines  = [
        '| ' + ' | '.join(str(c) for c in header) + ' |',
        '| ' + ' | '.join(['---'] * w) + ' |',
    ]
    for row in rows[1:]:
        padded = list(row) + [''] * max(0, w - len(row))
        lines.append('| ' + ' | '.join(str(c) for c in padded[:w]) + ' |')
    return '\n'.join(lines)
