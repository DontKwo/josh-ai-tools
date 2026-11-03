#!/usr/bin/env python3
"""Unit tests for spell_checker.py script."""
import tempfile
import unittest
from pathlib import Path

from scripts.spell_checker import (
    check_line_spelling,
    audit_file_native,
    scan_target,
    split_identifier_words,
)


class TestSpellChecker(unittest.TestCase):

    def test_split_identifier_words(self) -> None:
        self.assertEqual(split_identifier_words("camelCase"), ["camel", "Case"])
        self.assertEqual(split_identifier_words("PascalCase"), ["Pascal", "Case"])
        self.assertEqual(split_identifier_words("simple"), ["simple"])
        self.assertEqual(split_identifier_words("XMLHttpRequest"), ["XML", "Http", "Request"])
        self.assertEqual(split_identifier_words("calc_max_val"), ["calc", "max", "val"])
        self.assertEqual(split_identifier_words("get_User_Profile"), ["get", "User", "Profile"])

    def test_check_line_spelling_typos(self) -> None:
        line = "def recieve_data(arguement):  # This is neccessary"
        findings = check_line_spelling(line)
        self.assertEqual(len(findings), 3)

        wrong_words = [f[0].lower() for f in findings]
        self.assertIn("recieve", wrong_words)
        self.assertIn("arguement", wrong_words)
        self.assertIn("neccessary", wrong_words)

    def test_check_line_spelling_clean(self) -> None:
        line = "import os\nimport sys\ndef receive_data(argument):  # This is necessary"
        findings = check_line_spelling(line)
        self.assertEqual(len(findings), 0)

    def test_audit_file_native(self) -> None:
        code = '''
# occurence of a bug
def do_something() -> None:
    dependancy = True
'''
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(code)
            path = Path(f.name)

        try:
            findings = audit_file_native(path)
            self.assertEqual(len(findings), 2)
            wrong_words = [f[1].lower() for f in findings]
            self.assertIn("occurence", wrong_words)
            self.assertIn("dependancy", wrong_words)
        finally:
            path.unlink()

    def test_scan_target_ignored_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            ignored_dir = temp_path / "node_modules"
            ignored_dir.mkdir()

            test_file = ignored_dir / "test.py"
            test_file.write_text("def recieve(): pass", encoding="utf-8")

            findings = scan_target(temp_path, use_external=False)
            self.assertEqual(len(findings), 0)

    def test_custom_dictionary_ignore(self) -> None:
        line = "def recieve_data(): pass"

        findings_before = check_line_spelling(line)
        self.assertEqual(len(findings_before), 1)

        findings_after = check_line_spelling(line, ignore={"recieve"})
        self.assertEqual(len(findings_after), 0)

    def test_audit_file_with_ignore(self) -> None:
        code = '''
# occurence of a bug
def do_something() -> None:
    dependancy = True
'''
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(code)
            path = Path(f.name)

        try:
            findings = audit_file_native(path, ignore={"occurence"})
            self.assertEqual(len(findings), 1)
            wrong_words = [f[1].lower() for f in findings]
            self.assertIn("dependancy", wrong_words)
            self.assertNotIn("occurence", wrong_words)
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
