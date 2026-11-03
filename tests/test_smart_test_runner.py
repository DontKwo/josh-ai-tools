#!/usr/bin/env python3
"""Unit tests for scripts/smart_test_runner.py."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.smart_test_runner import (
    extract_symbols_from_file,
    find_matching_tests,
    find_venv_python,
    find_impacted_tests,
)


class TestSmartTestRunner(unittest.TestCase):
    def setUp(self) -> None:
        self.raw_temp_dir = tempfile.mkdtemp()
        self.workspace_dir = Path(self.raw_temp_dir).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.workspace_dir, ignore_errors=True)

    def test_extract_symbols_from_file_success(self) -> None:
        sample_code = (
            "class SampleService:\n"
            "    def execute_task(self) -> None:\n"
            "        pass\n"
            "\n"
            "async def async_fetch_data() -> None:\n"
            "    pass\n"
        )
        source_path = self.workspace_dir / "service.py"
        source_path.write_text(sample_code, encoding="utf-8")

        extracted_symbols = extract_symbols_from_file(source_path)
        expected_symbols = {"SampleService", "execute_task", "async_fetch_data"}
        self.assertEqual(extracted_symbols, expected_symbols)

    def test_extract_symbols_from_file_syntax_error(self) -> None:
        invalid_code = "def invalid_syntax_func(:\n"
        source_path = self.workspace_dir / "broken.py"
        source_path.write_text(invalid_code, encoding="utf-8")

        extracted_symbols = extract_symbols_from_file(source_path)
        self.assertEqual(extracted_symbols, set())

    def test_find_matching_tests_direct_test_file(self) -> None:
        tests_dir = self.workspace_dir / "tests"
        tests_dir.mkdir(parents=True)
        modified_test = tests_dir / "test_example.py"
        modified_test.write_text("def test_simple() -> None:\n    pass\n", encoding="utf-8")

        matched = find_matching_tests(self.workspace_dir, [modified_test])
        self.assertEqual(matched, [modified_test])

    def test_find_matching_tests_naming_convention(self) -> None:
        tests_dir = self.workspace_dir / "tests"
        tests_dir.mkdir(parents=True)
        feature_test = tests_dir / "test_calculator.py"
        feature_test.write_text("# Test calculator file\n", encoding="utf-8")

        source_file = self.workspace_dir / "calculator.py"
        source_file.write_text("def calculate_total() -> int:\n    return 42\n", encoding="utf-8")

        matched = find_matching_tests(self.workspace_dir, [source_file])
        self.assertEqual(matched, [feature_test])

    def test_find_matching_tests_import_and_symbol_references(self) -> None:
        tests_dir = self.workspace_dir / "tests"
        tests_dir.mkdir(parents=True)

        symbol_test = tests_dir / "test_symbols_suite.py"
        symbol_test.write_text("from somewhere import compute_payload\n", encoding="utf-8")

        other_test = tests_dir / "test_unrelated.py"
        other_test.write_text("def test_other() -> None:\n    pass\n", encoding="utf-8")

        source_file = self.workspace_dir / "generator.py"
        source_file.write_text("def compute_payload() -> None:\n    pass\n", encoding="utf-8")

        matched = find_matching_tests(self.workspace_dir, [source_file])
        self.assertIn(symbol_test, matched)
        self.assertNotIn(other_test, matched)

    def test_find_venv_python_unix(self) -> None:
        virtual_bin = self.workspace_dir / ".venv" / "bin"
        virtual_bin.mkdir(parents=True)
        python_executable = virtual_bin / "python"
        python_executable.touch()

        with patch("platform.system", return_value="Linux"), patch.dict(os.environ, {}, clear=True):
            resolved_interpreter = find_venv_python(self.workspace_dir)
            self.assertEqual(resolved_interpreter, python_executable)

    def test_find_venv_python_windows(self) -> None:
        virtual_scripts = self.workspace_dir / ".venv" / "Scripts"
        virtual_scripts.mkdir(parents=True)
        python_executable = virtual_scripts / "python.exe"
        python_executable.touch()

        with patch("platform.system", return_value="Windows"), patch.dict(os.environ, {}, clear=True):
            resolved_interpreter = find_venv_python(self.workspace_dir)
            self.assertEqual(resolved_interpreter, python_executable)



    @patch("scripts.smart_test_runner.Path.cwd")
    def test_find_impacted_tests(self, mock_cwd: unittest.mock.MagicMock) -> None:
        mock_cwd.return_value = self.workspace_dir
        tests_dir = self.workspace_dir / "tests"
        tests_dir.mkdir(parents=True)
        feature_test = tests_dir / "test_doctor.py"
        feature_test.write_text("def test_doc() -> None:\n    pass\n", encoding="utf-8")
        source_file = self.workspace_dir / "scripts" / "doctor.py"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("def doc_func() -> None:\n    pass\n", encoding="utf-8")

        # Test finding impacted test using relative path
        impacted = find_impacted_tests(["scripts/doctor.py"])
        self.assertEqual(len(impacted), 1)
        self.assertTrue(impacted[0].endswith("test_doctor.py"))



if __name__ == "__main__":
    unittest.main()
