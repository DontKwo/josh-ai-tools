#!/usr/bin/env python3
"""AST-based descriptive variable name auditor for code quality enforcement."""
import argparse
import ast
import sys
from pathlib import Path

IGNORED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules", "dist",
    "build", ".ai_checkpoints", ".cache", ".pytest_cache",
}

# Standard exceptions for conventional short names
ALLOWED_SINGLE_CHARS = {"_", "i", "j", "k", "x", "y", "z", "e", "f"}

VAGUE_NAMES = {
    "temp", "tmp", "data", "obj", "val", "res", "ret", "var", "foo",
    "bar", "baz", "stuff", "thing", "dummy", "item", "arg", "param",
    "info", "out", "output", "inp", "input_data", "my_list", "data_dict",
}


def is_descriptive_name(name: str, context: str) -> tuple[bool, str]:
    if name.startswith("__") and name.endswith("__"):
        return True, ""
    if name in ALLOWED_SINGLE_CHARS:
        return True, ""
    if len(name) <= 2:
        return False, f"Variable name '{name}' is too short (<= 2 chars)."
    if name.lower() in VAGUE_NAMES:
        return False, f"Variable name '{name}' is non-descriptive or generic."
    return True, ""


class VariableAuditor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.violations: list[tuple[int, str, str]] = []

    def check_identifier(self, name: str, lineno: int, context: str) -> None:
        valid, reason = is_descriptive_name(name, context)
        if not valid:
            self.violations.append((lineno, name, reason))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for param_node in node.args.args:
            if param_node.arg != "self" and param_node.arg != "cls":
                self.check_identifier(param_node.arg, node.lineno, "parameter")
        for kw_param_node in node.args.kwonlyargs:
            self.check_identifier(kw_param_node.arg, node.lineno, "kw_parameter")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        for param_node in node.args.args:
            if param_node.arg != "self" and param_node.arg != "cls":
                self.check_identifier(param_node.arg, node.lineno, "parameter")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            self.check_identifier(node.id, node.lineno, "assignment")
        self.generic_visit(node)


def audit_file(path: Path) -> list[tuple[int, str, str]]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except Exception:
        return []

    auditor = VariableAuditor(path)
    auditor.visit(tree)
    return auditor.violations


def scan_directory(target: Path) -> dict[Path, list[tuple[int, str, str]]]:
    findings: dict[Path, list[tuple[int, str, str]]] = {}
    if target.is_file():
        if target.suffix == ".py":
            file_violations = audit_file(target)
            if file_violations:
                findings[target] = file_violations
        return findings

    for file_path in target.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in file_path.parts):
            continue
        file_violations = audit_file(file_path)
        if file_violations:
            findings[file_path] = file_violations
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit codebase for descriptive variable and parameter names.")
    parser.add_argument("target", nargs="?", default=".", help="Target file or directory")
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        sys.stderr.write(f"Error: Target path does not exist: {target_path}\n")
        sys.exit(1)

    findings = scan_directory(target_path)
    total_violations = sum(len(hits) for hits in findings.values())

    if not total_violations:
        print("[OK] Clean. All variable and parameter names are descriptive.")
        sys.exit(0)

    print("=" * 70)
    print(f"  [!] Found {total_violations} non-descriptive variable/parameter name(s)")
    print("=" * 70)
    for path, hits in findings.items():
        try:
            rel = str(path.relative_to(target_path))
        except ValueError:
            rel = str(path)
        print(f"\n{rel}:")
        for lineno, name, reason in hits:
            print(f"  Line {lineno:<4} [{name}]: {reason}")
    print("=" * 70)
    sys.exit(1)


if __name__ == "__main__":
    main()
