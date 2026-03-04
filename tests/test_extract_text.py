import unittest
from pathlib import Path
from unittest.mock import patch

from pypdf.errors import PdfStreamError

from ebook_editor_core import extract_text_from_pdf


class _FakePage:
    def __init__(self, text=None, error=None):
        self._text = text
        self._error = error

    def extract_text(self):
        if self._error:
            raise self._error
        return self._text


class _FakeReader:
    def __init__(self, _):
        self.pages = [
            _FakePage("page one"),
            _FakePage(error=PdfStreamError("broken stream")),
            _FakePage("page three"),
        ]


class ExtractTextFromPdfTests(unittest.TestCase):
    @patch("pypdf.PdfReader", _FakeReader)
    def test_skips_corrupt_pages_and_returns_remaining_text(self):
        with self.assertWarns(RuntimeWarning):
            text = extract_text_from_pdf(Path("dummy.pdf"))

        self.assertEqual(text, "page one\n\npage three")


if __name__ == "__main__":
    unittest.main()
