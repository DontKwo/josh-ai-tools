import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from sync_rules import (
    get_rule_targets,
    find_most_recent_source,
    expand_template_variables,
    sync_rules,

)

class TestSyncRules(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.ws = Path(self.temp_dir) / "workspace"
        self.ws.mkdir()
        self.home = Path(self.temp_dir) / "home"
        self.home.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir)

    @patch("sync_rules.get_user_home")
    def test_get_rule_targets(self, mock_home: MagicMock) -> None:
        mock_home.return_value = self.home
        targets = get_rule_targets(self.ws)

        # Verify supported tools
        self.assertIn("claude", targets)
        self.assertIn("antigravity", targets)
        self.assertIn("cursor", targets)
        self.assertIn("cline", targets)
        self.assertIn("codex", targets)
        self.assertIn("windsurf", targets)
        self.assertIn("copilot", targets)
        self.assertIn("aider", targets)

        # Verify global vs workspace split for claude
        self.assertEqual(targets["claude"][0], self.home / ".claude" / "CLAUDE.md")
        self.assertEqual(targets["claude"][1], self.ws / "CLAUDE.md")

    def test_find_most_recent_source(self) -> None:
        file1 = self.ws / "file1.md"
        file2 = self.ws / "file2.md"
        file1.write_text("1")
        file2.write_text("2")

        # Set mtime to make file2 newer
        os.utime(file1, (1000, 1000))
        os.utime(file2, (2000, 2000))

        targets = {"tool1": [file1, file2]}
        recent = find_most_recent_source(targets)
        self.assertEqual(recent, file2)

        # Test empty targets
        targets_empty: dict[str, list[Path]] = {"tool1": [self.ws / "nonexistent.md"]}
        self.assertIsNone(find_most_recent_source(targets_empty))

    def test_expand_template_variables(self) -> None:
        content = "{{LINTER_COMMAND}} {{ENGINEERING_RULES_PATH}} {{PYTHON_RULES_PATH}} <project_root>"
        expanded = expand_template_variables(content)

        self.assertNotIn("{{LINTER_COMMAND}}", expanded)
        self.assertNotIn("{{ENGINEERING_RULES_PATH}}", expanded)
        self.assertNotIn("{{PYTHON_RULES_PATH}}", expanded)
        self.assertNotIn("<project_root>", expanded)
        self.assertIn(".", expanded)
        self.assertTrue("claudemd_linter.py" in expanded)

    @patch("sync_rules.get_rule_targets")
    def test_sync_rules_dry_run(self, mock_targets: MagicMock) -> None:
        source_file = self.ws / "source.md"
        source_file.write_text("Hello World", encoding="utf-8")

        target_file = self.ws / "target.md"
        mock_targets.return_value = {"tool1": [target_file]}

        # Run dry run
        exit_code = sync_rules(source_file, self.ws, True)
        self.assertEqual(exit_code, 0)
        self.assertFalse(target_file.exists())

    @patch("sync_rules.get_rule_targets")
    def test_sync_rules_write(self, mock_targets: MagicMock) -> None:
        source_file = self.ws / "source.md"
        source_file.write_text("Hello World", encoding="utf-8")

        target_file = self.ws / "target.md"
        mock_targets.return_value = {"tool1": [target_file]}

        # Run write
        exit_code = sync_rules(source_file, self.ws, False)
        self.assertEqual(exit_code, 0)
        self.assertTrue(target_file.exists())
        self.assertEqual(target_file.read_text(encoding="utf-8"), "Hello World")

    @patch("sync_rules.get_rule_targets")
    def test_sync_rules_no_source(self, mock_targets: MagicMock) -> None:
        mock_targets.return_value = {"tool1": [self.ws / "target.md"]}

        with patch("sync_rules.TEMPLATE_PATH", Path(self.temp_dir) / "nonexistent.md"):
            with patch("sync_rules.find_most_recent_source", return_value=None):
                exit_code = sync_rules(None, self.ws, False)
                self.assertEqual(exit_code, 1)

if __name__ == "__main__":
    unittest.main()
