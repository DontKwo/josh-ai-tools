import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from configure import (
    build_instructions,
    configure_mcp_servers,
    configure_skills,
    get_tool_definitions,
)


class TestConfigure(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()
        self.mock_home = self.temp_dir / "home"
        self.mock_ws = self.temp_dir / "workspace"
        self.mock_repo = self.temp_dir / "repo"
        self.mock_home.mkdir(parents=True)
        self.mock_ws.mkdir(parents=True)
        self.mock_repo.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_tool_definitions(self) -> None:
        # get_user_home is already patched in setUp, but need to patch it for the actual configure module scope
        with patch("configure.get_user_home", return_value=self.mock_home):
            defs = get_tool_definitions(self.mock_ws)
        expected_tools = ["claude", "cursor", "cline", "antigravity", "codex", "windsurf", "copilot", "aider"]
        for tool in expected_tools:
            self.assertIn(tool, defs)

        cursor_def = defs["cursor"]
        self.assertIn("alwaysApply: true", cursor_def["frontmatter"])
        self.assertIn("globs: *", cursor_def["frontmatter"])

        claude_def = defs["claude"]
        self.assertEqual(claude_def["frontmatter"], "")

        # Verify workspace paths use the provided workspace
        self.assertTrue(any(str(self.mock_ws) in str(p) for p in cursor_def["workspace_paths"]))
        # Verify global paths use the home dir
        self.assertTrue(any(str(self.mock_home) in str(p) for p in cursor_def["global_paths"]))

    @patch("configure.calc_linter_command", return_value="uv run python linter.py")
    def test_build_instructions(self, mock_calc: MagicMock) -> None:
        mock_template = MagicMock()
        mock_template.read_text.return_value = "Linter: {{LINTER_COMMAND}}\nEng Rules: {{ENGINEERING_RULES_PATH}}\nPy Rules: {{PYTHON_RULES_PATH}}\n"

        with patch("configure.TEMPLATE_PATH", mock_template):
            with patch("configure.format_command_path", side_effect=lambda x: str(x).replace("/workspace/", "rel/") if "workspace" in str(x) else str(x)):
                content = build_instructions()
        self.assertIn("Linter: uv run python linter.py", content)
        self.assertNotIn("{{LINTER_COMMAND}}", content)
        self.assertNotIn("{{ENGINEERING_RULES_PATH}}", content)
        self.assertNotIn("{{PYTHON_RULES_PATH}}", content)

        frontmatter = "---\nfrontmatter\n---\n"
        with patch("configure.TEMPLATE_PATH", mock_template):
            with patch("configure.format_command_path", side_effect=lambda x: str(x)):
                content_with_fm = build_instructions(frontmatter)
        self.assertTrue(content_with_fm.startswith(frontmatter))
        self.assertIn("Linter: uv run python linter.py", content_with_fm)

    def test_configure_mcp_servers(self) -> None:
        mcp_script = self.mock_repo / "mcp" / "server.py"
        mcp_script.parent.mkdir()
        mcp_script.touch()

        # Create existing MCP configs to ensure we don't clobber them
        cursor_mcp_path = self.mock_ws / ".cursor" / "mcp.json"
        cursor_mcp_path.parent.mkdir(parents=True)
        cursor_mcp_path.write_text(json.dumps({"mcpServers": {"other-server": {"command": "dummy"}}}), encoding="utf-8")

        windsurf_mcp_path = self.mock_home / ".codeium" / "windsurf" / "mcp_config.json"
        windsurf_mcp_path.parent.mkdir(parents=True)
        windsurf_mcp_path.write_text(json.dumps({"mcpServers": {"other": {"command": "dummy"}}}), encoding="utf-8")

        anti_mcp_path = self.mock_home / ".gemini" / "antigravity" / "mcp_config.json"
        anti_mcp_path.parent.mkdir(parents=True)
        anti_mcp_path.write_text(json.dumps({"mcpServers": {"other-gemini": {"command": "dummy"}}}), encoding="utf-8")

        import platform
        from scripts.utils import IS_WINDOWS
        if IS_WINDOWS:
            claude_mcp_path_desktop = self.mock_home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        elif platform.system() == "Darwin":
            claude_mcp_path_desktop = self.mock_home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        else:
            claude_mcp_path_desktop = self.mock_home / ".config" / "Claude" / "claude_desktop_config.json"

        claude_mcp_path_desktop.parent.mkdir(parents=True)
        claude_mcp_path_desktop.write_text(json.dumps({"mcpServers": {"other-claude": {"command": "dummy"}}}), encoding="utf-8")

        with patch("configure.get_user_home", return_value=self.mock_home):
            configure_mcp_servers(
                repo_root=self.mock_repo,
                scope="both",
                workspace=self.mock_ws,
                tools=["claude", "cursor", "windsurf", "antigravity"],
            )

        data = json.loads(cursor_mcp_path.read_text(encoding="utf-8"))
        self.assertIn("other-server", data["mcpServers"])
        self.assertIn("josh-ai-tools", data["mcpServers"])
        self.assertIn("command", data["mcpServers"]["josh-ai-tools"])
        self.assertIn("args", data["mcpServers"]["josh-ai-tools"])

        data_ws = json.loads(windsurf_mcp_path.read_text(encoding="utf-8"))
        self.assertIn("other", data_ws["mcpServers"])
        self.assertIn("josh-ai-tools", data_ws["mcpServers"])
        self.assertIn("command", data_ws["mcpServers"]["josh-ai-tools"])
        self.assertIn("args", data_ws["mcpServers"]["josh-ai-tools"])

        # Antigravity tests
        data_anti = json.loads(anti_mcp_path.read_text(encoding="utf-8"))
        self.assertIn("other-gemini", data_anti["mcpServers"])
        self.assertIn("josh-ai-tools", data_anti["mcpServers"])
        self.assertIn("command", data_anti["mcpServers"]["josh-ai-tools"])

        # Claude tests
        claude_mcp_path = self.mock_ws / ".claude.json"
        data_claude = json.loads(claude_mcp_path.read_text(encoding="utf-8"))
        self.assertIn("josh-ai-tools", data_claude["mcpServers"])
        self.assertIn("command", data_claude["mcpServers"]["josh-ai-tools"])

        data_claude_desktop = json.loads(claude_mcp_path_desktop.read_text(encoding="utf-8"))
        self.assertIn("other-claude", data_claude_desktop["mcpServers"])
        self.assertIn("josh-ai-tools", data_claude_desktop["mcpServers"])
        self.assertIn("command", data_claude_desktop["mcpServers"]["josh-ai-tools"])

        # Test remove functionality
        with patch("configure.get_user_home", return_value=self.mock_home):
            configure_mcp_servers(
                repo_root=self.mock_repo,
                scope="both",
                workspace=self.mock_ws,
                tools=["claude", "cursor", "windsurf", "antigravity"],
                remove=True,
            )

        data = json.loads(cursor_mcp_path.read_text(encoding="utf-8"))
        self.assertIn("other-server", data["mcpServers"])
        self.assertNotIn("josh-ai-tools", data["mcpServers"])

    def test_configure_skills(self) -> None:
        skills_dir = self.mock_repo / "skills"
        skills_dir.mkdir()
        skill_a = skills_dir / "skill_a"
        skill_a.mkdir()
        (skill_a / "SKILL.md").write_text("test")

        configure_skills(
            repo_root=self.mock_repo,
            scope="workspace",
            workspace=self.mock_ws,
        )

        target_dir = self.mock_ws / ".agent" / "skills" / "skill_a"
        self.assertTrue(target_dir.is_dir())
        self.assertTrue((target_dir / "SKILL.md").is_file())

        configure_skills(
            repo_root=self.mock_repo,
            scope="workspace",
            workspace=self.mock_ws,
            remove=True,
        )

        self.assertFalse(target_dir.exists())


if __name__ == "__main__":
    unittest.main()
