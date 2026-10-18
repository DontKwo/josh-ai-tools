#!/usr/bin/env python3
"""Token-Efficient Directory Tree & Codebase Overview for AI Tooling.
Provides a clean, compact visual hierarchy with file sizes and line counts,
automatically ignoring vendor packages, version control, and temporary caches.
"""
import argparse
import sys
from pathlib import Path

DEFAULT_IGNORES = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "node_modules", "bower_components", "dist",
    "build", ".next", ".nuxt", "target", ".idea", ".vscode", ".lint_cache.json",
}


def count_lines_and_size(p: Path) -> tuple[int, float]:
    """Return line count and size in KB for a text file."""
    try:
        size_kb = p.stat().st_size / 1024
        with open(p, "rb") as f:
            lines = sum(1 for _ in f)
        return lines, size_kb
    except Exception:
        return 0, 0.0


def render_tree(
    dir_path: Path,
    prefix: str = "",
    current_depth: int = 0,
    max_depth: int = 4,
    allowed_exts: set[str] | None = None,
    max_files: int = 150,
    stats: bool = False,
    file_counter: list[int] | None = None,
) -> list[str]:
    if file_counter is None:
        file_counter = [0]

    if current_depth > max_depth or file_counter[0] >= max_files:
        return []

    lines: list[str] = []
    try:
        entries = sorted(dir_path.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
    except (PermissionError, OSError):
        return [f"{prefix}[Permission Denied]"]

    entries = [e for e in entries if e.name not in DEFAULT_IGNORES and not e.name.startswith(".")]

    total_entries = len(entries)
    for i, entry in enumerate(entries):
        if file_counter[0] >= max_files:
            lines.append(f"{prefix}... [Limit reached: {max_files} files displayed]")
            break

        is_last = (i == total_entries - 1)
        connector = "└── " if is_last else "├── "
        next_prefix = prefix + ("    " if is_last else "│   ")

        if entry.is_dir():
            lines.append(f"{prefix}{connector}{entry.name}/")
            lines.extend(
                render_tree(
                    entry,
                    prefix=next_prefix,
                    current_depth=current_depth + 1,
                    max_depth=max_depth,
                    allowed_exts=allowed_exts,
                    max_files=max_files,
                    stats=stats,
                    file_counter=file_counter,
                )
            )
        elif entry.is_file():
            if allowed_exts and entry.suffix.lower() not in allowed_exts:
                continue

            file_counter[0] += 1
            if stats:
                lcount, size_kb = count_lines_and_size(entry)
                lines.append(f"{prefix}{connector}{entry.name} ({lcount} lines, {size_kb:.1f} KB)")
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    return lines


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Token-efficient codebase hierarchy and file size visualizer"
    )
    parser.add_argument("target", nargs="?", default=".", help="Target directory (default: .)")
    parser.add_argument("--depth", "-d", type=int, default=3, help="Maximum recursion depth (default: 3)")
    parser.add_argument("--ext", help="Filter by comma-separated file extensions (e.g. py,js,ts)")
    parser.add_argument("--stats", "-s", action="store_true", help="Display line count and file size in KB")
    parser.add_argument("--max-files", "-m", type=int, default=150, help="Maximum files to display (default: 150)")

    args = parser.parse_args()
    target_path = Path(args.target).resolve()

    if not target_path.exists() or not target_path.is_dir():
        print(f"Error: Directory does not exist: {target_path}", file=sys.stderr)
        return 1

    allowed_exts = None
    if args.ext:
        allowed_exts = {f".{e.strip().lstrip('.').lower()}" for e in args.ext.split(",") if e.strip()}

    print(f"{target_path.name}/")
    tree_lines = render_tree(
        target_path,
        max_depth=args.depth,
        allowed_exts=allowed_exts,
        max_files=args.max_files,
        stats=args.stats,
    )
    for line in tree_lines:
        print(line)

    return 0


if __name__ == "__main__":
    sys.exit(main())

