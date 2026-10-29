#!/usr/bin/env python3
"""Synchronize AI rule files across Claude, Gemini, Cursor, Cline, and Codex."""
from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Add scripts directory to path to allow importing utils
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from utils import format_command_path
TEMPLATE_PATH = REPO_ROOT / "templates" / "INSTRUCTIONS_TEMPLATE.md"
ENGINEERING_PATH = REPO_ROOT / "templates" / "ENGINEERING_RULES.md"
PYTHON_RULES_PATH = REPO_ROOT / "templates" / "PYTHON_RULES.md"
LINTER_SCRIPT = REPO_ROOT / "scripts" / "claudemd_linter.py"
IS_WINDOWS = platform.system() == "Windows"


def get_user_home() -> Path:
    return Path(os.environ.get("USERPROFILE" if IS_WINDOWS else "HOME", Path.home()))


def get_rule_targets(ws: Path) -> dict[str, list[Path]]:
    home = get_user_home()
    return {
        "claude": [home / ".claude" / "CLAUDE.md", ws / "CLAUDE.md"],
        "antigravity": [
            home / ".gemini" / "config" / "AGENTS.md",
            home / ".gemini" / "antigravity" / "rules" / "josh_rules.md",
            ws / "AGENTS.md",
            ws / ".agent" / "rules" / "josh_rules.md",
            ws / ".agents" / "rules" / "josh_rules.md",
        ],
        "cursor": [
            home / ".cursor" / "rules" / "josh-rules.mdc",
            home / ".cursorrules",
            ws / ".cursor" / "rules" / "josh-rules.mdc",
            ws / ".cursorrules",
        ],
        "cline": [home / ".clinerules", ws / ".clinerules"],
        "codex": [home / ".codex" / "instructions.md", ws / "AGENTS.md"],
        "windsurf": [home / ".windsurfrules", ws / ".windsurfrules"],
        "copilot": [ws / ".github" / "copilot-instructions.md"],
        "aider": [home / ".aider.conventions.md", ws / ".aider.conventions.md"],
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
    return re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)


def expand_template_variables(content: str) -> str:
    linter_str = format_command_path(LINTER_SCRIPT)
    if shutil.which("uv"):
        linter_cmd = f"uv run --no-project python {linter_str}"
    else:
        py_bin = "python" if IS_WINDOWS else "python3"
        linter_cmd = f"{py_bin} {linter_str}"

    eng_path = format_command_path(ENGINEERING_PATH)
    py_rules_path = format_command_path(PYTHON_RULES_PATH)
    expanded = content.replace("{{LINTER_COMMAND}}", linter_cmd)
    expanded = expanded.replace("{{ENGINEERING_RULES_PATH}}", eng_path)
    expanded = expanded.replace("{{PYTHON_RULES_PATH}}", py_rules_path)
    return expanded.replace("<project_root>", ".")


def format_for_target(target: Path, expanded: str) -> str:
    if target.suffix == ".mdc":
        header = "---\ndescription: Josh AI Development and Linting Rules\nglobs: *\nalwaysApply: true\n---\n\n"
        return header + expanded
    return expanded


def sync_rules(source: Path | None, ws: Path, dry_run: bool) -> int:
    targets = get_rule_targets(ws)
    if source is not None:
        src_file = source
    elif TEMPLATE_PATH.is_file():
        src_file = TEMPLATE_PATH
    else:
        src_file = find_most_recent_source(targets)

    if src_file is None or not src_file.is_file():
        sys.stderr.write("No existing rule file found to synchronize from.\n")
        return 1

    raw_text = src_file.read_text(encoding="utf-8", errors="replace")
    core_rules = strip_frontmatter(raw_text)
    expanded_rules = expand_template_variables(core_rules)

    synced_count = 0
    seen_paths: set[Path] = set()
    for tool_name, paths in targets.items():
        for dest in paths:
            resolved_dest = dest.resolve()
            if resolved_dest in seen_paths or resolved_dest == src_file.resolve():
                continue
            seen_paths.add(resolved_dest)
            if not dest.parent.exists() and not dest.exists():
                continue
            new_text = format_for_target(dest, expanded_rules)
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
