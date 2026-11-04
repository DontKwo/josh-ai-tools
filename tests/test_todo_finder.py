"""Tests for the todo_finder.py script."""

import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from todo_finder import TodoItem, scan_file, scan_directory  # noqa: 12, 13


class TestTodoFinder(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir).resolve()

    def tearDown(self) -> None:
        for f in self.temp_path.rglob("*"):
            if f.is_file():
                f.unlink()
        for d in sorted(self.temp_path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if d.is_dir():
                d.rmdir()
        self.temp_path.rmdir()

    def test_scan_file(self) -> None:
        test_file = self.temp_path / "test.py"
        test_file.write_text(
            "# TODO(josh): Fix this bug\n"
            "print('hello')  # FIXME: refactor\n"
            "// BUG: oops\n"
            "/* HACK(dev): temp workaround */\n"
            "<!-- NOTE: test -->\n"
            "# OPTIMIZE: make it faster\n",
            encoding="utf-8"
        )

        items = scan_file(test_file)
        self.assertEqual(len(items), 6)

        self.assertEqual(items[0], TodoItem("TODO", str(test_file), 1, "josh", "Fix this bug"))
        self.assertEqual(items[1], TodoItem("FIXME", str(test_file), 2, None, "refactor"))
        self.assertEqual(items[2], TodoItem("BUG", str(test_file), 3, None, "oops"))
        self.assertEqual(items[3], TodoItem("HACK", str(test_file), 4, "dev", "temp workaround"))
        self.assertEqual(items[4], TodoItem("NOTE", str(test_file), 5, None, "test"))
        self.assertEqual(items[5], TodoItem("OPTIMIZE", str(test_file), 6, None, "make it faster"))

    def test_scan_directory(self) -> None:
        test_file1 = self.temp_path / "test1.py"
        test_file1.write_text("# TODO: task 1\n", encoding="utf-8")

        test_file2 = self.temp_path / "test2.js"
        test_file2.write_text("// FIXME: task 2\n", encoding="utf-8")

        items = scan_directory(self.temp_path)
        self.assertEqual(len(items), 2)

        tags = {item.tag for item in items}
        self.assertIn("TODO", tags)
        self.assertIn("FIXME", tags)

    def test_exclude_directories(self) -> None:
        test_dir = self.temp_path / "venv"
        test_dir.mkdir()
        test_file = test_dir / "test.py"
        test_file.write_text("# TODO: should be ignored\n", encoding="utf-8")

        items = scan_directory(self.temp_path)
        self.assertEqual(len(items), 0)

if __name__ == "__main__":
    unittest.main()
