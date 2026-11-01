#!/usr/bin/env python3
"""Unit tests for dir_overview.py."""
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.dir_overview import count_lines_and_size, main, render_tree


class TestDirOverview(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_count_lines_and_size(self) -> None:
        file_ascii = self.temp_dir / "ascii.txt"
        file_ascii.write_text("line1\nline2\nline3\n", encoding="ascii")
        lines, size_kb = count_lines_and_size(file_ascii)
        self.assertEqual(lines, 3)
        self.assertAlmostEqual(size_kb, file_ascii.stat().st_size / 1024, places=4)

        file_utf8 = self.temp_dir / "utf8.txt"
        file_utf8.write_text("alpha\nbeta\n", encoding="utf-8")
        lines_u, size_u = count_lines_and_size(file_utf8)
        self.assertEqual(lines_u, 2)
        self.assertAlmostEqual(size_u, file_utf8.stat().st_size / 1024, places=4)

    def test_count_lines_and_size_nonexistent_and_unreadable(self) -> None:
        missing_file = self.temp_dir / "missing.txt"
        lines, size_kb = count_lines_and_size(missing_file)
        self.assertEqual(lines, 0)
        self.assertEqual(size_kb, 0.0)

        dir_as_file = self.temp_dir / "subdir"
        dir_as_file.mkdir()
        lines_dir, size_dir = count_lines_and_size(dir_as_file)
        self.assertEqual(lines_dir, 0)
        self.assertEqual(size_dir, 0.0)

    def test_render_tree_hierarchical(self) -> None:
        sub = self.temp_dir / "pkg"
        sub.mkdir()
        mod = sub / "mod.py"
        mod.write_text("print(1)\n", encoding="utf-8")
        root_file = self.temp_dir / "main.py"
        root_file.write_text("import pkg\n", encoding="utf-8")

        lines = render_tree(self.temp_dir)
        self.assertTrue(any("pkg/" in line for line in lines))
        self.assertTrue(any("mod.py" in line for line in lines))
        self.assertTrue(any("main.py" in line for line in lines))

    def test_render_tree_default_ignores_and_hidden(self) -> None:
        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git config", encoding="utf-8")

        node_dir = self.temp_dir / "node_modules"
        node_dir.mkdir()
        (node_dir / "package.json").write_text("{}", encoding="utf-8")

        hidden_file = self.temp_dir / ".hidden"
        hidden_file.write_text("secret", encoding="utf-8")

        regular_file = self.temp_dir / "app.py"
        regular_file.write_text("code", encoding="utf-8")

        lines = render_tree(self.temp_dir)
        for line in lines:
            self.assertNotIn(".git", line)
            self.assertNotIn("node_modules", line)
            self.assertNotIn(".hidden", line)
        self.assertTrue(any("app.py" in line for line in lines))

    def test_render_tree_max_depth(self) -> None:
        lvl1 = self.temp_dir / "lvl1"
        lvl1.mkdir()
        lvl2 = lvl1 / "lvl2"
        lvl2.mkdir()
        deep_file = lvl2 / "deep.txt"
        deep_file.write_text("deep", encoding="utf-8")

        lines_depth_0 = render_tree(self.temp_dir, max_depth=0)
        self.assertTrue(any("lvl1/" in line for line in lines_depth_0))
        self.assertFalse(any("lvl2/" in line for line in lines_depth_0))
        self.assertFalse(any("deep.txt" in line for line in lines_depth_0))

        lines_depth_1 = render_tree(self.temp_dir, max_depth=1)
        self.assertTrue(any("lvl1/" in line for line in lines_depth_1))
        self.assertTrue(any("lvl2/" in line for line in lines_depth_1))
        self.assertFalse(any("deep.txt" in line for line in lines_depth_1))

    def test_render_tree_allowed_exts(self) -> None:
        f_py = self.temp_dir / "sample.py"
        f_py.write_text("x = 1\n", encoding="utf-8")
        f_txt = self.temp_dir / "sample.txt"
        f_txt.write_text("text\n", encoding="utf-8")
        f_md = self.temp_dir / "sample.md"
        f_md.write_text("# doc\n", encoding="utf-8")

        lines = render_tree(self.temp_dir, allowed_exts={".py", ".md"})
        self.assertTrue(any("sample.py" in line for line in lines))
        self.assertTrue(any("sample.md" in line for line in lines))
        self.assertFalse(any("sample.txt" in line for line in lines))

    def test_render_tree_max_files(self) -> None:
        for i in range(5):
            f = self.temp_dir / f"file_{i}.txt"
            f.write_text(f"content {i}\n", encoding="utf-8")

        lines = render_tree(self.temp_dir, max_files=2)
        limit_lines = [line for line in lines if "Limit reached: 2 files displayed" in line]
        self.assertEqual(len(limit_lines), 1)

    def test_render_tree_stats(self) -> None:
        f = self.temp_dir / "stats_test.py"
        f.write_text("a = 1\nb = 2\nc = 3\n", encoding="utf-8")

        lines = render_tree(self.temp_dir, stats=True)
        stat_line = [line for line in lines if "stats_test.py" in line][0]
        self.assertIn("3 lines", stat_line)
        self.assertIn("KB", stat_line)

    @patch("pathlib.Path.iterdir")
    def test_render_tree_permission_denied(self, mock_iterdir: MagicMock) -> None:
        mock_iterdir.side_effect = PermissionError("Access denied")
        lines = render_tree(self.temp_dir)
        self.assertEqual(lines, ["[Permission Denied]"])

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_main_success(self, mock_stdout: io.StringIO) -> None:
        target_file = self.temp_dir / "test.py"
        target_file.write_text("x = 1\n", encoding="utf-8")

        test_args = ["dir_overview.py", str(self.temp_dir), "--stats", "--ext", "py", "-d", "2"]
        with patch("sys.argv", test_args):
            exit_code = main()
        self.assertEqual(exit_code, 0)
        output = mock_stdout.getvalue()
        self.assertIn(f"{self.temp_dir.name}/", output)
        self.assertIn("test.py", output)
        self.assertIn("1 lines", output)

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_main_nonexistent_directory(self, mock_stderr: io.StringIO) -> None:
        missing_dir = self.temp_dir / "does_not_exist"
        test_args = ["dir_overview.py", str(missing_dir)]
        with patch("sys.argv", test_args):
            exit_code = main()
        self.assertEqual(exit_code, 1)
        err_output = mock_stderr.getvalue()
        self.assertIn("Directory does not exist", err_output)


if __name__ == "__main__":
    unittest.main()
