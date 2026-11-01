#!/usr/bin/env python3
"""Unit tests for scripts/check_dependencies.py."""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.check_dependencies import (
    FALLBACK_STDLIB,
    KNOWN_IMPORT_ALIASES,
    clean_package_name,
    extract_imports_from_file,
    find_local_modules,
    get_declared_dependencies,
    get_stdlib_modules,
    parse_pyproject_toml,
    parse_requirements_file,
    scan_dependencies,
)


class TestCheckDependencies(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fallback_stdlib_contains_expected_modules(self) -> None:
        expected = {"json", "sys", "pathlib", "ast", "os", "re"}
        self.assertTrue(expected.issubset(FALLBACK_STDLIB))

    def test_get_stdlib_modules_resolution(self) -> None:
        stdlib = get_stdlib_modules()
        for mod in ["json", "sys", "pathlib", "ast"]:
            self.assertIn(mod, stdlib)

    def test_known_import_aliases_mapping(self) -> None:
        self.assertEqual(KNOWN_IMPORT_ALIASES.get("yaml"), "pyyaml")
        self.assertEqual(KNOWN_IMPORT_ALIASES.get("pil"), "pillow")
        self.assertEqual(KNOWN_IMPORT_ALIASES.get("cv2"), "opencv-python")

    def test_clean_package_name(self) -> None:
        self.assertEqual(clean_package_name("PyYAML>=5.1"), "pyyaml")
        self.assertEqual(clean_package_name("requests[security] <= 2.28.0"), "requests")
        self.assertEqual(clean_package_name("importlib-metadata; python_version<'3.8'"), "importlib_metadata")

    def test_ast_import_extraction(self) -> None:
        code_file = self.temp_dir / "sample.py"
        code_file.write_text(
            "import os, sys\n"
            "import numpy as np\n"
            "from pathlib import Path\n"
            "from requests.auth import HTTPBasicAuth\n"
            "from . import local_helper\n",
            encoding="utf-8",
        )
        extracted = extract_imports_from_file(code_file)
        self.assertEqual(extracted, {"os", "sys", "numpy", "pathlib", "requests"})

    def test_ast_import_extraction_syntax_error(self) -> None:
        bad_file = self.temp_dir / "bad.py"
        bad_file.write_text("def invalid syntax (:\n", encoding="utf-8")
        extracted = extract_imports_from_file(bad_file)
        self.assertEqual(extracted, set())

    def test_parse_requirements_file(self) -> None:
        req_file = self.temp_dir / "requirements.txt"
        req_file.write_text(
            "# Comment line\n"
            "-r base.txt\n"
            "requests>=2.25.0\n"
            "PyYAML==6.0\n"
            "scikit-learn\n",
            encoding="utf-8",
        )
        parsed = parse_requirements_file(req_file)
        self.assertEqual(parsed, {"requests", "pyyaml", "scikit_learn"})

    def test_parse_requirements_file_missing(self) -> None:
        missing_file = self.temp_dir / "nonexistent.txt"
        self.assertEqual(parse_requirements_file(missing_file), set())

    def test_parse_pyproject_toml(self) -> None:
        toml_file = self.temp_dir / "pyproject.toml"
        toml_file.write_text(
            "[project]\n"
            "name = 'demo'\n"
            "[project.dependencies]\n"
            "'fastapi>=0.95.0',\n"
            "\"uvicorn==0.22.0\",\n"
            "[tool.poetry.dependencies]\n"
            "python = '^3.10'\n"
            "pydantic = '^2.0'\n",
            encoding="utf-8",
        )
        parsed = parse_pyproject_toml(toml_file)
        self.assertEqual(parsed, {"fastapi", "uvicorn", "pydantic"})

    def test_parse_pyproject_toml_missing(self) -> None:
        missing_file = self.temp_dir / "nonexistent.toml"
        self.assertEqual(parse_pyproject_toml(missing_file), set())

    def test_get_declared_dependencies(self) -> None:
        req_file = self.temp_dir / "requirements.txt"
        req_file.write_text("click>=8.0.0\n", encoding="utf-8")
        req_dev_file = self.temp_dir / "requirements-dev.txt"
        req_dev_file.write_text("pytest>=7.0.0\n", encoding="utf-8")

        req_dir = self.temp_dir / "requirements"
        req_dir.mkdir()
        (req_dir / "extra.txt").write_text("attrs\n", encoding="utf-8")

        toml_file = self.temp_dir / "pyproject.toml"
        toml_file.write_text("[project.dependencies]\n'tqdm>=4.0'\n", encoding="utf-8")

        declared = get_declared_dependencies(self.temp_dir)
        self.assertEqual(declared, {"click", "pytest", "attrs", "tqdm"})

    def test_find_local_modules(self) -> None:
        (self.temp_dir / "local_mod.py").write_text("x = 1\n", encoding="utf-8")
        pkg_dir = self.temp_dir / "local_pkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("", encoding="utf-8")

        found = find_local_modules(self.temp_dir)
        self.assertIn("local_mod", found)
        self.assertIn("local_pkg", found)

    @patch("scripts.check_dependencies.get_installed_distributions")
    def test_scan_dependencies_audit_reporting(self, mock_installed: unittest.mock.MagicMock) -> None:
        mock_installed.return_value = {
            "installed_pkg": "installed_pkg",
            "declared_and_installed": "declared_and_installed",
        }

        # Setup mock project files
        req_file = self.temp_dir / "requirements.txt"
        req_file.write_text("declared_and_installed\nunused_pkg\n", encoding="utf-8")

        code_file = self.temp_dir / "app.py"
        code_file.write_text(
            "import os\n"
            "import declared_and_installed\n"
            "import installed_pkg\n"
            "import fake_pkg\n",
            encoding="utf-8",
        )

        results = scan_dependencies(self.temp_dir, project_root=self.temp_dir)
        self.assertIn("fake_pkg", results["hallucinated"])
        self.assertIn("installed_pkg", results["undeclared"])
        self.assertIn("unused_pkg", results["unused_declared"])
        self.assertIn("declared_and_installed", results["third_party"])
        self.assertIn("installed_pkg", results["third_party"])
        self.assertIn("fake_pkg", results["third_party"])
        self.assertNotIn("os", results["third_party"])


if __name__ == "__main__":
    unittest.main()
