#!/usr/bin/env python3
"""Token counter and context budget analyzer for AI developer workflows."""
import argparse
import sys
from pathlib import Path

IGNORED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules", "dist",
    "build", ".ai_checkpoints", ".cache", ".pytest_cache",
}

# Standard multipliers for code and prose token estimation
CHARS_PER_TOKEN = 3.8
WORDS_PER_TOKEN = 0.75


def estimate_tokens(text: str) -> dict[str, int]:
    chars = len(text)
    words = len(text.split())
    lines = len(text.splitlines())

    # Weighted estimate reflecting programming syntax punctuation
    tokens = max(1, int(chars / CHARS_PER_TOKEN))
    return {
        "chars": chars,
        "words": words,
        "lines": lines,
        "tokens": tokens,
    }


def analyze_file(path: Path) -> dict[str, int] | None:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return estimate_tokens(content)
    except Exception:
        return None


def format_number(val: int) -> str:
    return f"{val:,}"


def scan_directory(target: Path, max_depth: int = 5) -> list[tuple[Path, dict[str, int]]]:
    results: list[tuple[Path, dict[str, int]]] = []
    if target.is_file():
        info = analyze_file(target)
        if info:
            results.append((target, info))
        return results

    for p in target.rglob("*"):
        if not p.is_file():
            continue
        if any(part in IGNORED_DIRS for part in p.parts):
            continue
        info = analyze_file(p)
        if info:
            results.append((p, info))
    return results


def print_budget_report(results: list[tuple[Path, dict[str, int]]], root: Path, threshold: int) -> None:
    results.sort(key=lambda item: item[1]["tokens"], reverse=True)

    total_tokens = sum(info["tokens"] for _, info in results)
    total_lines = sum(info["lines"] for _, info in results)
    total_files = len(results)

    print("=" * 72)
    print("                    AI Context Token Budget Report")
    print("=" * 72)
    print(f"{'File':<46} {'Lines':>8} {'Tokens':>12}")
    print("-" * 72)

    flagged_count = 0
    for path, info in results:
        try:
            rel = str(path.relative_to(root))
        except ValueError:
            rel = str(path)

        if len(rel) > 44:
            rel = "..." + rel[-41:]

        is_large = info["tokens"] >= threshold
        marker = " [!]" if is_large else ""
        if is_large:
            flagged_count += 1

        print(f"{rel:<46} {format_number(info['lines']):>8} {format_number(info['tokens']) + marker:>12}")

    print("-" * 72)
    print(f"Total Scanned Files : {total_files}")
    print(f"Total Lines         : {format_number(total_lines)}")
    print(f"Total Estimated Tokens : {format_number(total_tokens)}")
    if flagged_count:
        print(f"[!] Warning: {flagged_count} file(s) exceed {format_number(threshold)} tokens.")
    print("=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate token usage across files and directories.")
    parser.add_argument("target", nargs="?", default=".", help="Target file or directory path")
    parser.add_argument("--threshold", type=int, default=5000, help="Token threshold to flag large files")
    args = parser.parse_args()

    root = Path(args.target).resolve()
    if not root.exists():
        sys.stderr.write(f"Error: Path does not exist: {root}\n")
        sys.exit(1)

    results = scan_directory(root)
    print_budget_report(results, root, args.threshold)


if __name__ == "__main__":
    main()

