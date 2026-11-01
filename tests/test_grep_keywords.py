#!/usr/bin/env python3
"""Unit tests for grep_keywords.py script."""
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.grep_keywords import DEFAULT_SKIP_DIRS, iter_files, search


class TestGrepKeywords(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir_path = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir_path, ignore_errors=True)

    def test_literal_keyword_matching(self) -> None:
        file_a = self.temp_dir_path / "file_a.txt"
        file_b = self.temp_dir_path / "file_b.txt"
        file_a.write_text("hello world\nfoo bar\n", encoding="utf-8")
        file_b.write_text("another line\nhello universe\n", encoding="utf-8")

        files = iter_files(self.temp_dir_path, None, DEFAULT_SKIP_DIRS)
        pattern = re.compile(re.escape("hello"))
        results, count = search(files, pattern, context=0)

        self.assertEqual(count, 2)
        self.assertEqual(len(results), 2)
        self.assertTrue(any(f"{file_a}:1:> hello world" in line for line in results))
        self.assertTrue(any(f"{file_b}:2:> hello universe" in line for line in results))

    def test_regex_search_mode(self) -> None:
        file_a = self.temp_dir_path / "file_a.txt"
        file_a.write_text("alpha 123\nbeta 456\ngamma abc\n", encoding="utf-8")

        files = [file_a]
        pattern = re.compile(r"[a-z]+\s+\d+")
        results, count = search(files, pattern, context=0)

        self.assertEqual(count, 2)
        self.assertEqual(len(results), 2)
        self.assertIn(f"{file_a}:1:> alpha 123", results)
        self.assertIn(f"{file_a}:2:> beta 456", results)

    def test_case_sensitivity_and_ignore_case(self) -> None:
        file_a = self.temp_dir_path / "file_a.txt"
        file_a.write_text("Target line\ntarget line\nOTHER\n", encoding="utf-8")

        files = [file_a]
        sensitive_pattern = re.compile(re.escape("target"))
        results_sensitive, count_sensitive = search(files, sensitive_pattern, context=0)
        self.assertEqual(count_sensitive, 1)
        self.assertEqual(len(results_sensitive), 1)
        self.assertIn(f"{file_a}:2:> target line", results_sensitive)

        insensitive_pattern = re.compile(re.escape("target"), re.IGNORECASE)
        results_insensitive, count_insensitive = search(files, insensitive_pattern, context=0)
        self.assertEqual(count_insensitive, 2)
        self.assertEqual(len(results_insensitive), 2)

    def test_context_line_extraction(self) -> None:
        file_a = self.temp_dir_path / "file_a.txt"
        file_a.write_text("line 1\nline 2\nmatch line\nline 4\nline 5\n", encoding="utf-8")

        files = [file_a]
        pattern = re.compile(re.escape("match line"))
        results, count = search(files, pattern, context=1)

        self.assertEqual(count, 1)
        expected = [
            f"{file_a}:2:  line 2",
            f"{file_a}:3:> match line",
            f"{file_a}:4:  line 4",
            "--",
        ]
        self.assertEqual(results, expected)

    def test_extension_filtering(self) -> None:
        file_py = self.temp_dir_path / "script.py"
        file_md = self.temp_dir_path / "readme.md"
        file_txt = self.temp_dir_path / "notes.txt"
        file_py.write_text("code", encoding="utf-8")
        file_md.write_text("docs", encoding="utf-8")
        file_txt.write_text("text", encoding="utf-8")

        filtered = iter_files(self.temp_dir_path, ["py", "md"], DEFAULT_SKIP_DIRS)
        filtered_names = {f.name for f in filtered}

        self.assertEqual(filtered_names, {"script.py", "readme.md"})
        self.assertNotIn("notes.txt", filtered_names)

    def test_directory_exclusion(self) -> None:
        git_dir = self.temp_dir_path / ".git"
        custom_dir = self.temp_dir_path / "custom_ignored"
        valid_dir = self.temp_dir_path / "src"

        git_dir.mkdir()
        custom_dir.mkdir()
        valid_dir.mkdir()

        (git_dir / "hidden.py").write_text("hidden", encoding="utf-8")
        (custom_dir / "skip.py").write_text("skip", encoding="utf-8")
        (valid_dir / "app.py").write_text("app", encoding="utf-8")

        skip_dirs = DEFAULT_SKIP_DIRS | {"custom_ignored"}
        found_files = iter_files(self.temp_dir_path, None, skip_dirs)
        found_names = {f.name for f in found_files}

        self.assertEqual(found_names, {"app.py"})
        self.assertNotIn("hidden.py", found_names)
        self.assertNotIn("skip.py", found_names)


if __name__ == "__main__":
    unittest.main()
