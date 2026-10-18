#!/usr/bin/env python3
"""Token-efficient Symbol and Dependency Map Generator.
Builds a compressed AST-level structural map of codebases for LLM context.
"""
import argparse
import ast
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
            names = ", ".join(a.name for a in node.names)
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
            bases = [ast.unparse(b) for b in node.bases]
            base_str = f"({', '.join(bases)})" if bases else ""
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_sig = _format_func_sig(item)
                    methods.append(m_sig)
            symbols["classes"][f"{node.name}{base_str}"] = (summary, methods)

    return symbols


def _format_func_sig(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = []
    for a in node.args.args:
        ann = f": {ast.unparse(a.annotation)}" if a.annotation else ""
        args.append(f"{a.arg}{ann}")
    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{prefix}def {node.name}({', '.join(args)}){ret}"


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
            # Simple line-count preview for non-Python supported files
            lines.append(f"{rel_path}")

    return "\n".join(lines)


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
