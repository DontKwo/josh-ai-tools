import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO
import sys

# Append scripts dir so we can import modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import install_hooks
import install_antigravity_hooks

class TestInstallHooks(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name).resolve()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_hook_content(self) -> None:
        content = install_hooks.create_hook_content()
        self.assertTrue(content.startswith("#!/usr/bin/env sh"))
        self.assertIn("claudemd_linter.py", content)
        self.assertIn("--staged", content)

    @patch("sys.stdout", new_callable=StringIO)
    def test_install_hook_no_git(self, mock_stdout: StringIO) -> None:
        install_hooks.install_hook(self.temp_path, action="overwrite")
        self.assertIn("not a git repository", mock_stdout.getvalue())

    def test_install_hook_success(self) -> None:
        git_dir = self.temp_path / ".git"
        git_dir.mkdir()
        install_hooks.install_hook(self.temp_path, action="overwrite")

        hook_file = git_dir / "hooks" / "pre-commit"
        self.assertTrue(hook_file.exists())
        content = hook_file.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("#!/usr/bin/env sh"))

        # Check permissions on POSIX
        if os.name != "nt":
            mode = hook_file.stat().st_mode
            self.assertTrue(mode & stat.S_IXUSR)

    @patch("sys.stdout", new_callable=StringIO)
    def test_uninstall_hook(self, mock_stdout: StringIO) -> None:
        git_dir = self.temp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        hook_file = hooks_dir / "pre-commit"
        hook_file.write_text("fake hook", encoding="utf-8")

        install_hooks.uninstall_hook(self.temp_path)
        self.assertFalse(hook_file.exists())
        self.assertIn("Removed pre-commit hook", mock_stdout.getvalue())

class TestInstallAntigravityHooks(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name).resolve()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @patch("install_antigravity_hooks.get_user_home")
    def test_get_hook_paths(self, mock_home: MagicMock) -> None:
        mock_home.return_value = self.temp_path / "home"
        paths = install_antigravity_hooks.get_hook_paths(self.temp_path)

        self.assertIn("workspace", paths)
        self.assertIn("global", paths)
        self.assertEqual(paths["workspace"][0], self.temp_path / ".agent" / "hooks.json")
        self.assertEqual(paths["global"][0], self.temp_path / "home" / ".gemini" / "config" / "hooks.json")

    def test_build_hook_config(self) -> None:
        config = install_antigravity_hooks.build_hook_config("fake cmd", "Stop")
        self.assertIn("josh-linter-completion-guard", config)
        guard = config["josh-linter-completion-guard"]
        self.assertIn("Stop", guard)
        self.assertEqual(guard["Stop"][0]["command"], "fake cmd")

    def test_install_hook(self) -> None:
        dest = self.temp_path / "hooks.json"
        install_antigravity_hooks.install_hook(dest, "fake cmd")

        self.assertTrue(dest.exists())
        data = json.loads(dest.read_text(encoding="utf-8"))
        self.assertIn("josh-linter-completion-guard", data)

    def test_remove_hook(self) -> None:
        dest = self.temp_path / "hooks.json"
        install_antigravity_hooks.install_hook(dest, "fake cmd")

        res = install_antigravity_hooks.remove_hook(dest)
        self.assertTrue(res)
        data = json.loads(dest.read_text(encoding="utf-8"))
        self.assertNotIn("josh-linter-completion-guard", data)

if __name__ == "__main__":
    unittest.main()
