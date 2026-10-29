#!/usr/bin/env python3
"""Configures AI developer tools (Claude, Cursor, Cline, Antigravity, Codex, etc.)
with Josh's unified style rules and automated AST linter instructions.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO_ROOT / "templates" / "INSTRUCTIONS_TEMPLATE.md"
ENGINEERING_PATH = REPO_ROOT / "templates" / "ENGINEERING_RULES.md"
PYTHON_RULES_PATH = REPO_ROOT / "templates" / "PYTHON_RULES.md"
LINTER_SCRIPT = REPO_ROOT / "scripts" / "claudemd_linter.py"

IS_WINDOWS = platform.system() == "Windows"


def get_user_home() -> Path:
    return Path(os.environ.get("USERPROFILE" if IS_WINDOWS else "HOME", Path.home()))


# Registry of supported AI tools and target paths
def get_tool_definitions(workspace: Path | None = None) -> dict[str, dict]:
    home = get_user_home()
    ws = workspace or Path.cwd()

    return {
        "claude": {
            "name": "Claude Code",
            "global_paths": [home / ".claude" / "CLAUDE.md"],
            "workspace_paths": [ws / "CLAUDE.md"],
            "frontmatter": "",
        },
        "cursor": {
            "name": "Cursor IDE",
            "global_paths": [
                home / ".cursor" / "rules" / "josh-rules.mdc",
                home / ".cursorrules",
            ],
            "workspace_paths": [
                ws / ".cursor" / "rules" / "josh-rules.mdc",
                ws / ".cursorrules",
            ],
            "frontmatter": "---\ndescription: Josh AI Development and Linting Rules\nglobs: *\nalwaysApply: true\n---\n\n",
        },
        "cline": {
            "name": "Cline & Roo Code",
            "global_paths": [home / ".clinerules"],
            "workspace_paths": [ws / ".clinerules"],
            "frontmatter": "",
        },
        "antigravity": {
            "name": "Google Antigravity (AGY)",
            "global_paths": [
                home / ".gemini" / "config" / "AGENTS.md",
                home / ".gemini" / "antigravity" / "rules" / "josh_rules.md",
            ],
            "workspace_paths": [
                ws / "AGENTS.md",
                ws / ".agent" / "rules" / "josh_rules.md",
                ws / ".agents" / "rules" / "josh_rules.md",
            ],
            "frontmatter": "",
        },
        "codex": {
            "name": "OpenAI Codex & ChatGPT",
            "global_paths": [home / ".codex" / "instructions.md"],
            "workspace_paths": [ws / "AGENTS.md"],
            "frontmatter": "",
        },
        "windsurf": {
            "name": "Windsurf IDE",
            "global_paths": [home / ".windsurfrules"],
            "workspace_paths": [ws / ".windsurfrules"],
            "frontmatter": "",
        },
        "copilot": {
            "name": "GitHub Copilot",
            "global_paths": [],
            "workspace_paths": [ws / ".github" / "copilot-instructions.md"],
            "frontmatter": "",
        },
        "aider": {
            "name": "Aider CLI",
            "global_paths": [home / ".aider.conventions.md"],
            "workspace_paths": [ws / ".aider.conventions.md"],
            "frontmatter": "",
        },
    }


def format_command_path(path: Path) -> str:
    path_str = str(path)
    if " " in path_str:
        return f'"{path_str}"'
    return path_str


def calc_linter_command() -> str:
    script_str = format_command_path(LINTER_SCRIPT)
    if shutil.which("uv"):
        return f"uv run --no-project python {script_str}"
    py_bin = "python" if IS_WINDOWS else "python3"
    return f"{py_bin} {script_str}"


def build_instructions(frontmatter: str = "") -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    linter_cmd = calc_linter_command()
    eng_path = format_command_path(ENGINEERING_PATH)
    py_rules_path = format_command_path(PYTHON_RULES_PATH)

    content = template.replace("{{LINTER_COMMAND}}", linter_cmd)
    content = content.replace("{{ENGINEERING_RULES_PATH}}", eng_path)
    content = content.replace("{{PYTHON_RULES_PATH}}", py_rules_path)
    if frontmatter:
        content = frontmatter + content
    return content


def install_file(dest: Path, content: str, default_action: str = "ask", dry_run: bool = False) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)

    action = default_action
    begin_marker = "<!-- BEGIN JOSH-AI-TOOLS -->"
    end_marker = "<!-- END JOSH-AI-TOOLS -->"
    bounded_content = f"{begin_marker}\n{content}\n{end_marker}"

    if dest.exists():
        if action == "ask":
            print(f"\n[!] File already exists: {dest}")
            print("    [O] Overwrite")
            print("    [A] Append to existing file")
            print("    [S] Skip")
            while True:
                choice = input("    Choose action [O/A/S]: ").strip().lower()
                if choice in ("o", "overwrite"):
                    action = "overwrite"
                    break
                if choice in ("a", "append"):
                    action = "append"
                    break
                if choice in ("s", "skip"):
                    action = "skip"
                    break
                print("    Invalid input. Please enter O, A, or S.")

        if action == "skip":
            print(f"[-] Skipped: {dest}")
            return
        if action == "append":
            if dry_run:
                print(f"[DRY-RUN] Would append bounded block to: {dest}")
                return
            existing = dest.read_text(encoding="utf-8")
            if begin_marker in existing and end_marker in existing:
                pattern = rf"{re.escape(begin_marker)}.*?{re.escape(end_marker)}"
                updated = re.sub(pattern, bounded_content, existing, flags=re.DOTALL)
            else:
                updated = existing.rstrip() + f"\n\n{bounded_content}\n"
            dest.write_text(updated, encoding="utf-8")
            print(f"[+] Appended instructions to: {dest}")
            return
        if action == "overwrite":
            if dry_run:
                print(f"[DRY-RUN] Would overwrite: {dest}")
                return
            dest.write_text(content, encoding="utf-8")
            print(f"[+] Overwrote: {dest}")
            return
    else:
        if dry_run:
            print(f"[DRY-RUN] Would create: {dest}")
            return
        dest.write_text(content, encoding="utf-8")
        print(f"[+] Created: {dest}")


def remove_tool_targets(selected_tools: list[str], scope: str, workspace: Path, dry_run: bool = False) -> None:
    tool_defs = get_tool_definitions(workspace)
    begin_marker = "<!-- BEGIN JOSH-AI-TOOLS -->"
    end_marker = "<!-- END JOSH-AI-TOOLS -->"

    for tool_key in selected_tools:
        if tool_key not in tool_defs:
            continue
        defn = tool_defs[tool_key]
        targets: list[Path] = []
        if scope in ("global", "both"):
            targets.extend(defn["global_paths"])
        if scope in ("workspace", "both"):
            targets.extend(defn["workspace_paths"])

        for target in targets:
            if not target.is_file():
                continue
            text = target.read_text(encoding="utf-8", errors="replace")
            if begin_marker in text and end_marker in text:
                pattern = rf"\n*{re.escape(begin_marker)}.*?{re.escape(end_marker)}\n*"
                cleaned = re.sub(pattern, "", text, flags=re.DOTALL)
                if dry_run:
                    print(f"[DRY-RUN] Would remove josh-ai-tools block from: {target}")
                else:
                    target.write_text(cleaned, encoding="utf-8")
                    print(f"[OK] Removed josh-ai-tools block from: {target}")
            elif "claudemd_linter" in text or "josh-ai-tools" in text:
                if dry_run:
                    print(f"[DRY-RUN] Would delete: {target}")
                else:
                    target.unlink()
                    print(f"[OK] Deleted: {target}")


def configure_tools(
    selected_tools: list[str],
    scope: str,
    workspace: Path,
    action: str,
    dry_run: bool = False,
) -> None:
    tool_defs = get_tool_definitions(workspace)

    for tool_key in selected_tools:
        if tool_key not in tool_defs:
            print(f"[!] Warning: Unknown tool '{tool_key}' ignored.")
            continue

        defn = tool_defs[tool_key]
        print(f"\n>>> Configuring {defn['name']}...")

        targets: list[Path] = []
        if scope in ("global", "both"):
            targets.extend(defn["global_paths"])
        if scope in ("workspace", "both"):
            targets.extend(defn["workspace_paths"])

        if not targets:
            if scope == "global" and not defn["global_paths"]:
                print(f"[-] Note: {defn['name']} is workspace-only (configure with --scope workspace).")
            else:
                print(f"[-] No target paths configured for {defn['name']} under scope '{scope}'.")
            continue

        for target in targets:
            frontmatter = defn["frontmatter"] if target.suffix == ".mdc" else ""
            content = build_instructions(frontmatter)
            install_file(target, content, default_action=action, dry_run=dry_run)


def configure_mcp_servers(
    repo_root: Path,
    scope: str = "global",
    workspace: Path | None = None,
    tools: list[str] | None = None,
    dry_run: bool = False,
    remove: bool = False,
) -> None:
    home = get_user_home()
    ws = workspace or Path.cwd()
    mcp_script = repo_root / "mcp" / "server.py"

    print("\n>>> Configuring Model Context Protocol (MCP) Servers...")

    uv_bin = shutil.which("uv")
    if uv_bin:
        resolved_uv = str(Path(uv_bin).resolve())
        base_entry: dict = {
            "command": resolved_uv,
            "args": ["run", "--no-project", "python", str(mcp_script)],
        }
    else:
        server_cmd = sys.executable or ("python" if IS_WINDOWS else "python3")
        base_entry = {
            "command": server_cmd,
            "args": [str(mcp_script)],
        }

    configs: list[tuple[str, Path, dict]] = []

    # 1. Claude Desktop & Claude Code
    if not tools or "claude" in tools:
        if IS_WINDOWS:
            claude_desktop = home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        elif platform.system() == "Darwin":
            claude_desktop = home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        else:
            claude_desktop = home / ".config" / "Claude" / "claude_desktop_config.json"

        if scope in ("global", "both"):
            configs.append(("Claude Desktop", claude_desktop, dict(base_entry)))
            configs.append(("Claude Code CLI (Global)", home / ".claude.json", dict(base_entry)))
        if scope in ("workspace", "both"):
            configs.append(("Claude Code CLI (Workspace)", ws / ".claude.json", dict(base_entry)))

    # 2. Cursor IDE
    if not tools or "cursor" in tools:
        if scope in ("global", "both"):
            configs.append(("Cursor IDE (Global)", home / ".cursor" / "mcp.json", dict(base_entry)))
        if scope in ("workspace", "both"):
            configs.append(("Cursor IDE (Workspace)", ws / ".cursor" / "mcp.json", dict(base_entry)))

    # 3. Cline & Roo Code
    if not tools or "cline" in tools:
        cline_entry = dict(base_entry)
        cline_entry.update({"disabled": False, "autoApprove": []})

        if IS_WINDOWS:
            code_storage = home / "AppData" / "Roaming" / "Code" / "User" / "globalStorage"
        elif platform.system() == "Darwin":
            code_storage = home / "Library" / "Application Support" / "Code" / "User" / "globalStorage"
        else:
            code_storage = home / ".config" / "Code" / "User" / "globalStorage"

        configs.append(
            (
                "Cline (VS Code)",
                code_storage / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
                cline_entry,
            )
        )
        configs.append(
            (
                "Roo Code (VS Code)",
                code_storage / "rooveterinaryinc.roo-cline" / "settings" / "cline_mcp_settings.json",
                cline_entry,
            )
        )

    # 4. Windsurf IDE
    if not tools or "windsurf" in tools:
        configs.append(
            (
                "Windsurf IDE",
                home / ".codeium" / "windsurf" / "mcp_config.json",
                dict(base_entry),
            )
        )

    # 5. Google Antigravity
    if not tools or "antigravity" in tools:
        if scope in ("global", "both"):
            configs.append(
                (
                    "Google Antigravity (Global Config)",
                    home / ".gemini" / "config" / "mcp_config.json",
                    dict(base_entry),
                )
            )
            configs.append(
                (
                    "Google Antigravity (App Storage)",
                    home / ".gemini" / "antigravity" / "mcp_config.json",
                    dict(base_entry),
                )
            )
        if scope in ("workspace", "both"):
            configs.append(
                (
                    "Google Antigravity (Workspace .agent)",
                    ws / ".agent" / "mcp_config.json",
                    dict(base_entry),
                )
            )
            configs.append(
                (
                    "Google Antigravity (Workspace .agents)",
                    ws / ".agents" / "mcp_config.json",
                    dict(base_entry),
                )
            )

    configured_count = 0
    for name, path, entry in configs:
        if remove:
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if "mcpServers" in data and "josh-ai-tools" in data["mcpServers"]:
                    del data["mcpServers"]["josh-ai-tools"]
                    if dry_run:
                        print(f"[DRY-RUN] Would remove MCP server entry from {name}: {path}")
                    else:
                        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                        print(f"[OK] Removed MCP server from {name}: {path}")
            except OSError:
                continue
            continue

        try:
            if dry_run:
                print(f"[DRY-RUN] Would configure MCP for {name} -> {path}")
                configured_count += 1
                continue

            path.parent.mkdir(parents=True, exist_ok=True)
            data: dict = {}
            if path.is_file():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except Exception as err:
                    print(f"[!] Warning: Could not parse {path} as valid JSON ({err}). Skipping to prevent corruption.")
                    continue
                try:
                    backup_path = path.with_suffix(path.suffix + ".bak")
                    backup_path.write_bytes(path.read_bytes())
                except OSError:
                    backup_path = None

            if "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
                data["mcpServers"] = {}

            data["mcpServers"]["josh-ai-tools"] = entry
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"[OK] Configured MCP server for {name} -> {path}")
            configured_count += 1
        except OSError as err:
            print(f"[!] Note: Could not configure MCP for {name} ({err})")

    if not remove:
        print(f"[+] Total MCP configs updated: {configured_count}")


def interactive_menu() -> tuple[list[str], str, Path, bool]:
    print("Josh AI Tools Configurator")
    print(f"Repo directory: {REPO_ROOT}")
    print(f"Linter script:  {LINTER_SCRIPT}")
    print("")

    tool_defs = get_tool_definitions()
    keys = list(tool_defs.keys())

    print("Supported AI Tools:")
    print("  0) [ALL] Configure all supported AI tools")
    for idx, key in enumerate(keys, 1):
        print(f"  {idx}) {tool_defs[key]['name']} ({key})")
    print("")

    selection = input(f"Select tools to configure [0-{len(keys)} or comma-separated, default 0]: ").strip()
    if not selection or selection == "0":
        selected = keys
    else:
        selected = []
        for part in selection.split(","):
            part_str = part.strip()
            if part_str.isdigit():
                num_idx = int(part_str) - 1
                if 0 <= num_idx < len(keys):
                    selected.append(keys[num_idx])
            elif part_str in tool_defs:
                selected.append(part_str)
        if not selected:
            selected = keys

    print(f"\nSelected tools: {', '.join(selected)}")
    print("\nConfiguration Scope:")
    print("  1) Global (user profile directories)")
    print("  2) Workspace (current or specified project directory)")
    print("  3) Both (global defaults + local workspace files)")
    scope_choice = input("Select scope [1-3, default 1]: ").strip()
    scope_map = {"1": "global", "2": "workspace", "3": "both"}
    scope = scope_map.get(scope_choice, "global")

    workspace = Path.cwd()
    if scope in ("workspace", "both"):
        ws_in = input(f"Target workspace folder [default: {workspace}]: ").strip()
        if ws_in:
            workspace = Path(ws_in).resolve()

    setup_mcp_in = input("\nAutomatically configure MCP servers for selected tools? [Y/n]: ").strip().lower()
    setup_mcp = setup_mcp_in not in ("n", "no")

    return selected, scope, workspace, setup_mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="Configure Josh's AI development tools across platforms.")
    parser.add_argument(
        "--tools",
        help="Comma-separated list of tools (claude, cursor, cline, antigravity, codex, windsurf, copilot, aider, all)",
    )
    parser.add_argument(
        "--scope",
        choices=["global", "workspace", "both"],
        default="global",
        help="Installation scope: global user profile, workspace project, or both.",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Path to workspace root (used when scope is workspace or both).",
    )
    parser.add_argument(
        "--action",
        choices=["ask", "overwrite", "append", "skip"],
        default="ask",
        help="Action when a destination file already exists.",
    )
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help="Skip automatic configuration of Model Context Protocol (MCP) servers.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without modifying files.",
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove configured rules and MCP servers for selected tools.",
    )
    args = parser.parse_args()

    tool_defs = get_tool_definitions(args.workspace)

    if not args.tools and len(sys.argv) == 1:
        selected, scope, workspace, setup_mcp = interactive_menu()
        configure_tools(selected, scope, workspace, args.action, dry_run=args.dry_run)
        if setup_mcp:
            configure_mcp_servers(REPO_ROOT, scope, workspace, selected, dry_run=args.dry_run)
    else:
        tools_arg = args.tools or "all"
        if tools_arg.strip().lower() == "all":
            selected = list(tool_defs.keys())
        else:
            selected = [t.strip().lower() for t in tools_arg.split(",") if t.strip()]

        if args.remove:
            remove_tool_targets(selected, args.scope, args.workspace, dry_run=args.dry_run)
            configure_mcp_servers(REPO_ROOT, args.scope, args.workspace, selected, dry_run=args.dry_run, remove=True)
            return

        configure_tools(selected, args.scope, args.workspace, args.action, dry_run=args.dry_run)
        if not args.no_mcp:
            configure_mcp_servers(REPO_ROOT, args.scope, args.workspace, selected, dry_run=args.dry_run)

    print("Configuration finished! All AI tools reference:")
    print(f"  Linter: {LINTER_SCRIPT}")
    print(f"  Rules:  {ENGINEERING_PATH}")


if __name__ == "__main__":
    main()
