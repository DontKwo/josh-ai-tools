#!/usr/bin/env python3
"""Unit tests for scripts/clean_encoding.py."""
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.clean_encoding import (
    MOJIBAKE_MAP,
    PLACEHOLDER_MAP,
    SKIP_DIRS,
    clean_content,
    clean_file,
    process_file,
    scan_directory,
)


class TestCleanContent(unittest.TestCase):
    """Test string-level encoding cleaning transformations."""

    def test_mojibake_replacements_individual(self) -> None:
        # Test specific known mojibake pairs from MOJIBAKE_MAP
        text = "Quotes: â€˜singleâ€™ and â€œdoubleâ€\x9d and ellipsisâ€¦ and hyphen â€“"
        cleaned_text, change_list = clean_content(text)
        self.assertIn("'single'", cleaned_text)
        self.assertIn('"double"', cleaned_text)
        self.assertIn("ellipsis...", cleaned_text)
        self.assertIn("hyphen -", cleaned_text)
        self.assertGreater(len(change_list), 0)

    def test_mojibake_all_mappings(self) -> None:
        # Ensure all entries in MOJIBAKE_MAP are replaced
        for corrupted_seq, expected_char in MOJIBAKE_MAP.items():
            sample_text = f"prefix_{corrupted_seq}_suffix"
            cleaned_text, change_list = clean_content(sample_text)
            self.assertEqual(cleaned_text, f"prefix_{expected_char}_suffix")
            self.assertEqual(len(change_list), 1)

    def test_unicode_replacement_character(self) -> None:
        sample_text = "corrupted\ufffdtext\ufffdhere"
        cleaned_text, change_list = clean_content(sample_text)
        self.assertEqual(cleaned_text, "corruptedtexthere")
        self.assertEqual(len(change_list), 1)

    def test_placeholder_mappings(self) -> None:
        # Ensure all entries in PLACEHOLDER_MAP are correctly converted
        for corrupted_ph, expected_ph in PLACEHOLDER_MAP.items():
            sample_text = f"token {corrupted_ph} value"
            cleaned_text, change_list = clean_content(sample_text)
            self.assertEqual(cleaned_text, f"token {expected_ph} value")
            self.assertEqual(len(change_list), 1)

    def test_degrees_to_word_disabled(self) -> None:
        sample_text = "Temperature is 25°C or 75Â°F."
        cleaned_text, change_list = clean_content(sample_text, degrees_to_word=False)
        self.assertEqual(cleaned_text, "Temperature is 25°C or 75°F.")

    def test_degrees_to_word_enabled(self) -> None:
        sample_text = "Temperature is 25°C and 75Â°F."
        cleaned_text, change_list = clean_content(sample_text, degrees_to_word=True)
        self.assertEqual(cleaned_text, "Temperature is 25 degreesC and 75 degreesF.")
        self.assertGreater(len(change_list), 0)

    def test_clean_content_no_artifacts(self) -> None:
        sample_text = "Normal clean ASCII and standard UTF-8 text without artifacts."
        cleaned_text, change_list = clean_content(sample_text)
        self.assertEqual(cleaned_text, sample_text)
        self.assertEqual(len(change_list), 0)

    def test_invisible_chars(self) -> None:
        sample_text = "text\u200Bwith\u200Cinvisible\u200Dchars\uFEFF"
        cleaned_text, change_list = clean_content(sample_text)
        self.assertEqual(cleaned_text, "textwithinvisiblechars")
        self.assertGreater(len(change_list), 0)

    def test_fullwidth_normalization(self) -> None:
        sample_text = "Ｈｅｌｌｏ！ １２３"
        cleaned_text, change_list = clean_content(sample_text)
        self.assertEqual(cleaned_text, "Hello! 123")
        self.assertGreater(len(change_list), 0)


class TestCleanFile(unittest.TestCase):
    """Test file-level reading, cleaning, and writing."""

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_clean_file_dry_run(self) -> None:
        file_path = self.temp_dir / "sample.txt"
        corrupted_content = "Here is â€œtextâ€\x9d with mojibake."
        file_path.write_text(corrupted_content, encoding="utf-8")

        fixes_count = clean_file(file_path, dry_run=True, degrees_to_word=False)
        self.assertGreater(fixes_count, 0)
        self.assertEqual(file_path.read_text(encoding="utf-8"), corrupted_content)

    def test_clean_file_in_place(self) -> None:
        file_path = self.temp_dir / "sample.txt"
        corrupted_content = "Itâ€™s clean now."
        file_path.write_text(corrupted_content, encoding="utf-8")

        fixes_count = clean_file(file_path, dry_run=False, degrees_to_word=False)
        self.assertGreater(fixes_count, 0)
        self.assertEqual(file_path.read_text(encoding="utf-8"), "It's clean now.")

    def test_clean_file_with_latin1_encoding(self) -> None:
        file_path = self.temp_dir / "latin1.txt"
        raw_bytes = b"\xff '[emoji]'"
        file_path.write_bytes(raw_bytes)

        fixes_count = clean_file(file_path, dry_run=False, degrees_to_word=False)
        self.assertGreater(fixes_count, 0)
        self.assertEqual(file_path.read_text(encoding="utf-8"), "ÿ '[emoji placeholder]'")

    def test_clean_file_no_changes_needed(self) -> None:
        file_path = self.temp_dir / "clean.txt"
        file_path.write_text("Hello clean world\n", encoding="utf-8")

        fixes_count = clean_file(file_path, dry_run=False, degrees_to_word=False)
        self.assertEqual(fixes_count, 0)
        self.assertEqual(file_path.read_text(encoding="utf-8"), "Hello clean world\n")

    def test_clean_file_nonexistent_path(self) -> None:
        missing_path = self.temp_dir / "nonexistent.txt"
        fixes_count = clean_file(missing_path, dry_run=False, degrees_to_word=False)
        self.assertEqual(fixes_count, 0)

    def test_process_file_alias_identical(self) -> None:
        self.assertIs(clean_file, process_file)


class TestScanDirectory(unittest.TestCase):
    """Test directory scanning and filtering ignored folders."""

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scan_directory_single_file(self) -> None:
        single_file = self.temp_dir / "doc.md"
        single_file.write_text("content", encoding="utf-8")
        results = scan_directory(single_file)
        self.assertEqual(results, [single_file.resolve()])

    def test_scan_directory_skips_ignored_folders(self) -> None:
        for ignored_name in [".git", ".venv", "node_modules", "dist", "build"]:
            ignored_dir = self.temp_dir / ignored_name
            ignored_dir.mkdir(parents=True, exist_ok=True)
            ignored_file = ignored_dir / "corrupt.py"
            ignored_file.write_text("â€™", encoding="utf-8")

        valid_dir = self.temp_dir / "src"
        valid_dir.mkdir(parents=True, exist_ok=True)
        valid_file = valid_dir / "valid.py"
        valid_file.write_text("â€™", encoding="utf-8")

        unsupported_file = valid_dir / "image.png"
        unsupported_file.write_text("binary", encoding="utf-8")

        found_files = scan_directory(self.temp_dir)
        self.assertIn(valid_file.resolve(), found_files)
        self.assertNotIn(unsupported_file.resolve(), found_files)

        for found_file in found_files:
            for ignored_name in SKIP_DIRS:
                self.assertNotIn(ignored_name, found_file.parts)


if __name__ == "__main__":
    unittest.main()
