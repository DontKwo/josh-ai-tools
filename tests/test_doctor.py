import json
import subprocess
import tempfile
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.doctor import check_installed_skills, inspect_mcp_config, check_git_tracking, check_python_version


class TestDoctor(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_check_installed_skills(self) -> None:
        # A better approach for pathlib testing is to actually create temp files
        repo = self.root / "repo"
        skills = repo / "skills"
        skills.mkdir(parents=True)

        (skills / "skill1").mkdir()
        (skills / "skill2").mkdir()
        (skills / "not_a_dir").touch()

        home_dir = self.root / "home"
        dest_skills = home_dir / ".gemini" / "antigravity" / "skills"
        dest_skills.mkdir(parents=True)

        # Install skill 1 correctly
        skill1_dest = dest_skills / "skill1"
        skill1_dest.mkdir()
        (skill1_dest / "SKILL.md").touch()

        # Skill 2 missing

        status = check_installed_skills(repo, home_dir)
        self.assertIn("skill1", status)
        self.assertIn("skill2", status)
        self.assertNotIn("not_a_dir", status)
        self.assertTrue(status["skill1"])
        self.assertFalse(status["skill2"])

    def test_inspect_mcp_config_missing(self) -> None:
        mcp_path = self.root / "missing.json"
        info = inspect_mcp_config(mcp_path)
        self.assertFalse(info["exists"])

    def test_inspect_mcp_config_corrupted(self) -> None:
        mcp_path = self.root / "corrupted.json"
        mcp_path.write_text("{ invalid json", encoding="utf-8")
        info = inspect_mcp_config(mcp_path)
        self.assertTrue(info["exists"])
        self.assertTrue(info["corrupted"])

    def test_inspect_mcp_config_not_registered(self) -> None:
        mcp_path = self.root / "not_registered.json"
        mcp_path.write_text(json.dumps({"mcpServers": {"other-tool": {}}}), encoding="utf-8")
        info = inspect_mcp_config(mcp_path)
        self.assertTrue(info["exists"])
        self.assertFalse(info["is_registered"])

    def test_inspect_mcp_config_valid(self) -> None:
        mcp_path = self.root / "valid.json"

        cmd_path = self.root / "python"
        cmd_path.touch()

        script_path = self.root / "server.py"
        script_path.touch()

        config = {
            "mcpServers": {
                "josh-ai-tools": {
                    "command": str(cmd_path),
                    "args": ["run", str(script_path)]
                }
            }
        }
        mcp_path.write_text(json.dumps(config), encoding="utf-8")

        info = inspect_mcp_config(mcp_path)
        self.assertTrue(info["exists"])
        self.assertTrue(info["is_registered"])
        self.assertFalse(info["corrupted"])
        self.assertTrue(info["command_valid"])
        self.assertTrue(info["script_valid"])

    def test_inspect_mcp_config_invalid_paths(self) -> None:
        mcp_path = self.root / "invalid.json"

        config = {
            "mcpServers": {
                "josh-ai-tools": {
                    "command": "/does/not/exist",
                    "args": ["run", "/also/missing/server.py"]
                }
            }
        }
        mcp_path.write_text(json.dumps(config), encoding="utf-8")

        info = inspect_mcp_config(mcp_path)
        self.assertTrue(info["exists"])
        self.assertTrue(info["is_registered"])
        self.assertFalse(info["command_valid"])
        self.assertFalse(info["script_valid"])

    @patch("scripts.doctor.shutil.which")
    def test_check_git_tracking_no_git(self, mock_which: MagicMock) -> None:
        mock_which.return_value = None
        info = check_git_tracking(self.root)
        self.assertFalse(info["has_git"])

    @patch("scripts.doctor.shutil.which")
    @patch("scripts.doctor.subprocess.run")
    def test_check_git_tracking_not_repo(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"
        mock_run.side_effect = subprocess.CalledProcessError(128, "git")
        info = check_git_tracking(self.root)
        self.assertTrue(info["has_git"])
        self.assertFalse(info["is_repo"])

    @patch("scripts.doctor.shutil.which")
    @patch("scripts.doctor.subprocess.run")
    def test_check_git_tracking_no_remote(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"

        # First call works (is repo), second call fails (no remote)
        mock_is_inside = MagicMock()
        mock_is_inside.returncode = 0

        mock_remote = MagicMock()
        mock_remote.returncode = 128

        mock_run.side_effect = [mock_is_inside, mock_remote]

        info = check_git_tracking(self.root)
        self.assertTrue(info["is_repo"])
        self.assertFalse(info["has_tracking"])
        self.assertEqual(info["branch"], "")

    @patch("scripts.doctor.shutil.which")
    @patch("scripts.doctor.subprocess.run")
    def test_check_git_tracking_success(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/git"

        mock_is_inside = MagicMock()
        mock_is_inside.returncode = 0

        mock_remote = MagicMock()
        mock_remote.returncode = 0
        mock_remote.stdout = "origin/main\n"

        mock_run.side_effect = [mock_is_inside, mock_remote]

        info = check_git_tracking(self.root)
        self.assertTrue(info["is_repo"])
        self.assertTrue(info["has_tracking"])
        self.assertEqual(info["branch"], "origin/main")

    def test_check_python_version_no_toml(self) -> None:
        info = check_python_version(self.root)
        self.assertFalse(info["has_toml"])

    def test_check_python_version_no_requires(self) -> None:
        toml = self.root / "pyproject.toml"
        toml.write_text("[tool.something]\nkey = 'value'", encoding="utf-8")
        info = check_python_version(self.root)
        self.assertTrue(info["has_toml"])
        self.assertEqual(info["requires_python"], "")
        self.assertTrue(info["meets_req"])

    @patch("scripts.doctor.sys.version_info")
    def test_check_python_version_meets_req(self, mock_version: MagicMock) -> None:
        mock_version.major = 3
        mock_version.minor = 10

        toml = self.root / "pyproject.toml"
        toml.write_text("requires-python = '>=3.9'", encoding="utf-8")

        info = check_python_version(self.root)
        self.assertTrue(info["has_toml"])
        self.assertEqual(info["requires_python"], ">=3.9")
        self.assertTrue(info["meets_req"])

    @patch("scripts.doctor.sys.version_info")
    def test_check_python_version_fails_req(self, mock_version: MagicMock) -> None:
        mock_version.major = 3
        mock_version.minor = 8

        toml = self.root / "pyproject.toml"
        toml.write_text("requires-python = '>=3.10'", encoding="utf-8")

        info = check_python_version(self.root)
        self.assertTrue(info["has_toml"])
        self.assertEqual(info["requires_python"], ">=3.10")
        self.assertFalse(info["meets_req"])

if __name__ == "__main__":
    unittest.main()
