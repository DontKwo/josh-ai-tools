#!/usr/bin/env python3
"""Token Minifier for AI Instruction Files (CLAUDE.md, .cursorrules, .clinerules, etc.).
Compacts whitespace, comments, and formatting while preserving 100% of directives.
"""
import argparse
import re
import sys
from pathlib import Path


def minify_text(text: str) -> str:
    # 1. Strip HTML/Markdown comments <!-- ... -->
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    lines = []
    prev_blank = False

    for line in text.splitlines():
        trimmed = line.rstrip()
        if not trimmed:
            if not prev_blank and lines:
                lines.append("")
                prev_blank = True
        else:
            lines.append(trimmed)
            prev_blank = False

    minified = "\n".join(lines).strip() + "\n"
    return minified


def process_file(path: Path, in_place: bool, output_path: Path | None) -> None:
    original = path.read_text(encoding="utf-8")
    minified = minify_text(original)

    orig_bytes = len(original.encode("utf-8"))
    mini_bytes = len(minified.encode("utf-8"))
    saved_bytes = orig_bytes - mini_bytes
    pct = (saved_bytes / orig_bytes * 100) if orig_bytes else 0

    # Approx token estimate: 4 chars per token
    orig_tokens = len(original) // 4
    mini_tokens = len(minified) // 4
    saved_tokens = orig_tokens - mini_tokens

    target = path if in_place else (output_path or path.with_suffix(".min.md"))
    target.write_text(minified, encoding="utf-8")

    print(f"[OK] Minified {path.name} -> {target.name}")
    print(f"     Bytes:  {orig_bytes} -> {mini_bytes} (-{saved_bytes} B, -{pct:.1f}%)")
    print(f"     Tokens: ~{orig_tokens} -> ~{mini_tokens} (-~{saved_tokens} tokens)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Minify AI instructions files for token efficiency.")
    parser.add_argument("file", help="Path to instruction file (CLAUDE.md, .cursorrules, etc.)")
    parser.add_argument("-i", "--in-place", action="store_true", help="Overwrite the original file directly")
    parser.add_argument("-o", "--output", help="Write to specified output file")
    args = parser.parse_args()

    target = Path(args.file).resolve()
    if not target.is_file():
        print(f"Error: File not found: {target}")
        sys.exit(1)

    out = Path(args.output).resolve() if args.output else None
    process_file(target, args.in_place, out)


if __name__ == "__main__":
    main()
