#!/usr/bin/env python3
"""Unit tests for the fast_search tool."""
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from io import StringIO
from unittest.mock import patch

from scripts.fast_search import main, search_in_file


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

    def test_regex_search(self) -> None:
        test_file = self.temp_dir / "test_regex.txt"
        test_file.write_text("hello 123 world\nthis is a test\nfind 456 me\n", encoding="utf-8")

        # Compile the regex pattern directly, equivalent to passing --regex
        pattern = re.compile(r"find \d+ me")
        results = search_in_file(test_file, pattern)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 3)
        self.assertTrue(any("find 456 me" in line for line in results[0][1]))

    def test_literal_search(self) -> None:
        test_file = self.temp_dir / "test_literal.txt"
        test_file.write_text("hello world\nthis is a test\nfind .* me\n", encoding="utf-8")

        # Compile the literal string using re.escape, equivalent to NOT passing --regex
        query = "find .* me"
        pattern = re.compile(re.escape(query))
        results = search_in_file(test_file, pattern)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 3)
        self.assertTrue(any("find .* me" in line for line in results[0][1]))

    def test_extension_filter(self) -> None:
        py_file = self.temp_dir / "test.py"
        py_file.write_text("def hello():\n    pass\n", encoding="utf-8")
        txt_file = self.temp_dir / "test.txt"
        txt_file.write_text("def hello():\n    pass\n", encoding="utf-8")

        with patch("sys.argv", ["fast_search.py", "def", str(self.temp_dir), "--ext", "py"]), \
             patch("sys.stdout", new=StringIO()) as fake_out:
            main()
            output = fake_out.getvalue()
            self.assertIn("test.py", output)
            self.assertNotIn("test.txt", output)


if __name__ == "__main__":
    unittest.main()
