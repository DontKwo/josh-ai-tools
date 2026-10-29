#!/usr/bin/env python3
"""Unit tests for newly added tools in josh-ai-tools."""
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.install_antigravity_hooks import build_hook_config, install_hook, remove_hook
from scripts.pack_context import pack_files
from scripts.secret_sanitizer import mask_secrets, scan_file
from scripts.smart_test_runner import extract_symbols_from_file
from scripts.sync_rules import format_for_target, strip_frontmatter
from scripts.token_budget import estimate_tokens


class TestNewTools(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sync_rules_formatting(self) -> None:
        raw_md = "---\ndescription: test\n---\n# Rule\nBe terse.\n"
        stripped = strip_frontmatter(raw_md)
        self.assertEqual(stripped, "# Rule\nBe terse.\n")

        cursor_target = Path("test.mdc")
        formatted = format_for_target(cursor_target, stripped)
        self.assertTrue(formatted.startswith("---"))
        self.assertIn("alwaysApply: true", formatted)

    def test_smart_test_runner_ast_symbol_extraction(self) -> None:
        py_file = self.temp_dir / "sample.py"
        py_file.write_text("def my_func(): pass\nclass MyClass: pass\n", encoding="utf-8")
        symbols = extract_symbols_from_file(py_file)
        self.assertIn("my_func", symbols)
        self.assertIn("MyClass", symbols)

    def test_token_budget_estimation(self) -> None:
        text = "def hello_world():\n    return 'Hello, world!'\n"
        metrics = estimate_tokens(text)
        self.assertGreater(metrics["tokens"], 0)
        self.assertEqual(metrics["lines"], 2)

    def test_pack_context_files(self) -> None:
        doc = self.temp_dir / "sample.txt"
        doc.write_text("Hello payload", encoding="utf-8")
        blocks = pack_files([doc], self.temp_dir)
        self.assertEqual(len(blocks), 1)
        self.assertIn("Hello payload", blocks[0])

    def test_secret_sanitizer_masking(self) -> None:
        leak = "OpenAI key: sk-abcdefghijklmnopqrstuvwxyz123456"
        masked = mask_secrets(leak)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz123456", masked)
        self.assertIn("[OpenAI API Key]", masked)

        clean_file = self.temp_dir / "clean.py"
        clean_file.write_text("API_URL = 'https://api.example.com'\n", encoding="utf-8")
        self.assertEqual(len(scan_file(clean_file)), 0)

    def test_antigravity_completion_hook(self) -> None:
        hook_path = self.temp_dir / ".agent" / "hooks.json"
        config = build_hook_config("python lint.py", "PostInvocation")
        self.assertIn("PostInvocation", config["josh-linter-completion-guard"])

        installed = install_hook(hook_path, "python lint.py", "PostInvocation")
        self.assertTrue(installed)
        self.assertTrue(hook_path.is_file())

        removed = remove_hook(hook_path)
        self.assertTrue(removed)

    def test_variable_name_auditor(self) -> None:
        from scripts.check_variable_names import audit_file
        bad_file = self.temp_dir / "bad_vars.py"
        bad_file.write_text("def test_func(arg):\n    temp = 42\n    return temp\n", encoding="utf-8")
        violations = audit_file(bad_file)
        names = [name for _, name, _ in violations]
        self.assertIn("arg", names)
        self.assertIn("temp", names)

    def test_spell_checker(self) -> None:
        from scripts.spell_checker import check_line_spelling
        hits = check_line_spelling("We must recieve the seperate files.")  # noqa: 39
        wrong_words = [w.lower() for w, _ in hits]
        self.assertIn("recieve", wrong_words)  # noqa: 39
        self.assertIn("seperate", wrong_words)  # noqa: 39

    def test_find_venv_python(self) -> None:
        import platform
        from scripts.smart_test_runner import find_venv_python
        is_win = platform.system() == "Windows"
        rel_dir = "Scripts" if is_win else "bin"
        exe_name = "python.exe" if is_win else "python"

        venv_dir = self.temp_dir / ".venv" / rel_dir
        venv_dir.mkdir(parents=True, exist_ok=True)
        fake_py = venv_dir / exe_name
        fake_py.write_text("", encoding="utf-8")

        sub_dir = self.temp_dir / "sub" / "deep"
        sub_dir.mkdir(parents=True, exist_ok=True)
        found = find_venv_python(sub_dir)
        self.assertIsNotNone(found)
        if found:
            self.assertEqual(found.resolve(), fake_py.resolve())


if __name__ == "__main__":
    unittest.main()

