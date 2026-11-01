import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.doctor import check_installed_skills, inspect_mcp_config


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

if __name__ == "__main__":
    unittest.main()
