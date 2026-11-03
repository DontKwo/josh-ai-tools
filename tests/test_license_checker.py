import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict
from unittest.mock import patch, MagicMock

# Add scripts directory to path for import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from license_checker import (
    parse_requirements_txt,
    parse_package_json,
    parse_pyproject_toml,
    check_licenses,
    main,
)

class TestLicenseChecker(unittest.TestCase):

    def test_parse_requirements_txt(self) -> None:
        # Test parsing of requirements.txt
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()
            req_file = temp_path / "requirements.txt"
            req_file.write_text("requests==2.28.1\nflask>=2.0.0\n# comment\npytest", encoding="utf-8")

            packages = parse_requirements_txt(req_file)
            self.assertEqual(packages, ["requests", "flask", "pytest"])

    def test_parse_package_json(self) -> None:
        # Test parsing of package.json
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()
            pkg_file = temp_path / "package.json"
            pkg_data = {
                "dependencies": {"react": "^18.0.0"},
                "devDependencies": {"jest": "^27.0.0"}
            }
            pkg_file.write_text(json.dumps(pkg_data), encoding="utf-8")

            packages = parse_package_json(pkg_file)
            self.assertEqual(packages, ["react", "jest"])

    def test_parse_pyproject_toml(self) -> None:
        # Test parsing of pyproject.toml
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()
            toml_file = temp_path / "pyproject.toml"
            toml_content = """
[project]
dependencies = ["numpy>=1.20.0", "pandas"]

[tool.poetry.dependencies]
python = "^3.8"
fastapi = "^0.68.0"
"""
            toml_file.write_text(toml_content, encoding="utf-8")

            packages = parse_pyproject_toml(toml_file)
            self.assertEqual(sorted(packages), ["fastapi", "numpy", "pandas"])

    @patch("license_checker.get_pypi_license")
    def test_check_licenses_pypi(self, mock_get_license: MagicMock) -> None:
        # Test license checking for PyPI packages
        def mock_license(pkg: str) -> str:
            licenses: Dict[str, str] = {"requests": "Apache-2.0", "flask": "BSD-3-Clause", "django": "GPL"}
            return licenses.get(pkg, "Unknown")
        mock_get_license.side_effect = mock_license

        approved, unapproved = check_licenses(["requests", "flask", "django"], "pypi")
        self.assertEqual(len(approved), 2)
        self.assertEqual(len(unapproved), 1)
        self.assertTrue(any("django" in u for u in unapproved))

    @patch("license_checker.get_npm_license")
    def test_check_licenses_npm(self, mock_get_license: MagicMock) -> None:
        # Test license checking for NPM packages
        def mock_license(pkg: str) -> str:
            licenses: Dict[str, str] = {"react": "MIT", "vue": "MIT", "left-pad": "WTFPL"}
            return licenses.get(pkg, "Unknown")
        mock_get_license.side_effect = mock_license

        approved, unapproved = check_licenses(["react", "vue", "left-pad"], "npm")
        self.assertEqual(len(approved), 2)
        self.assertEqual(len(unapproved), 1)
        self.assertTrue(any("left-pad" in u for u in unapproved))

    @patch("license_checker.check_licenses")
    def test_main_success(self, mock_check: MagicMock) -> None:
        # Test main execution with all approved licenses
        mock_check.return_value = (["requests (MIT)"], [])

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()
            req_file = temp_path / "requirements.txt"
            req_file.write_text("requests", encoding="utf-8")

            exit_code = main(str(temp_path))
            self.assertEqual(exit_code, 0)

    @patch("license_checker.check_licenses")
    def test_main_failure(self, mock_check: MagicMock) -> None:
        # Test main execution with unapproved licenses
        mock_check.return_value = ([], ["django (GPL)"])

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()
            req_file = temp_path / "requirements.txt"
            req_file.write_text("django", encoding="utf-8")

            exit_code = main(str(temp_path))
            self.assertEqual(exit_code, 1)

if __name__ == '__main__':
    unittest.main()
