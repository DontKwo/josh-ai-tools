#!/usr/bin/env python3
"""Unit tests for the lint_fixer safe auto-fixer script."""
import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.lint_fixer import fix_file, fix_line, process_file


class TestLintFixerUnicode(unittest.TestCase):
    """Test unicode normalization (Rule 2)."""

    def test_curly_quotes_normalization(self) -> None:
        raw = "‘single’ and “double”\n"
        fixed, changes = fix_line(raw, 1, Path("example.py"), fix_emojis=False)
        self.assertEqual(fixed, "'single' and \"double\"\n")
        self.assertEqual(len(changes), 4)

    def test_ellipsis_normalization(self) -> None:
        raw = "loading…\n"
        fixed, changes = fix_line(raw, 1, Path("example.py"), fix_emojis=False)
        self.assertEqual(fixed, "loading...\n")
        self.assertEqual(len(changes), 1)

    def test_non_breaking_spaces_normalization(self) -> None:
        raw = "word1\u00a0word2\n"
        fixed, changes = fix_line(raw, 1, Path("example.py"), fix_emojis=False)
        self.assertEqual(fixed, "word1 word2\n")
        self.assertEqual(len(changes), 1)

    def test_bom_removal(self) -> None:
        raw = "\ufeffcontent\n"
        fixed, changes = fix_line(raw, 1, Path("example.py"), fix_emojis=False)
        self.assertEqual(fixed, "content\n")
        self.assertEqual(len(changes), 1)

    def test_additional_unicode_replacements(self) -> None:
        raw = "zero\u200bwidth, soft\u00adhyphen, prime\u2032 and double\u2033\n"
        fixed, changes = fix_line(raw, 1, Path("example.py"), fix_emojis=False)
        self.assertEqual(fixed, "zerowidth, softhyphen, prime' and double\"\n")
        self.assertEqual(len(changes), 4)


class TestLintFixerMechanicalOperators(unittest.TestCase):
    """Test mechanical operator fixes (Rule 15)."""

    def test_eq_none_replacement(self) -> None:
        raw = "if val == None:\n"
        fixed, changes = fix_line(raw, 1, Path("test.py"), fix_emojis=False)
        self.assertEqual(fixed, "if val is None:\n")
        self.assertEqual(len(changes), 1)

    def test_ne_none_replacement(self) -> None:
        raw = "if result != None:\n"
        fixed, changes = fix_line(raw, 1, Path("test.py"), fix_emojis=False)
        self.assertEqual(fixed, "if result is not None:\n")
        self.assertEqual(len(changes), 1)

    def test_both_operators_same_line(self) -> None:
        raw = "if a == None or b != None:\n"
        fixed, changes = fix_line(raw, 1, Path("test.py"), fix_emojis=False)
        self.assertEqual(fixed, "if a is None or b is not None:\n")
        self.assertEqual(len(changes), 2)

    def test_non_python_files_skip_operator_fixes(self) -> None:
        raw = "if (a == None || b != None) {\n"
        fixed, changes = fix_line(raw, 1, Path("test.js"), fix_emojis=False)
        self.assertEqual(fixed, raw)
        self.assertEqual(len(changes), 0)


class TestLintFixerAiBanner(unittest.TestCase):
    """Test AI divider banner removal and condensing (Rule 41)."""

    def test_python_banner_condensed(self) -> None:
        raw = "### =================== ###\n"
        fixed, changes = fix_line(raw, 1, Path("test.py"), fix_emojis=False, fix_banners=True)
        self.assertEqual(fixed, "# ---\n")
        self.assertEqual(len(changes), 1)

    def test_indented_python_banner(self) -> None:
        raw = "    ########################\n"
        fixed, changes = fix_line(raw, 1, Path("test.py"), fix_emojis=False, fix_banners=True)
        self.assertEqual(fixed, "    # ---\n")
        self.assertEqual(len(changes), 1)

    def test_javascript_banner_condensed(self) -> None:
        raw = "// ==========================\n"
        fixed, changes = fix_line(raw, 1, Path("test.js"), fix_emojis=False, fix_banners=True)
        self.assertEqual(fixed, "// ---\n")
        self.assertEqual(len(changes), 1)

    def test_banner_disabled_flag(self) -> None:
        raw = "### =================== ###\n"
        fixed, changes = fix_line(raw, 1, Path("test.py"), fix_emojis=False, fix_banners=False)
        self.assertEqual(fixed, raw)
        self.assertEqual(len(changes), 0)


class TestLintFixerEmoji(unittest.TestCase):
    """Test emoji stripping (--fix-emojis)."""

    def test_emoji_stripped_when_enabled(self) -> None:
        raw = "Warning: 🐱 error detected 🚀\n"
        fixed, changes = fix_line(raw, 1, Path("test.py"), fix_emojis=True)
        self.assertNotIn("🐱", fixed)
        self.assertNotIn("🚀", fixed)
        self.assertEqual(fixed, "Warning:  error detected \n")
        self.assertIn("Rule 3 (removed emoji)", changes)

    def test_emoji_preserved_when_disabled(self) -> None:
        raw = "Status: 🚀 and ⚠️\n"
        fixed, changes = fix_line(raw, 1, Path("test.py"), fix_emojis=False)
        self.assertEqual(fixed, raw)
        self.assertEqual(len(changes), 0)


class TestLintFixerEmDashSafety(unittest.TestCase):
    """Verify critical safety guarantee regarding em dashes."""

    def test_em_dash_line_never_modified_and_emits_warning(self) -> None:
        raw = "Before — after ‘smart quotes’ and == None\n"
        captured = io.StringIO()
        with redirect_stdout(captured):
            fixed, changes = fix_line(raw, 42, Path("critical.py"), fix_emojis=True)

        self.assertIn("\u2014", fixed)
        self.assertIn("‘smart quotes’", fixed)
        output = captured.getvalue()
        self.assertIn("[!] Skipped Rule 1 (em dash) at critical.py:42", output)
        self.assertIn("Manual sentence rewrite required", output)


class TestLintFixerFileProcessing(unittest.TestCase):
    """Test file processing with temporary files (dry-run vs. in-place)."""

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_dry_run_does_not_modify_file(self) -> None:
        file_path = self.temp_dir / "dry_run_test.py"
        original = "x = None\nif x == None:\n    msg = ‘hello’\n"
        file_path.write_text(original, encoding="utf-8")

        count = fix_file(file_path, dry_run=True, fix_emojis=False)
        self.assertGreater(count, 0)
        self.assertEqual(file_path.read_text(encoding="utf-8"), original)

    def test_in_place_modifications(self) -> None:
        file_path = self.temp_dir / "inplace_test.py"
        original = "if a == None or b != None:\n    s = “test”\n"
        file_path.write_text(original, encoding="utf-8")

        count = fix_file(file_path, dry_run=False, fix_emojis=False)
        self.assertEqual(count, 4)
        updated = file_path.read_text(encoding="utf-8")
        self.assertEqual(updated, 'if a is None or b is not None:\n    s = "test"\n')

    def test_process_file_alias(self) -> None:
        file_path = self.temp_dir / "alias_test.py"
        original = "if x == None:\n    val = ‘alias’\n"
        file_path.write_text(original, encoding="utf-8")

        count = process_file(file_path, dry_run=False, fix_emojis=False)
        self.assertGreater(count, 0)
        updated = file_path.read_text(encoding="utf-8")
        self.assertIn("if x is None:", updated)
        self.assertIn("'alias'", updated)

    def test_unreadable_file_handling(self) -> None:
        missing_file = self.temp_dir / "nonexistent.py"
        count = fix_file(missing_file, dry_run=False, fix_emojis=False)
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
