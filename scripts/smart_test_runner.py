#!/usr/bin/env python3
"""AST-aware test impact runner that executes tests for modified code."""

import argparse
import ast
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_git_modified_files(ws: Path) -> list[Path]:
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(ws),
            capture_output=True,
            text=True,
            check=False,
        )
        files: list[Path] = []
        for line in res.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                path = ws / parts[1].strip()
                if path.suffix == ".py" and path.is_file():
                    files.append(path)
        return files
    except Exception:
        return []


def extract_symbols_from_file(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        symbols: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbols.add(node.name)
        return symbols
    except Exception:
        return set()


def find_matching_tests(ws: Path, modified_files: list[Path]) -> list[Path]:
    test_dir = ws / "tests"
    if not test_dir.is_dir():
        test_dir = ws
    test_files = [p for p in test_dir.rglob("*.py") if p.is_file() and (p.name.startswith("test_") or p.name.endswith("_test.py"))]

    # If any modified file is a test file directly, include it
    matched_tests: set[Path] = set()
    for mf in modified_files:
        if mf.name.startswith("test_") or mf.name.endswith("_test.py"):
            matched_tests.add(mf)

    # For other modified files, check test files for imports or references
    for mf in modified_files:
        if mf in matched_tests:
            continue
        stem = mf.stem
        symbols = extract_symbols_from_file(mf)
        for tf in test_files:
            try:
                content = tf.read_text(encoding="utf-8", errors="replace")
                if stem in content:
                    matched_tests.add(tf)
                    continue
                if any(sym in content for sym in symbols):
                    matched_tests.add(tf)
            except Exception:
                continue

    return sorted(matched_tests)


def find_venv_python(start_dir: Path) -> Path | None:
    curr = start_dir.resolve()
    is_win = platform.system() == "Windows"
    rel_exe = Path("Scripts/python.exe") if is_win else Path("bin/python")

    for parent in [curr] + list(curr.parents):
        for candidate_name in (".venv", "venv"):
            candidate_bin = parent / candidate_name / rel_exe
            if candidate_bin.is_file():
                return candidate_bin

    if "VIRTUAL_ENV" in os.environ:
        env_dir = Path(os.environ["VIRTUAL_ENV"]).resolve()
        candidate_bin = env_dir / rel_exe
        if candidate_bin.is_file():
            return candidate_bin

    return None


def run_tests(test_files: list[Path], ws: Path, test_runner: str = "unittest") -> int:
    if not test_files:
        print("[*] No matching tests found for modified files.")
        return 0

    print(f"[*] Running {len(test_files)} impacted test file(s):")
    for tf in test_files:
        try:
            rel = tf.relative_to(ws)
        except ValueError:
            rel = tf
        print(f"  - {rel}")

    venv_py = find_venv_python(ws)
    if shutil.which("uv"):
        if venv_py:
            runner_bin = ["uv", "run", "--no-project", "--python", str(venv_py)]
        else:
            runner_bin = ["uv", "run", "--no-project", "python"]
    else:
        runner_bin = [str(venv_py)] if venv_py else [sys.executable]

    if test_runner == "pytest":
        cmd = runner_bin + ["-m", "pytest"] + [str(p) for p in test_files]
    else:
        cmd = runner_bin + ["-m", "unittest"] + [str(p) for p in test_files]

    res = subprocess.run(cmd, cwd=str(ws))
    return res.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="AST-aware test impact runner.")
    parser.add_argument("files", nargs="*", type=Path, help="Specific files or tests to run")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace directory")
    parser.add_argument("--all", action="store_true", help="Run all discoverable tests")
    parser.add_argument("--runner", choices=["unittest", "pytest"], default="unittest", help="Test runner")
    args = parser.parse_args()

    ws = args.workspace.resolve()
    if args.all:
        test_dir = ws / "tests"
        if not test_dir.is_dir():
            test_dir = ws
        all_tests = [p for p in test_dir.rglob("test_*.py") if p.is_file()]
        sys.exit(run_tests(all_tests, ws, args.runner))

    if args.files:
        modified = [p.resolve() for p in args.files if p.is_file()]
    else:
        modified = get_git_modified_files(ws)

    if not modified:
        print("[*] No modified Python files found. Use --all to run all tests.")
        sys.exit(0)

    matched = find_matching_tests(ws, modified)
    sys.exit(run_tests(matched, ws, args.runner))


if __name__ == "__main__":
    main()

