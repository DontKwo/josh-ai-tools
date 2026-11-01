#!/usr/bin/env python3
"""Unit tests for scripts/secret_sanitizer.py."""
import io
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import secret_sanitizer
from scripts.secret_sanitizer import (
    IGNORED_DIRS,
    SECRET_PATTERNS,
    mask_secrets,
    scan_directory,
    scan_file,
)


class TestSecretSanitizerTokens(unittest.TestCase):
    """Test detection across various token pattern categories."""

    def test_detect_openai_api_key(self) -> None:
        token = "sk-abcdefghijklmnopqrstuvwxyz1234567890"
        content = f"OPENAI_KEY = '{token}'"
        pattern_dict = dict(SECRET_PATTERNS)
        pattern = pattern_dict["OpenAI API Key"]
        match = pattern.search(content)
        self.assertIsNotNone(match)
        if match is not None:
            self.assertEqual(match.group(0), token)

    def test_detect_anthropic_api_key(self) -> None:
        token = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz123456"
        content = f"export ANTHROPIC_API_KEY={token}"
        pattern_dict = dict(SECRET_PATTERNS)
        pattern = pattern_dict["Anthropic API Key"]
        match = pattern.search(content)
        self.assertIsNotNone(match)
        if match is not None:
            self.assertEqual(match.group(0), token)

    def test_detect_github_pat(self) -> None:
        token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        content = f"GITHUB_TOKEN={token}"
        pattern_dict = dict(SECRET_PATTERNS)
        pattern = pattern_dict["GitHub Personal Access Token"]
        match = pattern.search(content)
        self.assertIsNotNone(match)
        if match is not None:
            self.assertEqual(match.group(0), token)

    def test_detect_github_oauth_tokens(self) -> None:
        token_gho = "gho_1234567890abcdefghijklmnopqrstuvwxyz"
        token_ghu = "ghu_1234567890abcdefghijklmnopqrstuvwxyz"
        pattern_dict = dict(SECRET_PATTERNS)
        pattern = pattern_dict["GitHub OAuth / App Token"]
        match_gho = pattern.search(token_gho)
        match_ghu = pattern.search(token_ghu)
        self.assertIsNotNone(match_gho)
        self.assertIsNotNone(match_ghu)

    def test_detect_aws_access_key(self) -> None:
        token = "AKIA1234567890ABCDEF"
        content = f"aws_access_key_id = {token}"
        pattern_dict = dict(SECRET_PATTERNS)
        pattern = pattern_dict["AWS Access Key ID"]
        match = pattern.search(content)
        self.assertIsNotNone(match)
        if match is not None:
            self.assertEqual(match.group(0), token)

    def test_detect_slack_token(self) -> None:
        token = "xoxb-1234567890-abcdefghij"
        content = f"SLACK_BOT_TOKEN={token}"
        pattern_dict = dict(SECRET_PATTERNS)
        pattern = pattern_dict["Slack Token"]
        match = pattern.search(content)
        self.assertIsNotNone(match)
        if match is not None:
            self.assertEqual(match.group(0), token)

    def test_detect_private_key_headers(self) -> None:
        rsa_header = "-----BEGIN RSA PRIVATE KEY-----"
        generic_header = "-----BEGIN PRIVATE KEY-----"
        ec_header = "-----BEGIN EC PRIVATE KEY-----"
        pattern_dict = dict(SECRET_PATTERNS)
        pattern = pattern_dict["Private Key Header"]
        self.assertIsNotNone(pattern.search(rsa_header))
        self.assertIsNotNone(pattern.search(generic_header))
        self.assertIsNotNone(pattern.search(ec_header))

    def test_detect_database_url_with_password(self) -> None:
        db_url = "postgresql://dbuser:supersecretpass@localhost:5432/production"
        content = f"DATABASE_URL={db_url}"
        pattern_dict = dict(SECRET_PATTERNS)
        pattern = pattern_dict["Database URL with Password"]
        match = pattern.search(content)
        self.assertIsNotNone(match)
        if match is not None:
            self.assertEqual(match.group(0), db_url)

    def test_detect_bearer_token(self) -> None:
        header = "Authorization: Bearer abcdef1234567890ghijklmnop"
        pattern_dict = dict(SECRET_PATTERNS)
        pattern = pattern_dict["Generic Bearer Token"]
        match = pattern.search(header)
        self.assertIsNotNone(match)


class TestSecretMasking(unittest.TestCase):
    """Test masking behavior for long and short tokens."""

    def test_mask_secrets_long_token_retention(self) -> None:
        token = "sk-12345678901234567890abcdef"
        raw_text = f"api_key = '{token}'"
        masked = mask_secrets(raw_text)
        expected_token = f"{token[:4]}...{token[-4:]}[OpenAI API Key]"
        self.assertIn(expected_token, masked)
        self.assertNotIn(token, masked)

    def test_mask_secrets_short_token_redaction(self) -> None:
        short_pattern = ("Short PIN", re.compile(r"\bpin_\d{3}\b"))
        with patch.object(secret_sanitizer, "SECRET_PATTERNS", [short_pattern]):
            text = "user secret is pin_482"
            masked = mask_secrets(text)
            self.assertIn("[REDACTED]", masked)
            self.assertNotIn("pin_482", masked)

    def test_mask_secrets_clean_text(self) -> None:
        clean_text = "def hello_world() -> None:\n    return None"
        self.assertEqual(mask_secrets(clean_text), clean_text)


class TestSecretScanning(unittest.TestCase):
    """Test file and directory scanning functionality."""

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scan_file_with_secrets(self) -> None:
        file_path = self.temp_dir / "secrets.env"
        token = "AKIA1234567890ABCDEF"
        file_path.write_text(f"# config\nAWS_KEY={token}\n", encoding="utf-8")
        findings = scan_file(file_path)
        self.assertEqual(len(findings), 1)
        lineno, name, snippet = findings[0]
        self.assertEqual(lineno, 2)
        self.assertEqual(name, "AWS Access Key ID")
        self.assertIn(token, snippet)

    def test_scan_file_clean(self) -> None:
        file_path = self.temp_dir / "clean.py"
        file_path.write_text("print('hello world')\n", encoding="utf-8")
        findings = scan_file(file_path)
        self.assertEqual(findings, [])

    def test_scan_file_nonexistent(self) -> None:
        file_path = self.temp_dir / "missing.txt"
        findings = scan_file(file_path)
        self.assertEqual(findings, [])

    def test_scan_directory_single_file(self) -> None:
        file_path = self.temp_dir / "target.py"
        file_path.write_text("token = 'AKIA1234567890ABCDEF'\n", encoding="utf-8")
        results = scan_directory(file_path)
        self.assertIn(file_path, results)
        self.assertEqual(len(results[file_path]), 1)

    def test_scan_directory_ignored_dirs(self) -> None:
        for ignored_name in [".git", ".venv", "node_modules", "dist", "build"]:
            ignored_folder = self.temp_dir / ignored_name
            ignored_folder.mkdir(parents=True, exist_ok=True)
            leak_file = ignored_folder / "leak.txt"
            leak_file.write_text("token = 'AKIA1234567890ABCDEF'\n", encoding="utf-8")

        valid_folder = self.temp_dir / "src"
        valid_folder.mkdir(parents=True, exist_ok=True)
        valid_leak = valid_folder / "app.py"
        valid_leak.write_text("token = 'AKIA1234567890ABCDEF'\n", encoding="utf-8")

        results = scan_directory(self.temp_dir)
        self.assertIn(valid_leak, results)
        scanned_paths = list(results.keys())
        for path in scanned_paths:
            for ignored_name in IGNORED_DIRS:
                self.assertNotIn(ignored_name, path.parts)


class TestSecretSanitizerCLI(unittest.TestCase):
    """Test command-line interface execution paths."""

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_stdin_masking(self) -> None:
        token = "AKIA1234567890ABCDEF"
        stdin_stream = io.StringIO(f"Key is {token}")
        stdout_stream = io.StringIO()

        with patch("sys.stdin", stdin_stream), patch("sys.stdout", stdout_stream):
            with patch("sys.argv", ["secret_sanitizer.py", "--stdin"]):
                with self.assertRaises(SystemExit) as exit_context:
                    secret_sanitizer.main()
                self.assertEqual(exit_context.exception.code, 0)

        output = stdout_stream.getvalue()
        self.assertIn("AKIA...CDEF[AWS Access Key ID]", output)
        self.assertNotIn(token, output)

    def test_cli_file_masking(self) -> None:
        token = "AKIA1234567890ABCDEF"
        file_path = self.temp_dir / "config.py"
        file_path.write_text(f"KEY = '{token}'\n", encoding="utf-8")
        stdout_stream = io.StringIO()

        with patch("sys.stdout", stdout_stream):
            with patch("sys.argv", ["secret_sanitizer.py", str(file_path), "--mask"]):
                with self.assertRaises(SystemExit) as exit_context:
                    secret_sanitizer.main()
                self.assertEqual(exit_context.exception.code, 0)

        output = stdout_stream.getvalue()
        self.assertIn("AKIA...CDEF[AWS Access Key ID]", output)

    def test_cli_nonexistent_target(self) -> None:
        missing_path = self.temp_dir / "does_not_exist.txt"
        stderr_stream = io.StringIO()

        with patch("sys.stderr", stderr_stream):
            with patch("sys.argv", ["secret_sanitizer.py", str(missing_path)]):
                with self.assertRaises(SystemExit) as exit_context:
                    secret_sanitizer.main()
                self.assertEqual(exit_context.exception.code, 1)

    def test_cli_clean_directory(self) -> None:
        clean_file = self.temp_dir / "clean.txt"
        clean_file.write_text("just normal text\n", encoding="utf-8")
        stdout_stream = io.StringIO()

        with patch("sys.stdout", stdout_stream):
            with patch("sys.argv", ["secret_sanitizer.py", str(self.temp_dir)]):
                with self.assertRaises(SystemExit) as exit_context:
                    secret_sanitizer.main()
                self.assertEqual(exit_context.exception.code, 0)

        output = stdout_stream.getvalue()
        self.assertIn("[OK] Clean.", output)

    def test_cli_leaks_detected(self) -> None:
        leak_file = self.temp_dir / "leak.txt"
        leak_file.write_text("KEY = 'AKIA1234567890ABCDEF'\n", encoding="utf-8")
        stdout_stream = io.StringIO()

        with patch("sys.stdout", stdout_stream):
            with patch("sys.argv", ["secret_sanitizer.py", str(self.temp_dir)]):
                with self.assertRaises(SystemExit) as exit_context:
                    secret_sanitizer.main()
                self.assertEqual(exit_context.exception.code, 1)

        output = stdout_stream.getvalue()
        self.assertIn("SECURITY WARNING", output)


if __name__ == "__main__":
    unittest.main()
