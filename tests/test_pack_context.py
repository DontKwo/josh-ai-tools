#!/usr/bin/env python3
"""Unit tests for pack_context.py."""
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.pack_context import get_git_diff, get_symbol_map, main, pack_files


class TestPackContext(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("subprocess.run")
    def test_get_git_diff(self, mock_run: MagicMock) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "diff text\n"
        mock_run.return_value = mock_result

        # Test unstaged
        res = get_git_diff(staged=False)
        self.assertEqual(res, "diff text")
        mock_run.assert_called_with(["git", "diff"], capture_output=True, text=True, check=False)

        # Test staged
        res = get_git_diff(staged=True)
        self.assertEqual(res, "diff text")
        mock_run.assert_called_with(["git", "diff", "--staged"], capture_output=True, text=True, check=False)

    @patch("subprocess.run")
    def test_get_git_diff_exception(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = Exception("git failed")
        res = get_git_diff()
        self.assertEqual(res, "")

    @patch("pathlib.Path.is_file")
    @patch("subprocess.run")
    def test_get_symbol_map(self, mock_run: MagicMock, mock_is_file: MagicMock) -> None:
        mock_is_file.return_value = True
        mock_result = MagicMock()
        mock_result.stdout = "symbol map\n"
        mock_run.return_value = mock_result

        res = get_symbol_map(self.temp_dir)
        self.assertEqual(res, "symbol map")

    @patch("pathlib.Path.is_file")
    def test_get_symbol_map_no_script(self, mock_is_file: MagicMock) -> None:
        mock_is_file.return_value = False
        res = get_symbol_map(self.temp_dir)
        self.assertEqual(res, "")

    @patch("pathlib.Path.is_file")
    @patch("subprocess.run")
    def test_get_symbol_map_exception(self, mock_run: MagicMock, mock_is_file: MagicMock) -> None:
        mock_is_file.return_value = True
        mock_run.side_effect = Exception("map failed")
        res = get_symbol_map(self.temp_dir)
        self.assertEqual(res, "")

    def test_pack_files(self) -> None:
        file1 = self.temp_dir / "f1.txt"
        file1.write_text("content 1", encoding="utf-8")
        file2 = self.temp_dir / "f2.txt"
        file2.write_text("content 2", encoding="utf-8")

        # test with non-existent file too
        non_existent = self.temp_dir / "f3.txt"

        blocks = pack_files([file1, file2, non_existent], self.temp_dir)
        self.assertEqual(len(blocks), 2)
        self.assertIn("### File: f1.txt", blocks[0])
        self.assertIn("content 1", blocks[0])
        self.assertIn("### File: f2.txt", blocks[1])
        self.assertIn("content 2", blocks[1])

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("scripts.pack_context.get_git_diff")
    @patch("scripts.pack_context.get_symbol_map")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_stdout(self, mock_parse_args: MagicMock, mock_get_symbol_map: MagicMock, mock_get_git_diff: MagicMock, mock_stdout: io.StringIO) -> None:
        args = MagicMock()
        args.files = []
        args.diff = True
        args.staged = False
        args.symbols = True
        args.output = None
        mock_parse_args.return_value = args

        mock_get_git_diff.return_value = "fake diff"
        mock_get_symbol_map.return_value = "fake map"

        main()

        output = mock_stdout.getvalue()
        self.assertIn("# Context Bundle", output)
        self.assertIn("## Codebase Symbol Map", output)
        self.assertIn("fake map", output)
        self.assertIn("## Git Changes", output)
        self.assertIn("fake diff", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_file_output(self, mock_parse_args: MagicMock, mock_stdout: io.StringIO) -> None:
        out_file = self.temp_dir / "out.md"
        args = MagicMock()
        args.files = []
        args.diff = False
        args.staged = False
        args.symbols = False
        args.output = out_file
        mock_parse_args.return_value = args

        main()

        self.assertTrue(out_file.is_file())
        content = out_file.read_text(encoding="utf-8")
        self.assertIn("# Context Bundle", content)

        stdout_val = mock_stdout.getvalue()
        self.assertIn("[OK] Context bundle written", stdout_val)


if __name__ == "__main__":
    unittest.main()
