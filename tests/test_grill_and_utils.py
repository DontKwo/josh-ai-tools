"""Tests for grill_user.py and utils.py."""
from __future__ import annotations

import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Dynamically append scripts directory to sys.path for module resolution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import grill_user
import utils


class TestUtils(unittest.TestCase):
    @patch.dict(os.environ, {"USERPROFILE": "C:\\Users\\Test", "HOME": "/home/test"})
    @patch("utils.IS_WINDOWS", True)
    def test_get_user_home_windows(self) -> None:
        expected_path = Path("C:\\Users\\Test")
        self.assertEqual(utils.get_user_home(), expected_path)

    @patch.dict(os.environ, {"USERPROFILE": "C:\\Users\\Test", "HOME": "/home/test"})
    @patch("utils.IS_WINDOWS", False)
    def test_get_user_home_unix(self) -> None:
        expected_path = Path("/home/test")
        self.assertEqual(utils.get_user_home(), expected_path)

    def test_format_command_path_with_spaces(self) -> None:
        path = Path("/path with/spaces")
        expected_str = f'"{str(path)}"'
        self.assertEqual(utils.format_command_path(path), expected_str)

    def test_format_command_path_without_spaces(self) -> None:
        path = Path("/path/without/spaces")
        expected_str = str(path)
        self.assertEqual(utils.format_command_path(path), expected_str)


class TestGrillUser(unittest.TestCase):
    @patch("sys.argv", ["grill_user.py", "test_topic"])
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_main_custom_topic(self, mock_stdout: io.StringIO) -> None:
        exit_code = grill_user.main()
        output = mock_stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Triggering 'Grilling' skill for topic: test_topic", output)
        self.assertIn("decision", output)
        self.assertIn("Instructions", output)

    @patch("sys.argv", ["grill_user.py"])
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_main_default_topic(self, mock_stdout: io.StringIO) -> None:
        exit_code = grill_user.main()
        output = mock_stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Triggering 'Grilling' skill for topic: ", output)
        self.assertIn("decision", output)
        self.assertIn("Instructions", output)


if __name__ == "__main__":
    unittest.main()
