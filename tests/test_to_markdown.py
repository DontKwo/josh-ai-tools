import unittest
from pathlib import Path
import zlib
import tempfile
import os

from scripts.to_markdown import extract_pdf_fallback

class TestExtractPdfFallback(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_file_read_error(self) -> None:
        # File doesn't exist
        missing_file = self.temp_dir_path / "missing.pdf"
        result = extract_pdf_fallback(missing_file)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].startswith("[Error reading PDF:"))

    def test_valid_zlib_streams(self) -> None:
        # Create a valid zlib stream containing text
        text_content = b"(Hello World) Tj"
        compressed = zlib.compress(text_content)
        pdf_content = b"stream\n" + compressed + b"\nendstream"

        pdf_file = self.temp_dir_path / "valid.pdf"
        pdf_file.write_bytes(pdf_content)

        result = extract_pdf_fallback(pdf_file)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "Hello World")

    def test_valid_zlib_streams_max_pages(self) -> None:
        # Create multiple streams to test max_pages
        # The function groups chunks: per_page = max(1, len(decompressed_chunks) // 4)
        # So we need at least 5 chunks to have more than 1 page.
        # Wait, if len is 5, per_page = 1. So 5 pages.
        # Let's create 5 streams.

        pdf_content = b""
        for i in range(5):
            text_content = f"(Page {i}) Tj".encode("latin1")
            compressed = zlib.compress(text_content)
            pdf_content += b"stream\n" + compressed + b"\nendstream\n"

        pdf_file = self.temp_dir_path / "max_pages.pdf"
        pdf_file.write_bytes(pdf_content)

        result = extract_pdf_fallback(pdf_file, max_pages=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "Page 0")
        self.assertEqual(result[1], "Page 1")

    def test_raw_string_fallback(self) -> None:
        # No streams, just raw text strings
        pdf_content = b"(Some readable text) \x00 (More text)"
        pdf_file = self.temp_dir_path / "raw.pdf"
        pdf_file.write_bytes(pdf_content)

        result = extract_pdf_fallback(pdf_file)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "Some readable text More text")

    def test_no_readable_text(self) -> None:
        # Neither streams nor strings
        pdf_content = b"random binary data without any text patterns"
        pdf_file = self.temp_dir_path / "noreadable.pdf"
        pdf_file.write_bytes(pdf_content)

        result = extract_pdf_fallback(pdf_file)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "[PDF contains scanned images or encrypted text without readable fonts. Consider installing 'pypdf': pip install pypdf]")

if __name__ == "__main__":
    unittest.main()
