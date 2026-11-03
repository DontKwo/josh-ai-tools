#!/usr/bin/env python3
"""Bundle codebase context, diffs, and symbol maps into token-efficient LLM payloads."""
import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_git_diff(staged: bool = False) -> str:
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--staged")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return res.stdout.strip()
    except Exception:
        return ""


def get_symbol_map(ws: Path) -> str:
    script = REPO_ROOT / "scripts" / "repo_map.py"
    if not script.is_file():
        return ""
    try:
        res = subprocess.run(
            [sys.executable, str(script), str(ws), "--max-lines", "150"],
            capture_output=True,
            text=True,
            check=False,
        )
        return res.stdout.strip()
    except Exception:
        return ""


def pack_files(files: list[Path], root: Path, max_kb: float) -> tuple[list[str], list[tuple[str, int]]]:
    blocks: list[str] = []
    stats: list[tuple[str, int]] = []
    for f in files:
        if not f.is_file():
            continue
        if f.stat().st_size > max_kb * 1024:
            continue
        try:
            rel = str(f.relative_to(root))
        except ValueError:
            rel = str(f)
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            c_bytes = len(content.encode("utf-8"))
            blocks.append(f"### File: {rel}\n```\n{content}\n```\n")
            stats.append((rel, c_bytes))
        except Exception:
            continue
    return blocks, stats


def generate_summary(file_stats: list[tuple[str, int]]) -> str:
    total_files = len(file_stats)
    total_bytes = sum(s[1] for s in file_stats)
    total_tokens = total_bytes // 4
    lines = [
        "## Executive Summary",
        f"- Total files: {total_files}",
        f"- Total bytes: {total_bytes}",
        f"- Estimated tokens: {total_tokens}",
        "",
        "| File | Bytes | Tokens |",
        "|---|---|---|"
    ]
    for rel, c_bytes in file_stats:
        lines.append(f"| {rel} | {c_bytes} | {c_bytes // 4} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Package project context into a token-efficient prompt payload.")
    parser.add_argument("files", nargs="*", type=Path, help="Files to include in context package")
    parser.add_argument("--diff", action="store_true", help="Include current git diff")
    parser.add_argument("--staged", action="store_true", help="Include staged git diff")
    parser.add_argument("--symbols", action="store_true", help="Include AST symbol tree")
    parser.add_argument("--output", type=Path, default=None, help="Output file path (default: stdout)")
    parser.add_argument("--max-file-kb", type=float, default=500.0, help="Skip files larger than max KB")
    args = parser.parse_args()

    ws = Path.cwd()
    output_parts: list[str] = ["# Context Bundle\n"]

    if args.files:
        file_blocks, stats = pack_files(args.files, ws, args.max_file_kb)
        if stats:
            output_parts.append(generate_summary(stats))
    else:
        file_blocks = []

    if args.symbols:
        sym_output = get_symbol_map(ws)
        if sym_output:
            output_parts.append(f"## Codebase Symbol Map\n```\n{sym_output}\n```\n")

    if args.diff or args.staged:
        diff_text = get_git_diff(staged=args.staged)
        if diff_text:
            output_parts.append(f"## Git Changes\n```diff\n{diff_text}\n```\n")

    if file_blocks:
        output_parts.append("## Source Files\n" + "\n".join(file_blocks))

    full_payload = "\n".join(output_parts)
    if args.output:
        args.output.write_text(full_payload, encoding="utf-8")
        print(f"[OK] Context bundle written to {args.output} ({len(full_payload)} chars)")
    else:
        sys.stdout.write(full_payload)


if __name__ == "__main__":
    main()

