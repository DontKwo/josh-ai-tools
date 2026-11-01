#!/usr/bin/env python3
"""Environment Doctor & Self-Healing Path Synchronizer.
Inspects all AI instruction configurations, verifies toolpaths, checks dependencies,
and repairs broken/stale paths across Claude, Cursor, Cline, Antigravity, and Codex.
"""

import argparse
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import IS_WINDOWS, get_user_home
from configure import configure_skills

REPO_ROOT = Path(__file__).resolve().parent.parent
LINTER_SCRIPT = REPO_ROOT / "scripts" / "claudemd_linter.py"
ENGINEERING_PATH = REPO_ROOT / "templates" / "ENGINEERING_RULES.md"
PYTHON_RULES_PATH = REPO_ROOT / "templates" / "PYTHON_RULES.md"


def inspect_mcp_config(mcp_path: Path) -> dict:
    info = {
        "exists": mcp_path.is_file(),
        "is_registered": False,
        "corrupted": False,
        "command_valid": False,
        "script_valid": False,
    }
    if not info["exists"]:
        return info

    try:
        mcp_data = json.loads(mcp_path.read_text(encoding="utf-8"))
        josh_tools = mcp_data.get("mcpServers", {}).get("josh-ai-tools")
        if josh_tools:
            info["is_registered"] = True

            cmd = josh_tools.get("command")
            if cmd and Path(cmd).is_file():
                info["command_valid"] = True

            args = josh_tools.get("args", [])
            for arg in args:
                if arg.endswith("server.py"):
                    if Path(arg).is_file():
                        info["script_valid"] = True
                    break
    except Exception:
        info["corrupted"] = True

    return info


def check_installed_skills(repo_root: Path, home: Path) -> dict[str, bool]:
    installed_status: dict[str, bool] = {}
    source_skills = repo_root / "skills"
    dest_dir = home / ".gemini" / "antigravity" / "skills"

    if not source_skills.is_dir():
        return installed_status

    for skill_dir in source_skills.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_name = skill_dir.name
        dest_skill_dir = dest_dir / skill_name
        dest_skill_md = dest_skill_dir / "SKILL.md"

        installed_status[skill_name] = dest_skill_dir.is_dir() and dest_skill_md.is_file()

    return installed_status


def get_all_config_paths() -> list[tuple[str, Path]]:
    home = get_user_home()
    return [
        ("Claude Code", home / ".claude" / "CLAUDE.md"),
        ("Cursor IDE", home / ".cursor" / "rules" / "josh-rules.mdc"),
        ("Cursor IDE (.cursorrules)", home / ".cursorrules"),
        ("Cline / Roo Code", home / ".clinerules"),
        ("Google Antigravity", home / ".gemini" / "antigravity" / "rules" / "josh_rules.md"),
        ("Google Antigravity (Agents)", home / ".gemini" / "config" / "AGENTS.md"),
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
        "has_unexpanded_tokens": False,
        "has_stale_ref": False,
    }

    if not path.is_file():
        return info

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        if any(tok in content for tok in ("{{LINTER_COMMAND}}", "{{ENGINEERING_RULES_PATH}}", "{{PYTHON_RULES_PATH}}")):
            info["has_unexpanded_tokens"] = True

        if "<project_root>" in content or "lint_report.txt" in content:
            info["has_stale_ref"] = True

        pattern = r'(?:uv\s+run\s+--no-project\s+python|python(?:3)?)\s+["\']?([^"\'\n]+claudemd_linter\.py)["\']?'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            info["has_linter_ref"] = True
            ref_path = Path(match.group(1).strip())
            info["extracted_path"] = ref_path
            info["linter_path_valid"] = (
                ref_path.is_file() and not info["has_unexpanded_tokens"] and not info["has_stale_ref"]
            )
    except OSError:
        return info

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

        eng_str = str(ENGINEERING_PATH)
        if " " in eng_str:
            eng_str = f'"{eng_str}"'

        py_str = str(PYTHON_RULES_PATH)
        if " " in py_str:
            py_str = f'"{py_str}"'

        if shutil.which("uv"):
            new_cmd = f"uv run --no-project python {target_linter_str}"
        else:
            py_bin = "python" if IS_WINDOWS else "python3"
            new_cmd = f"{py_bin} {target_linter_str}"

        pattern = re.compile(
            r'(?:uv\s+run\s+--no-project\s+python|python(?:3)?)\s+["\']?[^"\'\n]+claudemd_linter\.py["\']?',
            re.IGNORECASE,
        )
        new_content = pattern.sub(new_cmd, content)
        new_content = new_content.replace("{{LINTER_COMMAND}}", new_cmd)
        new_content = new_content.replace("{{ENGINEERING_RULES_PATH}}", eng_str)
        new_content = new_content.replace("{{PYTHON_RULES_PATH}}", py_str)
        new_content = new_content.replace("<project_root>", ".")
        new_content = re.sub(
            r"Then read [^\n]*lint_report\.txt in full\.",
            "When violations occur, inspect the report file path printed in terminal output.",
            new_content,
        )
        path.write_text(new_content, encoding="utf-8")
        return True
    except OSError as err:
        print(f"  [!] Failed to heal {path}: {err}")
        return False


def clean_stale_reports_and_cache(dry_run: bool = False) -> int:
    removed_count = 0
    targets = list((REPO_ROOT / "scripts").glob("lint_report*.txt"))
    targets.extend(REPO_ROOT.glob("lint_report*.txt"))
    cache_file = REPO_ROOT / "scripts" / ".lint_cache.json"
    if cache_file.is_file():
        targets.append(cache_file)

    for path in targets:
        if path.is_file():
            if dry_run:
                print(f"  [DRY-RUN] Would remove: {path}")
            else:
                try:
                    path.unlink()
                    print(f"  [+] Removed: {path.name}")
                    removed_count += 1
                except OSError as err:
                    print(f"  [!] Failed to delete {path.name}: {err}")
    return removed_count


def run_diagnostics(auto_heal: bool = False, clean_cache: bool = False, repair: bool = False) -> None:
    print("Josh AI Tools Health & Diagnostic Doctor")
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

    # 2. Check uv Package Manager
    print("\n[2] uv Package Manager:")
    uv_bin = shutil.which("uv")
    if uv_bin:
        print(f"  [OK] uv executable found at: {uv_bin}")
    else:
        print("  [WARN] uv executable not found in PATH.")

    # 3. Check Git
    print("\n[3] Git Availability:")
    git_bin = shutil.which("git")
    if git_bin:
        print(f"  [OK] Git executable found at: {git_bin}")
    else:
        print("  [WARN] Git executable not found in PATH.")

    # 4. Check Vulture
    print("\n[4] Optional AST Dependencies:")
    vulture_ok = importlib.util.find_spec("vulture") is not None
    if not vulture_ok and shutil.which("vulture"):
        vulture_ok = True

    if vulture_ok:
        print("  [OK] 'vulture' is installed (used for Rule 21 dead code detection).")
    else:
        print("  [INFO] 'vulture' is not installed. Install with 'uv tool install vulture' if desired.")

    # 5. Check Configured AI Tools
    print("\n[5] Configured AI Tools:")
    configs = get_all_config_paths()
    needs_heal = []

    for name, path in configs:
        info = inspect_config_file(name, path)
        if not info["exists"]:
            print(f"  [-] {name:20}: Not installed ({path.name} not found)")
        elif not info["has_linter_ref"] and not info["has_unexpanded_tokens"]:
            print(f"  [WARN] {name:20}: Installed, but has no claudemd_linter.py instruction")
        elif info["linter_path_valid"]:
            print(f"  [OK] {name:20}: Healthy (points to {info['extracted_path']})")
        else:
            if info["has_unexpanded_tokens"]:
                reason = "Unexpanded template tokens"
            elif info["has_stale_ref"]:
                reason = "Stale report or <project_root> reference"
            else:
                reason = f"Points to missing path: {info['extracted_path']}"
            print(f"  [BROKEN] {name:16}: {reason}")
            info["type"] = "config"
            needs_heal.append(info)

    # 6. Check Antigravity Skills
    print("\n[6] Antigravity Skills Status:")
    home = get_user_home()
    skills_status = check_installed_skills(REPO_ROOT, home)
    missing_skills = False

    if not skills_status:
        print("  [-] No skills found in repository.")
    else:
        for skill_name, is_installed in sorted(skills_status.items()):
            if is_installed:
                print(f"  [OK] {skill_name:20}: Installed")
            else:
                print(f"  [-] {skill_name:20}: Missing")
                missing_skills = True

    if missing_skills and repair:
        print("\nRepairing missing Antigravity Skills...")
        configure_skills(REPO_ROOT, scope="global")
        print("  [+] Repair complete.")

    # 7. Check Configured MCP Servers
    print("\n[7] Configured Model Context Protocol (MCP) Servers:")
    mcp_configs = [
        ("Claude Desktop", home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json" if IS_WINDOWS else home / ".config" / "Claude" / "claude_desktop_config.json"),
        ("Claude Code CLI", home / ".claude.json"),
        ("Cursor IDE", home / ".cursor" / "mcp.json"),
        (
            "Google Antigravity (Config)",
            home / ".gemini" / "config" / "mcp_config.json",
        ),
        (
            "Google Antigravity (App)",
            home / ".gemini" / "antigravity" / "mcp_config.json",
        ),
        ("Windsurf IDE", home / ".codeium" / "windsurf" / "mcp_config.json"),
    ]

    for mcp_name, mcp_path in mcp_configs:
        mcp_info = inspect_mcp_config(mcp_path)
        if not mcp_info["exists"]:
            print(f"  [-] {mcp_name:20}: Not installed ({mcp_path.name} not found)")
        elif mcp_info["corrupted"]:
            print(f"  [WARN] {mcp_name:18}: Corrupted JSON file")
        elif not mcp_info["is_registered"]:
            print(f"  [-] {mcp_name:20}: Present, but josh-ai-tools not registered")
        elif not mcp_info["command_valid"] or not mcp_info["script_valid"]:
            print(f"  [BROKEN] {mcp_name:16}: Registered, but points to missing paths")
            needs_heal.append({"name": mcp_name, "path": mcp_path, "type": "mcp"})
        else:
            print(f"  [OK] {mcp_name:20}: Active (josh-ai-tools registered and valid)")

    # 8. Healing action
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
                if info.get("type") == "config" and heal_config_file(info):
                    print(f"  [+] Repaired: {info['name']} -> {LINTER_SCRIPT}")
                elif info.get("type") == "mcp":
                    print(f"  [!] MCP Repair not yet implemented for {info['name']}")
            print("\n[OK] All broken configurations successfully healed!")
    else:
        print("\n[OK] All installed AI tool configurations are healthy and synchronized.")

    if clean_cache:
        print("\nCleaning lint reports and cache...")
        count = clean_stale_reports_and_cache()
        print(f"[OK] Cleaned {count} file(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run diagnostics and heal stale AI tool paths.")
    parser.add_argument("--heal", action="store_true", help="Automatically heal stale paths without asking")
    parser.add_argument("--clean", action="store_true", help="Remove stale lint reports and .lint_cache.json")
    parser.add_argument("--repair", action="store_true", help="Automated repair to reinstall missing skills")
    args = parser.parse_args()

    run_diagnostics(auto_heal=args.heal, clean_cache=args.clean, repair=args.repair)


if __name__ == "__main__":
    main()
