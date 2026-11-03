import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import redact_diff


class TestRedactDiff(unittest.TestCase):
    def test_redact_diff_content_empty(self) -> None:
        """Test empty diff returns 'No changes detected.'"""
        redacted, orig, new = redact_diff.redact_diff_content("")
        self.assertEqual(redacted, "No changes detected.")
        self.assertEqual(orig, 0)
        self.assertEqual(new, 0)

    def test_redact_diff_content_file_boundary(self) -> None:
        """Test file boundary parsing formats as expected."""
        raw_diff = "diff --git a/file.py b/file.py\nindex 123..456\n--- a/file.py\n+++ b/file.py\n@@ -1,1 +1,1 @@\n+print('hello')"
        redacted, orig, new = redact_diff.redact_diff_content(raw_diff)
        self.assertIn("### File: `file.py`", redacted)
        self.assertIn("+print('hello')", redacted)

    def test_redact_diff_content_chunk_headers(self) -> None:
        """Test chunk headers format scope."""
        raw_diff = "diff --git a/file.py b/file.py\n@@ -10,5 +10,5 @@ def my_func():\n+    pass"
        redacted, orig, new = redact_diff.redact_diff_content(raw_diff)
        self.assertIn("* Scope: `def my_func():`", redacted)
        self.assertIn("+    pass", redacted)

    def test_redact_diff_content_noisy_context(self) -> None:
        """Test noisy context and pure whitespace churn are omitted."""
        raw_diff = "diff --git a/file.py b/file.py\n@@ -1,5 +1,5 @@\n \n+    \n-  \n+valid"
        redacted, orig, new = redact_diff.redact_diff_content(raw_diff)
        self.assertNotIn("+    ", redacted)
        self.assertNotIn("-  ", redacted)
        self.assertIn("+valid", redacted)

    def test_redact_diff_content_max_lines(self) -> None:
        """Test truncation limit."""
        raw_diff = "diff --git a/file.py b/file.py\n@@ -1,5 +1,5 @@\n+1\n+2\n+3\n+4\n+5\n"
        redacted, orig, new = redact_diff.redact_diff_content(raw_diff, max_lines=4)
        self.assertIn("_... [2 diff lines truncated for token efficiency]_", redacted)
        self.assertEqual(new, 4)

    @patch("subprocess.run")
    def test_run_git_diff_success(self, mock_run: MagicMock) -> None:
        """Test mock subprocess execution returning git diff output."""
        mock_run.return_value.stdout = "mock diff output"
        output = redact_diff.run_git_diff(["--staged"])
        self.assertEqual(output, "mock diff output")
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_git_diff_error(self, mock_run: MagicMock) -> None:
        """Test mock subprocess exception handling."""
        mock_run.side_effect = Exception("git failed")
        output = redact_diff.run_git_diff(["--staged"])
        self.assertEqual(output, "Error executing git diff: git failed")

if __name__ == "__main__":
    unittest.main()
