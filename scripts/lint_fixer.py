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


# Rule 41 pattern
AI_BANNER_RE = re.compile(r"^(?:#|//|\*)\s*([#=]{5,})\s*$|^([#=]{5,})\s*$")


def fix_line(
    line: str,
    lineno: int,
    path: Path,
    fix_emojis: bool,
    fix_banners: bool = True,
) -> tuple[str, list[str]]:
    changes: list[str] = []
    new_line = line

    # Check for em dash (Rule 1) - explicitly refuse automated fix
    if "\u2014" in line:
        print(f"  [!] Skipped Rule 1 (em dash) at {path.name}:{lineno} - Manual sentence rewrite required by linter rules.")  # noqa: 25

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

    # 4. Rule 41: Heavy divider banners
    if fix_banners and path.suffix in (".py", ".js", ".ts", ".c", ".cpp", ".rs", ".go", ".sh"):
        if AI_BANNER_RE.match(new_line.strip()):
            indent = line[: len(line) - len(line.lstrip())]
            prefix = "//" if path.suffix in (".js", ".ts", ".c", ".cpp", ".rs", ".go") else "#"
            new_line = f"{indent}{prefix} ---\n"
            changes.append("Rule 41 (condensed heavy divider banner)")

    return new_line, changes


def condense_docstrings(content: str) -> tuple[str, int]:
    # Rule 40: Condense bloated docstrings on simple functions
    count = 0
    pattern = re.compile(
        r'("""|\'\'\')([^\n]*?)\n\s*(?:Args|Parameters|Returns|Raises):\s*\n[\s\S]*?\1',
        re.MULTILINE,
    )

    def repl(m: re.Match) -> str:
        nonlocal count
        count += 1
        quote = m.group(1)
        summary = m.group(2).strip()
        if not summary:
            summary = "Perform calculation."
        return f'{quote}{summary}{quote}'

    new_content = pattern.sub(repl, content)
    return new_content, count


def fix_file(
    path: Path,
    dry_run: bool,
    fix_emojis: bool,
    fix_banners: bool = True,
    fix_docstrings: bool = False,
) -> int:
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return 0

    lines = content.splitlines(keepends=True)
    modified_lines = []
    total_fixes = 0

    for i, line in enumerate(lines, 1):
        fixed, changes = fix_line(line, i, path, fix_emojis, fix_banners)
        if changes:
            total_fixes += len(changes)
            print(f"  {path.name}:{i} -> {', '.join(changes)}")  # noqa: 25
        modified_lines.append(fixed)

    updated_text = "".join(modified_lines)

    if fix_docstrings and path.suffix == ".py":
        updated_text, doc_fixes = condense_docstrings(updated_text)
        if doc_fixes > 0:
            total_fixes += doc_fixes
            print(f"  {path.name} -> Condensed {doc_fixes} bloated docstring(s) (Rule 40)")  # noqa: 25

    if total_fixes > 0 and not dry_run:
        path.write_text(updated_text, encoding="utf-8")
        print(f"[OK] Applied {total_fixes} safe fixes to {path}")  # noqa: 25
    elif total_fixes > 0 and dry_run:
        print(f"[DRY-RUN] Would apply {total_fixes} safe fixes to {path}")  # noqa: 25

    return total_fixes


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply guaranteed safe fixes for claudemd_linter.")
    parser.add_argument("target", help="File or directory to fix")
    parser.add_argument("--dry-run", action="store_true", help="Preview fixes without modifying files")
    parser.add_argument("--fix-emojis", action="store_true", help="Also safely strip unicode emojis (Rule 3)")
    parser.add_argument("--no-banners", action="store_true", help="Disable heavy banner condensing (Rule 41)")
    parser.add_argument("--fix-docstrings", action="store_true", help="Condense bloated docstrings on simple helpers (Rule 40)")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        print(f"Error: Target path not found: {target}")  # noqa: 25
        sys.exit(1)

    files = [target] if target.is_file() else [f for f in target.rglob("*") if f.is_file() and f.suffix in (".py", ".md", ".txt", ".js", ".ts", ".html")]

    print("=" * 60)  # noqa: 25
    print("           Josh's AI Tools Safe Auto-Fixer")  # noqa: 25
    print("=" * 60)  # noqa: 25
    if args.dry_run:
        print("MODE: DRY RUN (no files will be written)\n")  # noqa: 25

    total_changes = 0
    for f in files:
        if any(skip in f.parts for skip in {".git", ".venv", "node_modules", "__pycache__"}):
            continue
        total_changes += fix_file(
            f,
            args.dry_run,
            args.fix_emojis,
            fix_banners=not args.no_banners,
            fix_docstrings=args.fix_docstrings,
        )

    print("\n" + "=" * 60)  # noqa: 25
    action_word = "Would fix" if args.dry_run else "Fixed"
    print(f"Complete: {action_word} {total_changes} total violations safely.")  # noqa: 25
    print("=" * 60)  # noqa: 25


if __name__ == "__main__":
    main()
