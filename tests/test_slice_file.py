import unittest
from pathlib import Path
import tempfile
import os
import shutil

from scripts.slice_file import get_file_slice


class TestSliceFile(unittest.TestCase):
    temp_dir: str
    test_file: Path
    empty_file: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.mkdtemp()

        cls.test_file = Path(cls.temp_dir) / "test_file.txt"
        cls.test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8\nLine 9\nLine 10\n", encoding="utf-8")

        cls.empty_file = Path(cls.temp_dir) / "empty_file.txt"
        cls.empty_file.write_text("", encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.temp_dir)

    def test_exact_line_range(self) -> None:
        text, start, end, total = get_file_slice(self.test_file, start=2, end=4, numbered=False)
        self.assertEqual(start, 2)
        self.assertEqual(end, 4)
        self.assertEqual(total, 10)
        self.assertEqual(text, "Line 2\nLine 3\nLine 4")

    def test_exact_line_range_numbered(self) -> None:
        text, start, end, total = get_file_slice(self.test_file, start=2, end=3, numbered=True)
        self.assertEqual(start, 2)
        self.assertEqual(end, 3)
        self.assertEqual(total, 10)
        self.assertEqual(text, "    2 | Line 2\n    3 | Line 3")

    def test_head_parameter(self) -> None:
        text, start, end, total = get_file_slice(self.test_file, head=3, numbered=False)
        self.assertEqual(start, 1)
        self.assertEqual(end, 3)
        self.assertEqual(total, 10)
        self.assertEqual(text, "Line 1\nLine 2\nLine 3")

    def test_tail_parameter(self) -> None:
        text, start, end, total = get_file_slice(self.test_file, tail=2, numbered=False)
        self.assertEqual(start, 9)
        self.assertEqual(end, 10)
        self.assertEqual(total, 10)
        self.assertEqual(text, "Line 9\nLine 10")

    def test_empty_file(self) -> None:
        text, start, end, total = get_file_slice(self.empty_file, numbered=False)
        self.assertEqual(start, 1)
        self.assertEqual(end, 0)
        self.assertEqual(total, 0)
        self.assertEqual(text, "")

    def test_start_line_greater_than_total(self) -> None:
        text, start, end, total = get_file_slice(self.test_file, start=20, numbered=False)
        self.assertEqual(start, 20)
        self.assertEqual(end, 10)
        self.assertEqual(total, 10)
        self.assertEqual(text, "")

    def test_end_line_beyond_eof(self) -> None:
        text, start, end, total = get_file_slice(self.test_file, start=8, end=20, numbered=False)
        self.assertEqual(start, 8)
        self.assertEqual(end, 10)
        self.assertEqual(total, 10)
        self.assertEqual(text, "Line 8\nLine 9\nLine 10")

    def test_negative_start_bounds(self) -> None:
        text, start, end, total = get_file_slice(self.test_file, start=-5, numbered=False)
        self.assertEqual(start, 1)
        self.assertEqual(end, 10)
        self.assertEqual(total, 10)
        self.assertTrue(text.startswith("Line 1"))
        self.assertTrue(text.endswith("Line 10"))

    def test_negative_end_bounds(self) -> None:
        text, start, end, total = get_file_slice(self.test_file, end=-5, numbered=False)
        self.assertEqual(start, 1)
        self.assertEqual(end, -5)
        self.assertEqual(total, 10)
        self.assertEqual(text, "")

    def test_non_existent_file(self) -> None:
        non_existent = Path(self.temp_dir) / "does_not_exist.txt"
        with self.assertRaises(FileNotFoundError):
            get_file_slice(non_existent)


if __name__ == "__main__":
    unittest.main()
