#!/usr/bin/env python3
"""Token-efficient Symbol and Dependency Map Generator.
Builds a compressed AST-level structural map of codebases for LLM context.
"""
import argparse
import ast
import re
from pathlib import Path

DEFAULT_SKIP_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache",
    ".mypy_cache", "dist", "build", ".next", ".nuxt", ".cache", "target", "vendor",
}

SUPPORTED_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".rs", ".go"}


def extract_python_symbols(path: Path) -> dict:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except Exception:
        return {}

    symbols = {"imports": [], "classes": {}, "functions": []}

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                symbols["imports"].append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = ", ".join(alias_node.name for alias_node in node.names)
            symbols["imports"].append(f"{node.module}: {names}")
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            sig = _format_func_sig(node)
            doc = ast.get_docstring(node)
            summary = doc.splitlines()[0] if doc else ""
            symbols["functions"].append((sig, summary))
        elif isinstance(node, ast.ClassDef):
            methods = []
            doc = ast.get_docstring(node)
            summary = doc.splitlines()[0] if doc else ""
            bases = [ast.unparse(base_node) for base_node in node.bases]
            base_str = f"({', '.join(bases)})" if bases else ""
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_sig = _format_func_sig(item)
                    methods.append(m_sig)
            symbols["classes"][f"{node.name}{base_str}"] = (summary, methods)

    return symbols


def extract_regex_symbols(path: Path) -> dict[str, list[str]]:
    try:
        source_code = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}

    symbols: dict[str, list[str]] = {"classes": [], "functions": [], "exports": []}
    suffix = path.suffix.lower()

    if suffix in {".js", ".jsx", ".ts", ".tsx"}:
        class_pattern = re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z0-9_$]+)", re.MULTILINE)
        func_pattern = re.compile(
            r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(|"
            r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z0-9_$]+)\s*=>",
            re.MULTILINE,
        )
        export_pattern = re.compile(r"^\s*export\s+(?:default\s+)?(?:const|let|var|function|class)?\s*([A-Za-z0-9_$]+)?", re.MULTILINE)

        for match in class_pattern.finditer(source_code):
            symbols["classes"].append(match.group(1))

        for match in func_pattern.finditer(source_code):
            func_name = match.group(1) or match.group(2)
            if func_name:
                symbols["functions"].append(func_name)

        for match in export_pattern.finditer(source_code):
            export_name = match.group(1)
            if export_name:
                symbols["exports"].append(export_name)

    elif suffix == ".rs":
        type_pattern = re.compile(r"^\s*(?:pub\s+)?(?:struct|enum|trait|impl)\s+([A-Za-z0-9_]+)", re.MULTILINE)
        fn_pattern = re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z0-9_]+)\s*\(", re.MULTILINE)

        for match in type_pattern.finditer(source_code):
            symbols["classes"].append(match.group(1))

        for match in fn_pattern.finditer(source_code):
            symbols["functions"].append(match.group(1))

    elif suffix == ".go":
        type_pattern = re.compile(r"^\s*type\s+([A-Za-z0-9_]+)\s+(?:struct|interface)", re.MULTILINE)
        func_pattern = re.compile(r"^\s*func\s+(?:\([^)]+\)\s+)?([A-Za-z0-9_]+)\s*\(", re.MULTILINE)

        for match in type_pattern.finditer(source_code):
            symbols["classes"].append(match.group(1))

        for match in func_pattern.finditer(source_code):
            symbols["functions"].append(match.group(1))

    return symbols


def _format_func_sig(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = []
    for arg_node in node.args.args:
        ann = f": {ast.unparse(arg_node.annotation)}" if arg_node.annotation else ""
        args.append(f"{arg_node.arg}{ann}")
    ret_str = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{prefix}def {node.name}({', '.join(args)}){ret_str}"


def generate_map(root: Path, max_lines: int = 300) -> str:
    lines = [f"# Codebase Symbol & Dependency Map: {root.name}"]
    lines.append(f"# Generated for fast token-efficient AI context\n")

    files = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in SUPPORTED_EXTENSIONS:
            continue
        if any(part in DEFAULT_SKIP_DIRS for part in p.parts):
            continue
        files.append(p)

    files.sort(key=lambda f: str(f.relative_to(root)))

    for f in files:
        if len(lines) >= max_lines:
            lines.append("... [truncated to fit token budget]")
            break

        rel_path = f.relative_to(root)
        if f.suffix == ".py":
            syms = extract_python_symbols(f)
            if not syms or (not syms["classes"] and not syms["functions"]):
                continue

            lines.append(f"{rel_path}:")
            if syms["imports"]:
                lines.append(f"  imports: {', '.join(syms['imports'][:5])}")
            for cls_name, (doc, methods) in syms["classes"].items():
                doc_part = f" - {doc}" if doc else ""
                lines.append(f"  class {cls_name}{doc_part}")
                for m in methods[:8]:
                    lines.append(f"    {m}")
            for sig, doc in syms["functions"][:10]:
                doc_part = f" - {doc}" if doc else ""
                lines.append(f"  {sig}{doc_part}")
            lines.append("")
        else:
            regex_syms = extract_regex_symbols(f)
            has_regex_syms = any(regex_syms.values())
            lines.append(f"{rel_path}:")
            if has_regex_syms:
                if regex_syms.get("exports"):
                    lines.append(f"  exports: {', '.join(regex_syms['exports'][:5])}")
                for cls_name in regex_syms.get("classes", [])[:8]:
                    lines.append(f"  class/type {cls_name}")
                for func_name in regex_syms.get("functions", [])[:10]:
                    lines.append(f"  fn {func_name}")
            lines.append("")

    return "\n".join(lines)


def render_repo_map(root: Path, max_lines: int = 300) -> str:
    return generate_map(root, max_lines=max_lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate compact AST symbol and dependency map.")
    parser.add_argument("path", nargs="?", default=".", help="Root directory to analyze")
    parser.add_argument("--max-lines", type=int, default=300, help="Maximum lines in output (default: 300)")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    result = generate_map(root, max_lines=args.max_lines)

    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"Symbol map written to {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
