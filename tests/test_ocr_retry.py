"""
Tests for the automatic OCR retry logic in ingestion/ocr.py.

The retry fires when the standard endpoint returns:
  - DPI below OCR_MIN_DPI (300), OR
  - text shorter than OCR_MIN_TEXT_LEN (20 chars)

The aggressive endpoint is called at most once per request.
The result with more text wins.
"""
from unittest.mock import MagicMock, patch, call
import pytest


# ── helpers ───────────────────────────────────────────────────────────────────

def _mock_response(text: str, dpi: int, lang: str = 'eng') -> MagicMock:
    """Build a fake requests.Response that returns the given OCR payload."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {'text': text, 'language': lang, 'dpi': dpi}
    return resp


# ── retry triggered by low DPI ────────────────────────────────────────────────

class TestRetryOnLowDPI:
    def test_aggressive_called_when_dpi_below_threshold(self):
        """Standard call with DPI=72 must trigger a retry to /aggressive."""
        standard_resp  = _mock_response('hi', dpi=72)
        aggressive_resp = _mock_response('Hello world full text here.', dpi=72)

        with patch('ingestion.ocr._http') as mock_http:
            mock_http.post.side_effect = [standard_resp, aggressive_resp]

            from ingestion.ocr import _call_ocr
            text, lang = _call_ocr('fakebase64==', 'eng')

        assert mock_http.post.call_count == 2
        # First call: standard endpoint
        first_url = mock_http.post.call_args_list[0][0][0]
        assert first_url.endswith('/ocr/image')
        # Second call: aggressive endpoint
        second_url = mock_http.post.call_args_list[1][0][0]
        assert second_url.endswith('/ocr/image/aggressive')

    def test_returns_aggressive_text_when_longer(self):
        """Longer aggressive result must be returned over the short standard one."""
        standard_resp   = _mock_response('hi', dpi=72)
        aggressive_resp = _mock_response('Hello world full text here.', dpi=72)

        with patch('ingestion.ocr._http') as mock_http:
            mock_http.post.side_effect = [standard_resp, aggressive_resp]

            from ingestion.ocr import _call_ocr
            text, lang = _call_ocr('fakebase64==', 'eng')

        assert text == 'Hello world full text here.'

    def test_keeps_standard_text_when_aggressive_is_worse(self):
        """If aggressive retry yields less text, keep the standard result."""
        standard_resp   = _mock_response('Short but fine text output.', dpi=72)
        aggressive_resp = _mock_response('Bad', dpi=72)

        with patch('ingestion.ocr._http') as mock_http:
            mock_http.post.side_effect = [standard_resp, aggressive_resp]

            from ingestion.ocr import _call_ocr
            text, _ = _call_ocr('fakebase64==', 'eng')

        assert text == 'Short but fine text output.'

    def test_no_retry_when_dpi_is_high(self):
        """DPI >= 300 with sufficient text must NOT trigger a retry."""
        standard_resp = _mock_response('This is a full paragraph of text content.', dpi=300)

        with patch('ingestion.ocr._http') as mock_http:
            mock_http.post.return_value = standard_resp

            from ingestion.ocr import _call_ocr
            _call_ocr('fakebase64==', 'eng')

        assert mock_http.post.call_count == 1


# ── retry triggered by short text ─────────────────────────────────────────────

class TestRetryOnShortText:
    def test_aggressive_called_when_text_too_short(self):
        """Text shorter than OCR_MIN_TEXT_LEN must trigger aggressive retry."""
        # DPI is fine (300+) but text is only 5 chars
        standard_resp   = _mock_response('Hello', dpi=300)
        aggressive_resp = _mock_response('Hello world document text here ok.', dpi=300)

        with patch('ingestion.ocr._http') as mock_http:
            mock_http.post.side_effect = [standard_resp, aggressive_resp]

            from ingestion.ocr import _call_ocr
            text, _ = _call_ocr('fakebase64==', 'eng')

        assert mock_http.post.call_count == 2
        assert text == 'Hello world document text here ok.'

    def test_no_double_retry_when_already_aggressive(self):
        """Calling _call_ocr with aggressive=True must NOT retry again."""
        aggressive_resp = _mock_response('tiny', dpi=72)

        with patch('ingestion.ocr._http') as mock_http:
            mock_http.post.return_value = aggressive_resp

            from ingestion.ocr import _call_ocr
            _call_ocr('fakebase64==', 'eng', aggressive=True)

        # Only one HTTP call — no infinite recursion
        assert mock_http.post.call_count == 1


# ── edge cases ────────────────────────────────────────────────────────────────

class TestRetryEdgeCases:
    def test_empty_text_triggers_retry(self):
        """Empty text string (< OCR_MIN_TEXT_LEN) triggers aggressive retry."""
        standard_resp   = _mock_response('', dpi=300)
        aggressive_resp = _mock_response('Recovered text after aggressive OCR.', dpi=300)

        with patch('ingestion.ocr._http') as mock_http:
            mock_http.post.side_effect = [standard_resp, aggressive_resp]

            from ingestion.ocr import _call_ocr
            text, _ = _call_ocr('fakebase64==', 'eng')

        assert text == 'Recovered text after aggressive OCR.'

    def test_language_from_aggressive_result_returned(self):
        """Language tag from the winning (aggressive) result is returned."""
        standard_resp   = _mock_response('hi', dpi=72, lang='eng')
        aggressive_resp = _mock_response('සිංහල document text here', dpi=72, lang='sin')

        with patch('ingestion.ocr._http') as mock_http:
            mock_http.post.side_effect = [standard_resp, aggressive_resp]

            from ingestion.ocr import _call_ocr
            _, lang = _call_ocr('fakebase64==', 'sin+tam+eng')

        assert lang == 'sin'

    def test_service_error_returns_empty(self):
        """If the OCR service throws, return empty string gracefully."""
        with patch('ingestion.ocr._http') as mock_http:
            mock_http.post.side_effect = Exception('connection refused')

            from ingestion.ocr import _call_ocr
            text, lang = _call_ocr('fakebase64==', 'eng')

        assert text == ''
        assert lang == 'eng'
