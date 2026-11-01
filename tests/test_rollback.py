#!/usr/bin/env python3
"""Unit tests for scripts/rollback.py."""

import json
import os
import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts.rollback import (
    clear_checkpoints,
    diff_checkpoint,
    get_checkpoint_dir,
    list_checkpoints,
    restore_checkpoint,
    save_checkpoint,
)


class TestRollback(unittest.TestCase):
    def setUp(self) -> None:
        self.raw_temp_dir = tempfile.mkdtemp()
        self.ws = Path(self.raw_temp_dir).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.ws, ignore_errors=True)

    def test_save_checkpoint(self) -> None:
        app_file = self.ws / "app.py"
        app_file.write_text("hello", encoding="utf-8")

        ignore_dirs = [".git", ".venv", "__pycache__", "node_modules", "dist", "build"]
        for ignore_dir_name in ignore_dirs:
            ign_dir = self.ws / ignore_dir_name
            ign_dir.mkdir()
            (ign_dir / "skip.txt").write_text("skip", encoding="utf-8")

        saved_name = save_checkpoint(self.ws, "snap")
        self.assertEqual(saved_name, "snap")

        cp_file = get_checkpoint_dir(self.ws) / "snap.json"
        self.assertTrue(cp_file.exists())
        checkpoint_data = json.loads(cp_file.read_text(encoding="utf-8"))

        self.assertEqual(checkpoint_data["total_files"], 1)
        self.assertIn("app.py", checkpoint_data["files"])
        self.assertEqual(checkpoint_data["files"]["app.py"], "hello")
        self.assertEqual(checkpoint_data["name"], "snap")
        self.assertIn("timestamp", checkpoint_data)

    def test_list_checkpoints(self) -> None:
        cp_dir = get_checkpoint_dir(self.ws)
        cp_dir.mkdir(parents=True)

        first_checkpoint = cp_dir / "first.json"
        first_checkpoint.write_text('{"name": "first"}', encoding="utf-8")

        second_checkpoint = cp_dir / "second.json"
        second_checkpoint.write_text('{"name": "second"}', encoding="utf-8")

        bad_checkpoint = cp_dir / "bad.json"
        bad_checkpoint.write_text("{bad}", encoding="utf-8")

        os.utime(first_checkpoint, (100, 100))
        os.utime(second_checkpoint, (200, 200))

        checkpoints = list_checkpoints(self.ws)
        self.assertEqual(len(checkpoints), 2)
        self.assertEqual(checkpoints[0]["name"], "second")
        self.assertEqual(checkpoints[1]["name"], "first")

    def test_restore_checkpoint(self) -> None:
        app_file = self.ws / "app.py"
        app_file.write_text("orig", encoding="utf-8")
        save_checkpoint(self.ws, "snap")

        app_file.unlink()

        restore_success = restore_checkpoint(self.ws, "snap")
        self.assertTrue(restore_success)
        self.assertEqual(app_file.read_text(encoding="utf-8"), "orig")

    def test_diff_checkpoint_and_clear(self) -> None:
        app_file = self.ws / "app.py"
        app_file.write_text("orig", encoding="utf-8")
        deleted_file = self.ws / "del.py"
        deleted_file.write_text("del", encoding="utf-8")
        save_checkpoint(self.ws, "snap")

        app_file.write_text("mut", encoding="utf-8")
        deleted_file.unlink()
        (self.ws / "new.py").write_text("new", encoding="utf-8")

        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            diff_checkpoint(self.ws, "snap")
            diff_output = mock_out.getvalue()

        self.assertIn("Modified", diff_output)
        self.assertIn("Added", diff_output)
        self.assertIn("Deleted", diff_output)

        clear_checkpoints(self.ws)
        self.assertFalse(get_checkpoint_dir(self.ws).exists())


if __name__ == "__main__":
    unittest.main()
