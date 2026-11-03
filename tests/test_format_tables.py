import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to sys.path for tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import format_tables

class TestFormatTables(unittest.TestCase):
    def test_extract_rows(self) -> None:
        lines = [
            "| col1 | col2 |",
            "|---|---|",
            "| 1 | 2 |"
        ]
        rows = format_tables.extract_rows(lines)
        self.assertEqual(rows[0], ["col1", "col2"])
        self.assertEqual(rows[1], ["---", "---"])
        self.assertEqual(rows[2], ["1", "2"])

    def test_determine_alignment(self) -> None:
        delim_row = ["---", ":---", "---:", ":---:"]
        aligns = format_tables.determine_alignment(delim_row)
        self.assertEqual(aligns, ["left", "left", "right", "center"])

    def test_format_cell(self) -> None:
        self.assertEqual(format_tables.format_cell("a", 5, "left"), "a    ")
        self.assertEqual(format_tables.format_cell("a", 5, "right"), "    a")
        self.assertEqual(format_tables.format_cell("a", 5, "center"), "  a  ")

    def test_format_table(self) -> None:
        lines = [
            "| a | b | c |",
            "|---|:---:|---:|",
            "|1|200|3000|"
        ]
        formatted = format_tables.format_table(lines)
        self.assertEqual(formatted[0], "| a   |  b  |    c |")
        self.assertEqual(formatted[1], "| --- | :-: | ---: |")
        self.assertEqual(formatted[2], "| 1   | 200 | 3000 |")

    def test_process_content(self) -> None:
        content = (
            "Some text.\n"
            "\n"
            "| a | b |\n"
            "|--|--:|\n"
            "|1|200|\n"
            "\n"
            "```\n"
            "| not | a | table |\n"
            "```\n"
        )
        formatted = format_tables.process_content(content)
        expected = (
            "Some text.\n"
            "\n"
            "| a   |   b |\n"
            "| --- | --: |\n"
            "| 1   | 200 |\n"
            "\n"
            "```\n"
            "| not | a | table |\n"
            "```\n"
        )
        self.assertEqual(formatted, expected)

    def test_process_file_check_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()
            test_file = temp_path / "test.md"
            test_file.write_text("|a|b|\n|---|---|\n|1|2|\n", encoding="utf-8")

            is_ok = format_tables.process_file(test_file, check_only=True)
            self.assertFalse(is_ok)

    def test_process_file_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()
            test_file = temp_path / "test.md"
            test_file.write_text("|a|b|\n|---|---|\n|1|2|\n", encoding="utf-8")

            is_ok = format_tables.process_file(test_file, check_only=False)
            self.assertTrue(is_ok)

            content = test_file.read_text(encoding="utf-8")
            expected = "| a   | b   |\n| --- | --- |\n| 1   | 2   |\n"
            self.assertEqual(content, expected)

    def test_main(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()
            test_file = temp_path / "test.md"
            test_file.write_text("|a|b|\n|---|---|\n|1|2|\n", encoding="utf-8")

            ret_code = format_tables.main([str(test_file), "--check"])
            self.assertEqual(ret_code, 1)

            ret_code = format_tables.main([str(test_file), "--write"])
            self.assertEqual(ret_code, 0)

            ret_code = format_tables.main([str(test_file), "--check"])
            self.assertEqual(ret_code, 0)

if __name__ == "__main__":
    unittest.main()
