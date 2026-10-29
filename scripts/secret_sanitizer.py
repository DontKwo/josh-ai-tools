#!/usr/bin/env python3
"""Pre-prompt secret and credential scanner and masker."""
import argparse
import re
import sys
from pathlib import Path

IGNORED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules", "dist",
    "build", ".ai_checkpoints", ".cache",
}

SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("OpenAI API Key", re.compile(r"\bsk-[a-zA-Z0-9]{20,}\b")),
    ("Anthropic API Key", re.compile(r"\bsk-ant-[a-zA-Z0-9\-_]{20,}\b")),
    ("GitHub Personal Access Token", re.compile(r"\bghp_[a-zA-Z0-9]{36}\b")),
    ("GitHub OAuth / App Token", re.compile(r"\bgh[ousr]_[a-zA-Z0-9]{36}\b")),
    ("AWS Access Key ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack Token", re.compile(r"\bxox[baprs]-[0-9a-zA-Z\-]{10,}\b")),
    ("Private Key Header", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Database URL with Password", re.compile(r"[a-zA-Z0-9+]+://[^:\s]+:[^@\s]+@[^/\s]+/\w+")),
    ("Generic Bearer Token", re.compile(r"\bBearer\s+[a-zA-Z0-9\-_\.]{24,}\b", re.IGNORECASE)),
]


def mask_secrets(text: str) -> str:
    masked = text
    for name, pattern in SECRET_PATTERNS:
        def repl(match: re.Match) -> str:
            matched_val = match.group(0)
            if len(matched_val) <= 8:
                return "[REDACTED]"
            return matched_val[:4] + "..." + matched_val[-4:] + f"[{name}]"
        masked = pattern.sub(repl, masked)
    return masked


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    findings: list[tuple[int, str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return findings

    for i, line in enumerate(lines, 1):
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append((i, name, line.strip()))
    return findings


def scan_directory(target: Path) -> dict[Path, list[tuple[int, str, str]]]:
    all_findings: dict[Path, list[tuple[int, str, str]]] = {}
    if target.is_file():
        hits = scan_file(target)
        if hits:
            all_findings[target] = hits
        return all_findings

    for p in target.rglob("*"):
        if not p.is_file():
            continue
        if any(part in IGNORED_DIRS for part in p.parts):
            continue
        hits = scan_file(p)
        if hits:
            all_findings[p] = hits
    return all_findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan and mask credentials before AI prompt transmission.")
    parser.add_argument("target", nargs="?", default=".", help="Target file or directory")
    parser.add_argument("--mask", action="store_true", help="Print file content with secrets masked")
    parser.add_argument("--stdin", action="store_true", help="Read text from standard input and mask it")
    args = parser.parse_args()

    if args.stdin:
        input_text = sys.stdin.read()
        sys.stdout.write(mask_secrets(input_text))
        sys.exit(0)

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        sys.stderr.write(f"Error: Target path does not exist: {target_path}\n")
        sys.exit(1)

    if args.mask and target_path.is_file():
        content = target_path.read_text(encoding="utf-8", errors="replace")
        sys.stdout.write(mask_secrets(content))
        sys.exit(0)

    findings = scan_directory(target_path)
    total_leaks = sum(len(hits) for hits in findings.values())

    if not total_leaks:
        print("[OK] Clean. No exposed credentials detected.")
        sys.exit(0)

    print("=" * 68)
    print(f"  [!] SECURITY WARNING: {total_leaks} sensitive credential(s) detected!")
    print("=" * 68)
    for path, hits in findings.items():
        try:
            rel = str(path.relative_to(target_path))
        except ValueError:
            rel = str(path)
        print(f"\n{rel}:")
        for lineno, name, snippet in hits:
            masked = snippet[:15] + "..." + snippet[-10:] if len(snippet) > 30 else snippet
            print(f"  Line {lineno:<4} [{name}]: {masked}")
    print("=" * 68)
    sys.exit(1)


if __name__ == "__main__":
    main()

