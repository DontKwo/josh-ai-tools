#!/usr/bin/env python3
"""Synchronize AI rule files across Claude, Gemini, Cursor, Cline, and Codex."""
import argparse
import os
import platform
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
IS_WINDOWS = platform.system() == "Windows"


def get_user_home() -> Path:
    return Path(os.environ.get("USERPROFILE" if IS_WINDOWS else "HOME", Path.home()))


def get_rule_targets(ws: Path) -> dict[str, list[Path]]:
    home = get_user_home()
    return {
        "claude": [home / ".claude" / "CLAUDE.md", ws / "CLAUDE.md"],
        "gemini": [
            home / ".gemini" / "config" / "AGENTS.md",
            home / "GEMINI.md",
            ws / "GEMINI.md",
            ws / "AGENTS.md",
            ws / ".agents" / "rules" / "josh_rules.md",
        ],
        "cursor": [
            home / ".cursorrules",
            ws / ".cursorrules",
            ws / ".cursor" / "rules" / "josh-rules.mdc",
        ],
        "cline": [home / ".clinerules", ws / ".clinerules"],
        "codex": [home / ".codex" / "instructions.md", ws / "OPENAI.md"],
    }


def find_most_recent_source(targets: dict[str, list[Path]]) -> Path | None:
    best_file: Path | None = None
    best_mtime: float = -1.0
    for file_list in targets.values():
        for path in file_list:
            if path.is_file():
                mtime = path.stat().st_mtime
                if mtime > best_mtime:
                    best_mtime = mtime
                    best_file = path
    return best_file


def strip_frontmatter(content: str) -> str:
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].lstrip()
    return content


def format_for_target(target: Path, core_content: str) -> str:
    if target.suffix == ".mdc" or target.name == ".cursorrules":
        header = "---\ndescription: Josh AI Development and Linting Rules\nglobs: *\nalwaysApply: true\n---\n\n"
        return header + core_content
    return core_content


def sync_rules(source: Path | None, ws: Path, dry_run: bool) -> int:
    targets = get_rule_targets(ws)
    src_file = source or find_most_recent_source(targets)
    if src_file is None or not src_file.is_file():
        sys.stderr.write("No existing rule file found to synchronize from.\n")
        return 1

    raw_text = src_file.read_text(encoding="utf-8", errors="replace")
    core_rules = strip_frontmatter(raw_text)

    synced_count = 0
    for tool_name, paths in targets.items():
        for dest in paths:
            if dest.resolve() == src_file.resolve():
                continue
            if not dest.parent.exists() and not dest.exists():
                continue
            new_text = format_for_target(dest, core_rules)
            if dest.is_file() and dest.read_text(encoding="utf-8", errors="replace") == new_text:
                continue
            if dry_run:
                print(f"[DRY-RUN] Would update: {dest}")
                synced_count += 1
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(new_text, encoding="utf-8")
                print(f"[OK] Synced {tool_name} rule: {dest}")
                synced_count += 1

    print(f"Synchronization complete. Updated {synced_count} file(s) from {src_file}.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize rule files across all AI tools.")
    parser.add_argument("--source", type=Path, default=None, help="Specific source file to copy from")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Target workspace path")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync actions without writing")
    args = parser.parse_args()

    sys.exit(sync_rules(args.source, args.workspace, args.dry_run))


if __name__ == "__main__":
    main()

