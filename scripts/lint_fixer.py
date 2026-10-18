#!/usr/bin/env python3
"""Safe Auto-Fixer for claudemd_linter mechanical violations.
Strictly limited to 100% deterministic, low-risk, formulaic fixes:
- Code 15: '== None' -> 'is None' and '!= None' -> 'is not None'
- Code 2: Non-standard unicode (curly quotes -> ASCII quotes, ellipsis -> ..., nbsp -> space, BOM -> stripped)
- Code 3: Strip unicode emojis (optional via --fix-emojis)

CRITICAL SAFETY GUARANTEE:
Em dashes (Code 1) are NEVER automatically replaced.
Rule 1 mandates completely rewriting the sentence, which cannot be automated safely.
"""
import argparse
import re
import sys
from pathlib import Path

# Safe Unicode translation table (Rule 2)
UNICODE_REPLACEMENTS = {
    "\u2018": "'",   # Left single curly quote
    "\u2019": "'",   # Right single curly quote
    "\u201c": '"',   # Left double curly quote
    "\u201d": '"',   # Right double curly quote
    "\u2026": "...", # Ellipsis
    "\u00a0": " ",   # Non-breaking space
    "\u200b": "",    # Zero-width space
    "\ufeff": "",    # BOM
    "\u00ad": "",    # Soft hyphen
    "\u2032": "'",   # Prime mark
    "\u2033": '"',   # Double prime mark
}

EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF"
    "]"
)

# Rule 15 patterns
EQ_NONE_RE = re.compile(r"==\s*None\b")
NE_NONE_RE = re.compile(r"!=\s*None\b")


def fix_line(line: str, lineno: int, path: Path, fix_emojis: bool) -> tuple[str, list[str]]:
    changes = []
    new_line = line

    # Check for em dash (Rule 1) - explicitly refuse automated fix
    if "\u2014" in line:
        print(f"  [!] Skipped Rule 1 (em dash) at {path.name}:{lineno} - Manual sentence rewrite required by linter rules.")

    # 1. Rule 2: Safe Unicode normalization
    for bad_char, good_char in UNICODE_REPLACEMENTS.items():
        if bad_char in new_line:
            new_line = new_line.replace(bad_char, good_char)
            changes.append(f"Rule 2 (normalized unicode '{bad_char}' -> '{good_char}')")

    # 2. Rule 3: Emoji removal (only if explicitly enabled)
    if fix_emojis and EMOJI_RE.search(new_line):
        new_line = EMOJI_RE.sub("", new_line)
        changes.append("Rule 3 (removed emoji)")

    # 3. Rule 15: == None and != None in Python files
    if path.suffix == ".py":
        if EQ_NONE_RE.search(new_line):
            new_line = EQ_NONE_RE.sub("is None", new_line)
            changes.append("Rule 15 ('== None' -> 'is None')")
        if NE_NONE_RE.search(new_line):
            new_line = NE_NONE_RE.sub("is not None", new_line)
            changes.append("Rule 15 ('!= None' -> 'is not None')")

    return new_line, changes


def fix_file(path: Path, dry_run: bool, fix_emojis: bool) -> int:
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return 0

    lines = content.splitlines(keepends=True)
    modified_lines = []
    total_fixes = 0

    for i, line in enumerate(lines, 1):
        fixed, changes = fix_line(line, i, path, fix_emojis)
        if changes:
            total_fixes += len(changes)
            print(f"  {path.name}:{i} -> {', '.join(changes)}")
        modified_lines.append(fixed)

    if total_fixes > 0 and not dry_run:
        path.write_text("".join(modified_lines), encoding="utf-8")
        print(f"[OK] Applied {total_fixes} safe fixes to {path}")
    elif total_fixes > 0 and dry_run:
        print(f"[DRY-RUN] Would apply {total_fixes} safe fixes to {path}")

    return total_fixes


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply guaranteed safe fixes for claudemd_linter.")
    parser.add_argument("target", help="File or directory to fix")
    parser.add_argument("--dry-run", action="store_true", help="Preview fixes without modifying files")
    parser.add_argument("--fix-emojis", action="store_true", help="Also safely strip unicode emojis (Rule 3)")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        print(f"Error: Target path not found: {target}")
        sys.exit(1)

    files = [target] if target.is_file() else [f for f in target.rglob("*") if f.is_file() and f.suffix in (".py", ".md", ".txt", ".js", ".ts", ".html")]

    print("=" * 60)
    print("           Josh's AI Tools Safe Auto-Fixer")
    print("=" * 60)
    if args.dry_run:
        print("MODE: DRY RUN (no files will be written)\n")

    total_changes = 0
    for f in files:
        if any(skip in f.parts for skip in {".git", ".venv", "node_modules", "__pycache__"}):
            continue
        total_changes += fix_file(f, args.dry_run, args.fix_emojis)

    print("\n" + "=" * 60)
    action_word = "Would fix" if args.dry_run else "Fixed"
    print(f"Complete: {action_word} {total_changes} total violations safely.")
    print("=" * 60)


if __name__ == "__main__":
    main()
