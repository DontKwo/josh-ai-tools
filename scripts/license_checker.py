import json
import re
import sys
import tomllib
from pathlib import Path
from typing import List, Tuple

APPROVED_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"}

def parse_requirements_txt(file_path: Path) -> List[str]:
    # Parses requirements.txt and extracts package names.
    packages: List[str] = []
    if not file_path.exists():
        return packages
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line or line.startswith("-"):
                continue
            match = re.match(r"^([a-zA-Z0-9_\-]+)", line)
            if match:
                packages.append(match.group(1))
    return packages

def parse_package_json(file_path: Path) -> List[str]:
    # Parses package.json and extracts package names.
    packages: List[str] = []
    if not file_path.exists():
        return packages
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "dependencies" in data:
        packages.extend(data["dependencies"].keys())
    if "devDependencies" in data:
        packages.extend(data["devDependencies"].keys())
    return packages

def parse_pyproject_toml(file_path: Path) -> List[str]:
    # Parses pyproject.toml and extracts package names.
    packages: List[str] = []
    if not file_path.exists():
        return packages
    with open(file_path, "rb") as f:
        data = tomllib.load(f)

    if "project" in data and "dependencies" in data["project"]:
        for dep in data["project"]["dependencies"]:
            match = re.match(r"^([a-zA-Z0-9_\-]+)", dep)
            if match:
                packages.append(match.group(1))

    if "tool" in data and "poetry" in data["tool"] and "dependencies" in data["tool"]["poetry"]:
        for dep in data["tool"]["poetry"]["dependencies"].keys():
            if dep != "python":
                packages.append(dep)

    return packages

def get_pypi_license(package: str) -> str:
    # Fetches license information from PyPI for a given package.
    url = f"https://pypi.org/pypi/{package}/json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return str(data.get("info", {}).get("license", "Unknown"))
    except Exception:
        return "Unknown"

def get_npm_license(package: str) -> str:
    # Fetches license information from NPM for a given package.
    url = f"https://registry.npmjs.org/{package}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            license_val = data.get("license", "Unknown")
            if isinstance(license_val, dict):
                return str(license_val.get("type", "Unknown"))
            return str(license_val)
    except Exception:
        return "Unknown"

def check_licenses(packages: List[str], registry: str) -> Tuple[List[str], List[str]]:
    # Checks licenses for a list of packages and reports unapproved ones.
    unapproved: List[str] = []
    approved: List[str] = []
    for pkg in set(packages):
        if registry == "pypi":
            lic = get_pypi_license(pkg)
        else:
            lic = get_npm_license(pkg)

        # Simplistic check if approved license is in the returned license string
        is_approved = any(app_lic.lower() in lic.lower() for app_lic in APPROVED_LICENSES)
        if is_approved:
            approved.append(f"{pkg} ({lic})")
        else:
            unapproved.append(f"{pkg} ({lic})")

    return approved, unapproved

def main(directory_path: str) -> int:
    # Main entrypoint to check licenses in a directory.
    target_dir = Path(directory_path)
    all_unapproved: List[str] = []

    pypi_pkgs = parse_requirements_txt(target_dir / "requirements.txt")
    pypi_pkgs.extend(parse_pyproject_toml(target_dir / "pyproject.toml"))
    if pypi_pkgs:
        _, unapproved = check_licenses(pypi_pkgs, "pypi")
        all_unapproved.extend(unapproved)

    npm_pkgs = parse_package_json(target_dir / "package.json")
    if npm_pkgs:
        _, unapproved = check_licenses(npm_pkgs, "npm")
        all_unapproved.extend(unapproved)

    if all_unapproved:
        print("Unapproved licenses found:")
        for issue in all_unapproved:
            print(f" - {issue}")
        return 1

    print("All licenses approved.")
    return 0

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    target_path = sys.argv[1] if len(sys.argv) > 1 else "."
    exit_code = main(target_path)
    sys.exit(exit_code)
