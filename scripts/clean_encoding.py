#!/usr/bin/env python3
"""Automated Mojibake & Character Encoding Cleaner.
Scans files for double-encoded UTF-8/Windows-1252 sequences, corrupted placeholders,
and encoding artifacts, restoring clean text without data loss.
"""
import argparse
import sys
from pathlib import Path

# Common double-encoded UTF-8 / Windows-1252 mojibake pairs
MOJIBAKE_MAP = {
    "â€™": "'",       # Right single quotation mark
    "â€˜": "'",       # Left single quotation mark
    "â€œ": '"',       # Left double quotation mark
    "â€\x9d": '"',    # Right double quotation mark
    "â€\x9c": '"',
    "â€¦": "...",     # Ellipsis
    "â€“": "-",       # En dash  # noqa: 2
    "â€”": "-",       # Em dash  # noqa: 1, 2
    "Â°": "°",        # Degree sign
    "Â±": "±",        # Plus-minus sign
    "Â©": "©",        # Copyright sign
    "Â®": "®",        # Registered sign
    "Ã©": "é",        # e acute
    "Ã¨": "è",        # e grave
    "Ã ": "à",        # a grave
    "Ã¡": "á",        # a acute
    "Ã¯": "ï",        # i diaeresis
    "Ã±": "ñ",        # n tilde
    "Ã¼": "ü",        # u diaeresis
    "Ã¶": "ö",        # o diaeresis
    "Ã¤": "ä",        # a diaeresis
    "Â ": " ",        # Stray non-breaking space
    "\ufffd": "",     # Unicode replacement character
}

# Corrupted placeholder replacements (per Claude settings)
PLACEHOLDER_MAP = {
    "'[emoji]'": "'[emoji placeholder]'",
    "'[bookmark]'": "'[bookmark marker]'",
    "'[symbol]'": "'[symbol]'",
    "'[checkmark]'": "'[ok]'",
}

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build"}


def clean_content(content: str, degrees_to_word: bool = False) -> tuple[str, list[str]]:
    changes = []
    new_content = content

    # 1. Clean mojibake sequences
    for bad, good in MOJIBAKE_MAP.items():
        if bad in new_content:
            parts = new_content.split(bad)
            count = len(parts) - 1
            new_content = good.join(parts)
            changes.append(f"Replaced {count}x '{bad}' -> '{good}'")

    # 2. Clean corrupted placeholders
    for bad_ph, good_ph in PLACEHOLDER_MAP.items():
        if bad_ph in new_content:
            parts = new_content.split(bad_ph)
            count = len(parts) - 1
            new_content = good_ph.join(parts)
            changes.append(f"Replaced {count}x {bad_ph} -> {good_ph}")

    # 3. Optional: replace degree symbols with word 'degrees'
    if degrees_to_word and "°" in new_content:
        parts = new_content.split("°")
        count = len(parts) - 1
        new_content = " degrees".join(parts)
        changes.append(f"Replaced {count}x '°' -> ' degrees'")

    return new_content, changes


def process_file(path: Path, dry_run: bool, degrees_to_word: bool) -> int:
    try:
        raw_bytes = path.read_bytes()
    except OSError:
        return 0

    # Try UTF-8 decode
    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        # Fallback to Latin-1
        try:
            content = raw_bytes.decode("latin-1")
        except Exception:
            return 0

    new_content, changes = clean_content(content, degrees_to_word)

    if changes:
        print(f"\n{path}:")
        for change_item in changes:
            print(f"  [+] {change_item}")

        if not dry_run:
            path.write_text(new_content, encoding="utf-8")
            print("  -> Saved fixed file.")
        else:
            print("  -> [DRY-RUN] No changes written.")
        return len(changes)

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan and clean character encoding corruption (mojibake).")
    parser.add_argument("target", nargs="?", default=".", help="File or directory to scan (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="Preview fixes without modifying files")
    parser.add_argument("--degrees-to-word", action="store_true", help="Replace '°' with the word 'degrees'")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        print(f"Error: Target path not found: {target}")
        sys.exit(1)

    files = [target] if target.is_file() else [
        f for f in target.rglob("*")
        if f.is_file() and SKIP_DIRS.isdisjoint(f.parts) and f.suffix in (".py", ".txt", ".md", ".json", ".csv", ".html", ".js", ".ts")
    ]

    print("=" * 60)
    print("      Josh's AI Tools Mojibake & Encoding Cleaner")
    print("=" * 60)
    if args.dry_run:
        print("MODE: DRY RUN (preview only)\n")

    total_fixed_files = 0
    for f in files:
        fixes = process_file(f, args.dry_run, args.degrees_to_word)
        if fixes > 0:
            total_fixed_files += 1

    print("\n" + "=" * 60)
    print(f"Scan complete. {total_fixed_files} file(s) had encoding artifacts.")
    print("=" * 60)


if __name__ == "__main__":
    main()

