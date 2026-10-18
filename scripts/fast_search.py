#!/usr/bin/env python3
"""Fast, Token-Efficient Directory-Aware Search for AI Tooling.
Performs regex or literal text search across codebases, automatically ignoring
version control, virtual environments, binaries, and dependencies.
"""
import argparse
import re
import sys
from pathlib import Path

DEFAULT_IGNORES = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "node_modules", "bower_components", "dist",
    "build", ".next", ".nuxt", "target", ".idea", ".vscode", ".lint_cache.json",
}

# Configure stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def is_binary_file(path: Path) -> bool:
    """Check if file is binary by looking for null bytes."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except Exception:
        return True


def search_in_file(
    path: Path,
    pattern: re.Pattern,
    context: int = 1,
    max_matches_per_file: int = 10,
) -> list[tuple[int, list[str]]]:
    """Search for pattern in a file and return matches with context lines."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    lines = content.splitlines()
    matches: list[tuple[int, list[str]]] = []
    matched_lines: set[int] = set()

    for idx, line in enumerate(lines):
        if pattern.search(line):
            matched_lines.add(idx)
            if len(matched_lines) >= max_matches_per_file:
                break

    if not matched_lines:
        return []

    # Assemble context chunks
    for m_idx in sorted(matched_lines):
        start = max(0, m_idx - context)
        end = min(len(lines), m_idx + context + 1)
        chunk_lines = [
            f"{'->' if i == m_idx else '  '} {i + 1:4d} | {lines[i]}"
            for i in range(start, end)
        ]
        matches.append((m_idx + 1, chunk_lines))

    return matches


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fast, token-efficient regex & symbol search for codebases"
    )
    parser.add_argument("query", help="Regex or literal search string")
    parser.add_argument("target", nargs="?", default=".", help="Target directory (default: .)")
    parser.add_argument("-i", "--ignore-case", action="store_true", help="Case-insensitive search")
    parser.add_argument("-C", "--context", type=int, default=1, help="Context lines around match (default: 1)")
    parser.add_argument("--ext", help="Filter by comma-separated file extensions (e.g. py,ts,md)")
    parser.add_argument("--max-results", "-m", type=int, default=30, help="Maximum total matches to return (default: 30)")
    parser.add_argument("--names-only", action="store_true", help="Only list matching filenames")

    args = parser.parse_args()
    target_path = Path(args.target).resolve()

    flags = re.IGNORECASE if args.ignore_case else 0
    try:
        pattern = re.compile(args.query, flags)
    except re.error as e:
        print(f"Error: Invalid regular expression '{args.query}': {e}", file=sys.stderr)
        return 1

    allowed_exts = None
    if args.ext:
        allowed_exts = {f".{e.strip().lstrip('.').lower()}" for e in args.ext.split(",") if e.strip()}

    total_matches = 0
    matched_files = 0

    if target_path.is_file():
        files_to_scan = [target_path]
    else:
        files_to_scan = []
        for p in target_path.rglob("*"):
            if not p.is_file():
                continue
            if any(part in DEFAULT_IGNORES for part in p.parts):
                continue
            if allowed_exts and p.suffix.lower() not in allowed_exts:
                continue
            files_to_scan.append(p)

    for p in files_to_scan:
        if total_matches >= args.max_results:
            print(f"\n[!] Reached maximum limit of {args.max_results} results. Narrow your search.")
            break

        if is_binary_file(p):
            continue

        results = search_in_file(p, pattern, context=args.context)
        if results:
            matched_files += 1
            if args.names_only:
                print(p)
                continue

            try:
                rel = p.relative_to(Path.cwd())
            except ValueError:
                rel = p
            print(f"File: {rel}")
            for line_no, chunk in results:
                total_matches += 1
                for c in chunk:
                    print(c)
                print()

    if not args.names_only:
        print(f"Total: {total_matches} match(es) across {matched_files} file(s).")

    return 0 if matched_files > 0 else 1


if __name__ == "__main__":
    sys.exit(main())

