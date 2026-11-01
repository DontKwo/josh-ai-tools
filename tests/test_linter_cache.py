"""Unit tests for the incremental caching functionality in claudemd_linter.py."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import claudemd_linter


class TestLinterCache(unittest.TestCase):
    """Test suite for incremental caching in the claudemd_linter."""

    def setUp(self) -> None:
        """Set up isolated temporary directory and dummy file for caching tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name).resolve()
        self.dummy_file = (self.temp_path / "dummy.py").resolve()
        self.dummy_file.write_text("def foo() -> None:\n    pass  # noqa: 10\n", encoding="utf-8")

        self.cache_path = self.temp_path / ".lint_cache.json"

        # Patch stdout so we don't spam the console during testing
        self.patcher_stdout = patch("sys.stdout")
        self.mock_stdout = self.patcher_stdout.start()

        # Patch the cache path in the linter module
        self.patcher_cache = patch("scripts.claudemd_linter.CACHE_PATH", self.cache_path)
        self.patcher_cache.start()

        # Patch the calculate report path function so we don't generate junk reports
        self.report_path = self.temp_path / "lint_report.txt"
        self.patcher_report = patch("scripts.claudemd_linter.calc_report_path", return_value=self.report_path)
        self.patcher_report.start()

    def tearDown(self) -> None:
        """Clean up the temporary directory and patches after each test."""
        self.patcher_stdout.stop()
        self.patcher_cache.stop()
        self.patcher_report.stop()
        self.temp_dir.cleanup()

    def test_cache_creation_and_format(self) -> None:
        """Test that the cache file is created and has the expected JSON format."""
        test_args = ["claudemd_linter.py", str(self.dummy_file)]
        with patch.object(sys, "argv", test_args):
            claudemd_linter.main()

        self.assertTrue(self.cache_path.exists())

        cache_data = json.loads(self.cache_path.read_text(encoding="utf-8"))
        file_key = str(self.dummy_file)
        self.assertIn(file_key, cache_data)

        entry = cache_data[file_key]
        self.assertIn("hash", entry)
        self.assertIn("violations", entry)
        self.assertIn("funcs", entry)

        expected_hash = claudemd_linter.get_file_hash(self.dummy_file)
        self.assertEqual(entry["hash"], expected_hash)
        self.assertIsInstance(entry["violations"], list)

    def test_cache_hit_skips_parsing(self) -> None:
        """Test that running the linter twice on unmodified file skips scan_single_file."""
        test_args = ["claudemd_linter.py", str(self.dummy_file)]

        # First run to populate cache
        with patch.object(sys, "argv", test_args):
            with patch("scripts.claudemd_linter.scan_single_file", wraps=claudemd_linter.scan_single_file) as mock_scan:
                claudemd_linter.main()
                mock_scan.assert_called_once_with(str(self.dummy_file))

        # Second run should hit cache
        with patch.object(sys, "argv", test_args):
            with patch("scripts.claudemd_linter.scan_single_file", wraps=claudemd_linter.scan_single_file) as mock_scan:
                claudemd_linter.main()
                mock_scan.assert_not_called()

    def test_cache_invalidation_on_modification(self) -> None:
        """Test that modifying a file changes its hash and triggers a re-scan."""
        test_args = ["claudemd_linter.py", str(self.dummy_file)]

        # First run
        with patch.object(sys, "argv", test_args):
            with patch("scripts.claudemd_linter.scan_single_file", wraps=claudemd_linter.scan_single_file) as mock_scan:
                claudemd_linter.main()
                mock_scan.assert_called_once_with(str(self.dummy_file))

        # Modify the file
        self.dummy_file.write_text("def bar() -> None:\n    print('hello')\n", encoding="utf-8")

        # Second run should miss cache due to hash mismatch
        with patch.object(sys, "argv", test_args):
            with patch("scripts.claudemd_linter.scan_single_file", wraps=claudemd_linter.scan_single_file) as mock_scan:
                claudemd_linter.main()
                mock_scan.assert_called_once_with(str(self.dummy_file))

    def test_no_cache_flag(self) -> None:
        """Test that the --no-cache flag bypasses the cache reading entirely."""
        test_args = ["claudemd_linter.py", str(self.dummy_file)]
        test_args_no_cache = ["claudemd_linter.py", str(self.dummy_file), "--no-cache"]

        # First run to populate cache
        with patch.object(sys, "argv", test_args):
            claudemd_linter.main()

        # Second run with --no-cache should re-scan despite unmodified file
        with patch.object(sys, "argv", test_args_no_cache):
            with patch("scripts.claudemd_linter.scan_single_file", wraps=claudemd_linter.scan_single_file) as mock_scan:
                claudemd_linter.main()
                mock_scan.assert_called_once_with(str(self.dummy_file))


if __name__ == "__main__":
    unittest.main()
