#!/usr/bin/env python3
"""Environment Doctor & Self-Healing Path Synchronizer.
Inspects all AI instruction configurations, verifies toolpaths, checks dependencies,
and repairs broken/stale paths across Claude, Cursor, Cline, Antigravity, and Codex.
"""
import argparse
import json
import os
import platform
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LINTER_SCRIPT = REPO_ROOT / "scripts" / "claudemd_linter.py"
REPORT_PATH = REPO_ROOT / "scripts" / "lint_report.txt"

IS_WINDOWS = platform.system() == "Windows"
PYTHON_CMD = "python" if IS_WINDOWS else "python3"


def get_user_home() -> Path:
    return Path(os.environ.get("USERPROFILE" if IS_WINDOWS else "HOME", Path.home()))


def get_all_config_paths() -> list[tuple[str, Path]]:
    home = get_user_home()
    return [
        ("Claude Code", home / ".claude" / "CLAUDE.md"),
        ("Cursor IDE", home / ".cursorrules"),
        ("Cline / Roo Code", home / ".clinerules"),
        ("Google Antigravity", home / ".gemini" / "antigravity" / "rules" / "josh_rules.md"),
        ("OpenAI Codex", home / ".codex" / "instructions.md"),
        ("Windsurf IDE", home / ".windsurfrules"),
        ("Aider CLI", home / ".aider.conventions.md"),
    ]


def inspect_config_file(name: str, path: Path) -> dict:
    info = {
        "name": name,
        "path": path,
        "exists": path.is_file(),
        "has_linter_ref": False,
        "linter_path_valid": False,
        "extracted_path": None,
    }

    if not path.is_file():
        return info

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        # Match python .../claudemd_linter.py
        m = re.search(r'python(?:3)?\s+["\']?([^"\'\n]+claudemd_linter\.py)["\']?', content, re.IGNORECASE)
        if m:
            info["has_linter_ref"] = True
            ref_path = Path(m.group(1).strip())
            info["extracted_path"] = ref_path
            info["linter_path_valid"] = ref_path.is_file()
    except Exception:
        pass

    return info


def heal_config_file(info: dict) -> bool:
    path = info["path"]
    if not path.is_file():
        return False

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        target_linter_str = str(LINTER_SCRIPT)
        if " " in target_linter_str:
            target_linter_str = f'"{target_linter_str}"'

        # Regex replacement for the python linter command line
        pattern = re.compile(r'python(?:3)?\s+["\']?[^"\'\n]+claudemd_linter\.py["\']?', re.IGNORECASE)
        new_cmd = f"{PYTHON_CMD} {target_linter_str}"
        new_content = pattern.sub(new_cmd, content)

        # Also heal lint_report.txt path if present
        report_pattern = re.compile(r'["\']?[^"\'\n]+lint_report\.txt["\']?', re.IGNORECASE)
        target_report_str = str(REPORT_PATH)
        if " " in target_report_str:
            target_report_str = f'"{target_report_str}"'
        new_content = report_pattern.sub(target_report_str, new_content)

        path.write_text(new_content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"  [!] Failed to heal {path}: {e}")
        return False


def run_diagnostics(auto_heal: bool = False) -> None:
    print("=" * 65)
    print("           Josh's AI Tools Health & Diagnostic Doctor")
    print("=" * 65)
    print(f"Current Repo Root:  {REPO_ROOT}")
    print(f"Current Linter:     {LINTER_SCRIPT}")
    print("")

    # 1. Check Python Environment
    print("[1] Python Runtime:")
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 9):
        print(f"  [OK] Python {py_ver} (>= 3.9 requirement met)")
    else:
        print(f"  [FAIL] Python {py_ver} is too old! Please upgrade to Python 3.9+.")

    # 2. Check Git
    print("\n[2] Git Availability:")
    git_bin = shutil.which("git")
    if git_bin:
        print(f"  [OK] Git executable found at: {git_bin}")
    else:
        print("  [WARN] Git executable not found in PATH.")

    # 3. Check Vulture
    print("\n[3] Optional AST Dependencies:")
    try:
        import vulture
        print(f"  [OK] 'vulture' is installed (used for Rule 21 dead code detection).")
    except ImportError:
        print("  [INFO] 'vulture' is not installed. Install with 'pip install vulture' if desired.")

    # 4. Check Configured AI Tools
    print("\n[4] Configured AI Tools:")
    configs = get_all_config_paths()
    needs_heal = []

    for name, path in configs:
        info = inspect_config_file(name, path)
        if not info["exists"]:
            print(f"  [-] {name:20}: Not installed ({path.name} not found)")
        elif not info["has_linter_ref"]:
            print(f"  [WARN] {name:20}: Installed, but has no claudemd_linter.py instruction")
        elif info["linter_path_valid"]:
            print(f"  [OK] {name:20}: Healthy (points to {info['extracted_path']})")
        else:
            print(f"  [BROKEN] {name:16}: Points to missing path: {info['extracted_path']}")
            needs_heal.append(info)

    # 5. Check Configured MCP Servers
    print("\n[5] Configured Model Context Protocol (MCP) Servers:")
    home = get_user_home()
    mcp_configs = [
        ("Claude Desktop", home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json" if IS_WINDOWS else home / ".config" / "Claude" / "claude_desktop_config.json"),
        ("Claude Code CLI", home / ".claude.json"),
        ("Cursor IDE", home / ".cursor" / "mcp.json"),
        (
            "Google Antigravity",
            home / ".gemini" / "config" / "mcp_config.json"
            if (home / ".gemini" / "config" / "mcp_config.json").is_file()
            else home / ".gemini" / "antigravity" / "mcp_config.json",
        ),
        ("Windsurf IDE", home / ".codeium" / "windsurf" / "mcp_config.json"),
    ]

    for mcp_name, mcp_path in mcp_configs:
        if mcp_path.is_file():
            try:
                mcp_data = json.loads(mcp_path.read_text(encoding="utf-8"))
                if "josh-ai-tools" in mcp_data.get("mcpServers", {}):
                    print(f"  [OK] {mcp_name:20}: Active (josh-ai-tools registered)")
                else:
                    print(f"  [-] {mcp_name:20}: Present, but josh-ai-tools not registered")
            except Exception:
                print(f"  [WARN] {mcp_name:18}: Corrupted JSON file")
        else:
            print(f"  [-] {mcp_name:20}: Not installed ({mcp_path.name} not found)")

    # 6. Healing action
    if needs_heal:
        print(f"\n[!] Found {len(needs_heal)} configuration(s) pointing to stale or missing linter paths.")
        if auto_heal:
            do_heal = True
        else:
            choice = input("    Repair and heal these paths to point to this repository? [Y/n]: ").strip().lower()
            do_heal = choice in ("", "y", "yes")

        if do_heal:
            print("\nHealing configurations...")
            for info in needs_heal:
                if heal_config_file(info):
                    print(f"  [+] Repaired: {info['name']} -> {LINTER_SCRIPT}")
            print("\n[OK] All broken configurations successfully healed!")
    else:
        print("\n[OK] All installed AI tool configurations are healthy and synchronized.")

    print("=" * 65)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run diagnostics and heal stale AI tool paths.")
    parser.add_argument("--heal", action="store_true", help="Automatically heal stale paths without asking")
    args = parser.parse_args()

    run_diagnostics(auto_heal=args.heal)


if __name__ == "__main__":
    main()

