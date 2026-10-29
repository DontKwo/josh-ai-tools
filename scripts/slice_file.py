#!/usr/bin/env python3
"""Token-Efficient File Slicer for AI Tooling.
Reads exact line ranges, head, or tail of files with line numbers, avoiding full-file context dumps.
"""
import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except OSError:
        sys.stdout = sys.stdout


def slice_lines(
    file_path: Path,
    start: int = 1,
    end: int | None = None,
    head: int | None = None,
    tail: int | None = None,
    numbered: bool = True,
) -> None:
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        return

    lines = content.splitlines()
    total_lines = len(lines)

    if head is not None:
        start = 1
        end = min(total_lines, head)
    elif tail is not None:
        start = max(1, total_lines - tail + 1)
        end = total_lines
    else:
        start = max(1, start)
        end = min(total_lines, end if end is not None else total_lines)

    print(f"--- File: {file_path.name} (Lines {start}-{end} of {total_lines}) ---")
    for i in range(start - 1, end):
        if numbered:
            print(f"{i + 1:5d} | {lines[i]}")
        else:
            print(lines[i])


def parse_range(range_str: str) -> tuple[int, int | None]:
    """Parse range string like '50-100', '50:100', or '50'."""
    clean = range_str.replace(":", "-")
    if "-" in clean:
        parts = clean.split("-", 1)
        start = int(parts[0]) if parts[0].strip() else 1
        end = int(parts[1]) if parts[1].strip() else None
        return start, end
    return int(clean), int(clean)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect targeted line ranges of a file with line numbers"
    )
    parser.add_argument("target", help="File path, optionally with range (e.g. main.py or main.py:50-100)")
    parser.add_argument("range", nargs="?", help="Line range (e.g. 50-100, 50:, :100)")
    parser.add_argument("--head", type=int, help="Show first N lines")
    parser.add_argument("--tail", type=int, help="Show last N lines")
    parser.add_argument("--no-numbers", action="store_true", help="Omit line numbers")

    args = parser.parse_args()

    target_str = args.target
    start = 1
    end = None

    if ":" in target_str and not Path(target_str).exists():
        parts = target_str.split(":", 1)
        target_path = Path(parts[0]).resolve()
        start, end = parse_range(parts[1])
    else:
        target_path = Path(target_str).resolve()
        if args.range:
            start, end = parse_range(args.range)

    if not target_path.exists() or not target_path.is_file():
        print(f"Error: File does not exist: {target_path}", file=sys.stderr)
        return 1

    slice_lines(
        target_path,
        start=start,
        end=end,
        head=args.head,
        tail=args.tail,
        numbered=not args.no_numbers,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

