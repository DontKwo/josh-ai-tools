"""Reusable keyword/regex grep across files and folders, with skip-dir defaults."""
import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_SKIP_DIRS = {
    ".venv", "venv", ".git", "__pycache__", "node_modules",
    ".pytest_cache", ".cache", "dist", "build", ".mypy_cache",
}


def iter_files(root: Path, exts: list[str] | None, skip_dirs: set[str]) -> list[Path]:
    if root.is_file():
        return [root]
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip_dirs for part in path.parts):
            continue
        if exts and path.suffix.lstrip(".") not in exts:
            continue
        files.append(path)
    return files


def search(files: list[Path], pattern: re.Pattern, context: int) -> tuple[list[str], int]:
    out = []
    match_count = 0
    for f in files:
        try:
            lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines):
            if pattern.search(line):
                match_count += 1
                start = max(0, i - context)
                end = min(len(lines), i + context + 1)
                for j in range(start, end):
                    marker = ">" if j == i else " "
                    out.append(f"{f}:{j + 1}:{marker} {lines[j]}")
                if context:
                    out.append("--")
    return out, match_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Grep for a keyword/regex across files and folders.")
    parser.add_argument("keyword", help="Literal keyword or regex pattern to search for")
    parser.add_argument("path", nargs="?", default=".", help="File or folder to search (default: cwd)")
    parser.add_argument("--ext", help="Comma-separated extensions to include, e.g. py,md")
    parser.add_argument("--regex", action="store_true", help="Treat keyword as a regex instead of a literal string")
    parser.add_argument("--ignore-case", action="store_true", help="Case-insensitive search")
    parser.add_argument("--context", type=int, default=0, help="Lines of context to show around each match")
    parser.add_argument("--skip-dir", action="append", default=[], help="Additional directory name to skip (repeatable)")
    args = parser.parse_args()

    flags = re.IGNORECASE if args.ignore_case else 0
    needle = args.keyword if args.regex else re.escape(args.keyword)
    pattern = re.compile(needle, flags)

    exts = [e.strip() for e in args.ext.split(",")] if args.ext else None
    skip_dirs = DEFAULT_SKIP_DIRS | set(args.skip_dir)

    files = iter_files(Path(args.path), exts, skip_dirs)
    results, match_count = search(files, pattern, args.context)

    if not results:
        print("No matches.")
        sys.exit(0)
    print("\n".join(results))
    print(f"\n{match_count} matching lines found.")


if __name__ == "__main__":
    main()
