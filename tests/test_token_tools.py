#!/usr/bin/env python3
"""Unit tests for redact_diff and token_budget utilities."""
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.redact_diff import redact_diff_content
from scripts.token_budget import (
    CHARS_PER_TOKEN,
    analyze_file,
    estimate_tokens,
    scan_directory,
)


class TestRedactDiff(unittest.TestCase):
    def test_empty_diff_returns_no_changes(self) -> None:
        empty_text, orig_lines, redacted_lines = redact_diff_content("")
        self.assertEqual(empty_text, "No changes detected.")
        self.assertEqual(orig_lines, 0)
        self.assertEqual(redacted_lines, 0)

        whitespace_text, ws_orig, ws_redacted = redact_diff_content("   \n\t\n  ")
        self.assertEqual(whitespace_text, "No changes detected.")
        self.assertEqual(ws_orig, 0)
        self.assertEqual(ws_redacted, 0)

    def test_file_addition_and_deletion(self) -> None:
        sample_diff = (
            "diff --git a/new_file.py b/new_file.py\n"
            "new file mode 100644\n"
            "index 0000000..1234567\n"
            "--- /dev/null\n"
            "+++ b/new_file.py\n"
            "@@ -0,0 +1,2 @@\n"
            "+def added_function():\n"
            "+    return 42\n"
            "diff --git a/old_file.py b/old_file.py\n"
            "deleted file mode 100644\n"
            "index 1234567..0000000\n"
            "--- a/old_file.py\n"
            "+++ /dev/null\n"
            "@@ -1,2 +0,0 @@\n"
            "-def removed_function():\n"
            "-    return 0\n"
        )
        redacted, orig_lines, new_lines = redact_diff_content(sample_diff)
        self.assertIn("### File: `new_file.py`", redacted)
        self.assertIn("+def added_function():", redacted)
        self.assertIn("+    return 42", redacted)
        self.assertIn("### File: `old_file.py`", redacted)
        self.assertIn("-def removed_function():", redacted)
        self.assertIn("-    return 0", redacted)
        self.assertNotIn("--- /dev/null", redacted)
        self.assertNotIn("+++ b/new_file.py", redacted)
        self.assertNotIn("index 0000000..1234567", redacted)
        self.assertEqual(orig_lines, 16)
        self.assertEqual(new_lines, 9)

    def test_context_stripping_and_scope_retention(self) -> None:
        sample_diff = (
            "diff --git a/app.py b/app.py\n"
            "index 1111111..2222222 100644\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -10,6 +10,6 @@ def compute_total(items):\n"
            " \n"
            "-    rate = 1.05\n"
            "+    rate = 1.10\n"
            "+   \n"
            " \n"
        )
        redacted, orig_lines, new_lines = redact_diff_content(sample_diff)
        self.assertIn("### File: `app.py`", redacted)
        self.assertIn("* Scope: `def compute_total(items):`", redacted)
        self.assertIn("-    rate = 1.05", redacted)
        self.assertIn("+    rate = 1.10", redacted)
        self.assertNotIn(" \n", redacted)
        self.assertNotIn("+   \n", redacted)
        self.assertEqual(orig_lines, 10)
        self.assertEqual(new_lines, 5)

    def test_max_lines_truncation(self) -> None:
        lines = ["diff --git a/large.py b/large.py"]
        for idx in range(20):
            lines.append(f"+value_{idx} = {idx}")
        raw_diff = "\n".join(lines)
        redacted, orig_lines, new_lines = redact_diff_content(raw_diff, max_lines=5)
        self.assertEqual(orig_lines, 21)
        self.assertEqual(new_lines, 5)
        self.assertIn("diff lines truncated for token efficiency", redacted)


class TestTokenBudget(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_estimate_tokens_metrics(self) -> None:
        sample_text = "alpha beta gamma\none two\nthree"
        metrics = estimate_tokens(sample_text)
        expected_chars = len(sample_text)
        expected_words = len(sample_text.split())
        expected_lines = len(sample_text.splitlines())
        expected_tokens = max(1, int(expected_chars / CHARS_PER_TOKEN))

        self.assertEqual(metrics["chars"], expected_chars)
        self.assertEqual(metrics["words"], expected_words)
        self.assertEqual(metrics["lines"], expected_lines)
        self.assertEqual(metrics["tokens"], expected_tokens)

    def test_analyze_file_valid_and_missing(self) -> None:
        valid_file = self.temp_dir / "sample.py"
        valid_file.write_text("print('hello world')\n", encoding="utf-8")
        result = analyze_file(valid_file)
        self.assertIsNotNone(result)
        if result:
            self.assertEqual(result["lines"], 1)
            self.assertGreater(result["chars"], 0)

        missing_file = self.temp_dir / "non_existent.py"
        self.assertIsNone(analyze_file(missing_file))

    def test_scan_directory_and_ignored_folders(self) -> None:
        valid_sub = self.temp_dir / "src"
        valid_sub.mkdir(parents=True, exist_ok=True)
        included_file = valid_sub / "main.py"
        included_file.write_text("def run():\n    pass\n", encoding="utf-8")

        ignored_git = self.temp_dir / ".git" / "objects"
        ignored_git.mkdir(parents=True, exist_ok=True)
        git_blob = ignored_git / "blob.txt"
        git_blob.write_text("git internal metadata\n", encoding="utf-8")

        ignored_node = self.temp_dir / "node_modules" / "pkg"
        ignored_node.mkdir(parents=True, exist_ok=True)
        node_file = ignored_node / "index.js"
        node_file.write_text("module.exports = {};\n", encoding="utf-8")

        results = scan_directory(self.temp_dir)
        scanned_paths = [path.resolve() for path, _ in results]

        self.assertIn(included_file.resolve(), scanned_paths)
        self.assertNotIn(git_blob.resolve(), scanned_paths)
        self.assertNotIn(node_file.resolve(), scanned_paths)

    def test_scan_directory_target_single_file(self) -> None:
        single_target = self.temp_dir / "standalone.py"
        single_target.write_text("x = 10\n", encoding="utf-8")
        results = scan_directory(single_target)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0].resolve(), single_target.resolve())
        self.assertEqual(results[0][1]["lines"], 1)


if __name__ == "__main__":
    unittest.main()
