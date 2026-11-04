import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure we can import from mcp
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server import (
    TOOLS,
    handle_tool_call,
    main,
    resolve_cwd,
    run_command_tool,
)


class TestMCPServer(unittest.TestCase):

    def test_run_command_tool_success(self) -> None:
        """Test successful command execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="success", stderr="")
            res = run_command_tool(["echo", "test"])
            self.assertEqual(res, "success")

    def test_run_command_tool_exception(self) -> None:
        """Test command execution error handling."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("boom")
            res = run_command_tool(["echo", "test"])
            self.assertEqual(res, "Error executing tool: boom")

    def test_resolve_cwd_with_cwd(self) -> None:
        """Test resolving explicit cwd."""
        args = {"cwd": "."}
        res = resolve_cwd(args)
        self.assertIsNotNone(res)
        if res is not None:
            self.assertEqual(res, Path(".").resolve())

    def test_resolve_cwd_with_target(self) -> None:
        """Test resolving target fallback."""
        args = {"target": "."}
        res = resolve_cwd(args)
        self.assertIsNotNone(res)
        if res is not None:
            self.assertEqual(res, Path(".").resolve())

    def test_handle_tool_call_invalid(self) -> None:
        """Test invalid tool name."""
        res = handle_tool_call("bad_tool", {})
        self.assertEqual(len(res), 1)
        self.assertIn("Unknown tool", res[0].get("text", ""))

    @patch("mcp.server.run_command_tool")
    def test_handle_tool_call_valid(self, mock_run: MagicMock) -> None:
        """Test valid tool dispatch."""
        mock_run.return_value = "lint ok"
        res = handle_tool_call("run_linter", {"target": "."})
        self.assertEqual(len(res), 1)
        self.assertIn("lint ok", res[0].get("text", ""))

    def test_tools_list_count(self) -> None:
        """Verify all 23 tools are defined."""
        self.assertEqual(len(TOOLS), 24)
        for t in TOOLS:
            self.assertIn("name", t)
            self.assertIn("description", t)
            self.assertIn("inputSchema", t)

    def _simulate_request(self, payload: dict) -> str:
        """Helper to simulate JSON-RPC request and capture stdout."""
        body = json.dumps(payload)
        length = len(body.encode("utf-8"))
        inputs = [
            f"Content-Length: {length}\r\n",
            "\r\n",
        ]

        def fake_readline() -> str:
            return inputs.pop(0) if inputs else ""

        def fake_read(n: int) -> str:
            return body

        captured_stdout: list[str] = []
        def fake_write(data: str) -> None:
            captured_stdout.append(data)

        def fake_flush() -> None:
            """Fake flush for mock."""
            return None

        with patch("sys.stdin.readline", side_effect=fake_readline), \
             patch("sys.stdin.read", side_effect=fake_read), \
             patch("sys.stdout.write", side_effect=fake_write), \
             patch("sys.stdout.flush", side_effect=fake_flush):
            # We catch exceptions for tests that intentionally throw them like invalid JSON with content length
            try:
                main()
            except Exception:
                captured_stdout.append("Exception caught")

        return "".join(captured_stdout)

    def test_main_initialize(self) -> None:
        """Test initialize protocol message."""
        payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
        out = self._simulate_request(payload)
        self.assertIn("protocolVersion", out)
        self.assertIn("josh-ai-tools-mcp", out)

    def test_main_ping_method_not_found(self) -> None:
        """Test missing method returns error."""
        payload = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
        out = self._simulate_request(payload)
        self.assertIn("-32601", out)
        self.assertIn("Method not found", out)

    def test_main_tools_list(self) -> None:
        """Test tools/list method."""
        payload = {"jsonrpc": "2.0", "id": 3, "method": "tools/list"}
        out = self._simulate_request(payload)
        self.assertIn("run_linter", out)

    @patch("mcp.server.handle_tool_call")
    def test_main_tools_call(self, mock_handle: MagicMock) -> None:
        """Test tools/call method."""
        mock_handle.return_value = [{"type": "text", "text": "ok"}]
        payload = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "run_linter", "arguments": {}}
        }
        out = self._simulate_request(payload)
        self.assertIn("ok", out)
        mock_handle.assert_called_once()

    def test_main_internal_execution_error(self) -> None:
        """Test handling of internal execution error (e.g. unknown tool)."""
        payload = {
            "jsonrpc": "2.0",
            "id": 42,
            "method": "tools/call",
            "params": {"name": "does_not_exist", "arguments": {}}
        }
        out = self._simulate_request(payload)
        self.assertIn("Error: Unknown tool", out)
        self.assertIn("does_not_exist", out)

    def test_invalid_json_silent_continue(self) -> None:
        """Test handling of invalid JSON input silently ignores it."""
        inputs = ["invalid json string\n"]

        def fake_readline() -> str:
            return inputs.pop(0) if inputs else ""

        with patch("sys.stdin.readline", side_effect=fake_readline), \
             patch("sys.stdout.write") as mock_write:
            main()
            mock_write.assert_not_called()

    def test_invalid_json_with_content_length(self) -> None:
        """Test JSON decoding exception ignores gracefully."""
        inputs = ["Content-Length: 10\r\n", "\r\n"]

        def fake_readline() -> str:
            return inputs.pop(0) if inputs else ""

        def fake_read(n: int) -> str:
            return "bad json {"

        with patch("sys.stdin.readline", side_effect=fake_readline), \
             patch("sys.stdin.read", side_effect=fake_read):
            # The JSON decode error crashes the loop gracefully, ending execution without writing response
            with self.assertRaises(Exception):
                main()


if __name__ == "__main__":
    unittest.main()
