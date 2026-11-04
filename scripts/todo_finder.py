"""Scans files for TODOs and other tags and outputs a summary."""

import argparse
import re
import sys
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence


class TodoItem(NamedTuple):
    tag: str
    filepath: str
    line_number: int
    author: Optional[str]
    description: str


SUPPORTED_EXTENSIONS = {
    ".py", ".md", ".txt", ".rst",
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".html", ".htm", ".css", ".scss", ".vue", ".svelte",
    ".rs", ".go", ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp",
    ".sh", ".bash", ".zsh",
}

EXCLUDED_DIRS = {
    ".venv", "venv", ".toolchain", "node_modules", ".git", "__pycache__",
    ".pytest_cache", ".mypy_cache", "dist", "build", ".next", ".nuxt",
    ".cache", "target", "vendor", ".ai_checkpoints",
}

TAGS = ["TODO", "FIXME", "BUG", "HACK", "NOTE", "OPTIMIZE"]
TAG_PATTERN = re.compile(r"(?:#|//|/\*|<!--)\s*(" + "|".join(TAGS) + r")\b\s*(?:\(([^)]+)\))?[:\s-]*\s*(.*)", re.IGNORECASE)


def clean_description(desc: str) -> str:
    desc = desc.strip()
    if desc.endswith("-->"):
        desc = desc[:-3].strip()
    if desc.endswith("*/"):
        desc = desc[:-2].strip()
    return desc


def is_scannable_file(fpath: Path) -> bool:
    if fpath.suffix not in SUPPORTED_EXTENSIONS:
        return False
    return EXCLUDED_DIRS.isdisjoint(fpath.parts)


def scan_file(filepath: Path) -> List[TodoItem]:
    items: List[TodoItem] = []
    try:
        lines = filepath.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return items
    for i, line in enumerate(lines, 1):
        match = TAG_PATTERN.search(line)
        if match:
            tag = match.group(1).upper()
            author = match.group(2).strip() if match.group(2) else None
            desc = clean_description(match.group(3))
            items.append(TodoItem(tag, str(filepath), i, author, desc))
    return items


def scan_directory(target_path: Path) -> List[TodoItem]:
    items: List[TodoItem] = []
    if target_path.is_file():
        return scan_file(target_path) if is_scannable_file(target_path) else []
    for f in target_path.rglob("*"):
        if f.is_file() and is_scannable_file(f):
            items.extend(scan_file(f))
    return items


def print_markdown_table(items: List[TodoItem]) -> None:
    print("| Tag | File | Line | Author | Description |")  # noqa: 25
    print("|---|---|---|---|---|")  # noqa: 25
    for item in items:
        author = item.author if item.author else "-"
        print(f"| {item.tag} | {item.filepath} | {item.line_number} | {author} | {item.description} |")  # noqa: 25


def print_summary(items: List[TodoItem]) -> None:
    for item in items:
        author_str = f"({item.author}) " if item.author else ""
        print(f"[{item.tag}] {item.filepath}:{item.line_number} {author_str}{item.description}")  # noqa: 25


def parse_args(args: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find TODOs in codebase.")
    parser.add_argument("target", nargs="?", default=".", help="Target path")
    parser.add_argument("--markdown", action="store_true", help="Markdown format")
    return parser.parse_args(args)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args(sys.argv[1:])
    target_path = Path(args.target).resolve()
    items = scan_directory(target_path)
    if args.markdown:
        print_markdown_table(items)
    else:
        print_summary(items)


if __name__ == "__main__":
    main()
