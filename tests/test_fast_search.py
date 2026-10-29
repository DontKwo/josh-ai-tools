#!/usr/bin/env python3
"""Unit tests for the fast_search tool."""
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.fast_search import search_in_file

class TestFastSearch(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_search_in_file_utf8(self) -> None:
        test_file = self.temp_dir / "test_utf8.txt"
        test_file.write_text("hello world\nthis is a test\nfind me\n", encoding="utf-8")

        pattern = re.compile(r"find me")
        results = search_in_file(test_file, pattern)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 3)
        self.assertTrue(any("find me" in line for line in results[0][1]))

    def test_search_in_file_latin1_fallback(self) -> None:
        test_file = self.temp_dir / "test_latin1.txt"
        # Write bytes that will cause UnicodeDecodeError if decoded as UTF-8
        # \xff is valid in latin-1 but not utf-8
        test_file.write_bytes(b"hello \xff world\nfind me here\n")

        pattern = re.compile(r"find me")
        results = search_in_file(test_file, pattern)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 2)
        self.assertTrue(any("find me" in line for line in results[0][1]))

    def test_search_in_file_error(self) -> None:
        test_file = self.temp_dir / "test_missing.txt"
        # Don't create the file, so opening it raises FileNotFoundError

        pattern = re.compile(r"find me")
        results = search_in_file(test_file, pattern)

        # Exception handler should catch it and return empty list
        self.assertEqual(results, [])

if __name__ == "__main__":
    unittest.main()
