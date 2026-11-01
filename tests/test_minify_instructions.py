#!/usr/bin/env python3
"""Unit tests for minify_instructions.py."""
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.minify_instructions import main, minify_text, process_file


class TestMinifyInstructions(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_minify_text_html_comments_stripped(self) -> None:
        raw_text = "# Title <!-- inline comment -->\nContent line"
        result_text = minify_text(raw_text)
        self.assertEqual(result_text, "# Title\nContent line\n")

    def test_minify_text_multiline_comments_stripped(self) -> None:
        raw_text = "Before comment <!-- Multi-line\ncomment spanning\nmultiple lines --> After comment"
        result_text = minify_text(raw_text)
        self.assertEqual(result_text, "Before comment  After comment\n")

    def test_minify_text_trailing_whitespace_removed(self) -> None:
        raw_text = "First line with spaces   \nSecond line with tabs\t\t\nThird line"
        result_text = minify_text(raw_text)
        self.assertEqual(result_text, "First line with spaces\nSecond line with tabs\nThird line\n")

    def test_minify_text_consecutive_blank_lines_collapsed(self) -> None:
        raw_text = "Header\n\n\n\nMiddle\n\n\n\nFooter"
        result_text = minify_text(raw_text)
        self.assertEqual(result_text, "Header\n\nMiddle\n\nFooter\n")

    def test_minify_text_outer_blank_lines_trimmed(self) -> None:
        raw_text = "\n\n\n   \nOnly content line\n\n\n   \n"
        result_text = minify_text(raw_text)
        self.assertEqual(result_text, "Only content line\n")

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_process_file_output_mode(self, mock_stdout: io.StringIO) -> None:
        source_file = self.temp_dir / "instructions.md"
        dest_file = self.temp_dir / "instructions_output.md"
        original_content = "# Guide <!-- Note -->\nLine with space   \n\n\nNext line\n"
        source_file.write_text(original_content, encoding="utf-8")

        process_file(source_file, in_place=False, output_path=dest_file)

        self.assertTrue(dest_file.is_file())
        self.assertEqual(source_file.read_text(encoding="utf-8"), original_content)
        expected_minified = "# Guide\nLine with space\n\nNext line\n"
        self.assertEqual(dest_file.read_text(encoding="utf-8"), expected_minified)

        output_log = mock_stdout.getvalue()
        self.assertIn("[OK] Minified instructions.md -> instructions_output.md", output_log)
        self.assertIn("Bytes:", output_log)
        self.assertIn("Tokens: ~", output_log)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_process_file_default_output_suffix(self, mock_stdout: io.StringIO) -> None:
        source_file = self.temp_dir / "test_rules.md"
        source_file.write_text("# Rules <!-- Remove -->\nContent", encoding="utf-8")

        process_file(source_file, in_place=False, output_path=None)

        expected_target = self.temp_dir / "test_rules.min.md"
        self.assertTrue(expected_target.is_file())
        self.assertEqual(expected_target.read_text(encoding="utf-8"), "# Rules\nContent\n")

        output_log = mock_stdout.getvalue()
        self.assertIn("[OK] Minified test_rules.md -> test_rules.min.md", output_log)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_process_file_in_place(self, mock_stdout: io.StringIO) -> None:
        source_file = self.temp_dir / "in_place.md"
        source_file.write_text("# In Place <!-- Strip me -->\nData line\n\n\nEnd line\n", encoding="utf-8")

        process_file(source_file, in_place=True, output_path=None)

        expected_minified = "# In Place\nData line\n\nEnd line\n"
        self.assertEqual(source_file.read_text(encoding="utf-8"), expected_minified)

        output_log = mock_stdout.getvalue()
        self.assertIn("[OK] Minified in_place.md -> in_place.md", output_log)
        self.assertIn("Bytes:", output_log)
        self.assertIn("Tokens: ~", output_log)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_process_file_empty_content(self, mock_stdout: io.StringIO) -> None:
        source_file = self.temp_dir / "empty.md"
        source_file.write_text("", encoding="utf-8")

        process_file(source_file, in_place=True, output_path=None)

        self.assertEqual(source_file.read_text(encoding="utf-8"), "\n")
        output_log = mock_stdout.getvalue()
        self.assertIn("[OK] Minified empty.md -> empty.md", output_log)
        self.assertIn("0.0%", output_log)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("scripts.minify_instructions.process_file")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_valid_file(self, mock_parse_args: MagicMock, mock_process_file: MagicMock, mock_stdout: io.StringIO) -> None:
        source_file = self.temp_dir / "sample.md"
        source_file.write_text("# Test", encoding="utf-8")
        out_file = self.temp_dir / "sample_out.md"

        parsed_arguments = MagicMock()
        parsed_arguments.file = str(source_file)
        parsed_arguments.in_place = False
        parsed_arguments.output = str(out_file)
        mock_parse_args.return_value = parsed_arguments

        main()

        mock_process_file.assert_called_once_with(source_file.resolve(), False, out_file.resolve())

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_file_not_found(self, mock_parse_args: MagicMock, mock_stdout: io.StringIO) -> None:
        missing_file = self.temp_dir / "nonexistent.md"

        parsed_arguments = MagicMock()
        parsed_arguments.file = str(missing_file)
        parsed_arguments.in_place = False
        parsed_arguments.output = None
        mock_parse_args.return_value = parsed_arguments

        with self.assertRaises(SystemExit) as exit_context:
            main()

        self.assertEqual(exit_context.exception.code, 1)
        self.assertIn("Error: File not found", mock_stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
