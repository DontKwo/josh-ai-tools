#!/usr/bin/env python3
"""Installer for Antigravity lifecycle hooks that triggers linters on task completion."""
import argparse
import json
import os
import platform
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LINTER_SCRIPT = REPO_ROOT / "scripts" / "claudemd_linter.py"
IS_WINDOWS = platform.system() == "Windows"
PYTHON_CMD = "python" if IS_WINDOWS else "python3"


def get_user_home() -> Path:
    return Path(os.environ.get("USERPROFILE" if IS_WINDOWS else "HOME", Path.home()))


def get_hook_paths(workspace: Path) -> dict[str, Path]:
    home = get_user_home()
    return {
        "workspace": workspace / ".agents" / "hooks.json",
        "global": home / ".gemini" / "config" / "hooks.json",
    }


def build_hook_config(command_str: str, event: str = "PostInvocation") -> dict:
    return {
        "josh-linter-completion-guard": {
            event: [
                {
                    "type": "command",
                    "command": command_str,
                    "timeout": 60,
                }
            ]
        }
    }


def install_hook(dest: Path, command_str: str, event: str = "PostInvocation") -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    existing_data: dict = {}
    if dest.is_file():
        try:
            existing_data = json.loads(dest.read_text(encoding="utf-8"))
        except Exception:
            existing_data = {}

    hook_entry = build_hook_config(command_str, event)
    existing_data.update(hook_entry)

    dest.write_text(json.dumps(existing_data, indent=2), encoding="utf-8")
    return True


def remove_hook(dest: Path) -> bool:
    if not dest.is_file():
        return False
    try:
        data = json.loads(dest.read_text(encoding="utf-8"))
        if "josh-linter-completion-guard" in data:
            del data["josh-linter-completion-guard"]
            dest.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return True
    except Exception:
        pass
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Configure Antigravity completion hooks (triggers linter when done)."
    )
    parser.add_argument(
        "--scope",
        choices=["workspace", "global", "both"],
        default="workspace",
        help="Installation target scope",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Target workspace root",
    )
    parser.add_argument(
        "--event",
        choices=["PostInvocation", "Stop"],
        default="PostInvocation",
        help="Lifecycle event (fires only when done, not on every tool call)",
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Uninstall the completion hook",
    )
    args = parser.parse_args()

    paths = get_hook_paths(args.workspace.resolve())
    targets: list[tuple[str, Path]] = []
    if args.scope in ("workspace", "both"):
        targets.append(("Workspace", paths["workspace"]))
    if args.scope in ("global", "both"):
        targets.append(("Global", paths["global"]))

    linter_path = str(LINTER_SCRIPT)
    if " " in linter_path:
        linter_path = f'"{linter_path}"'
    cmd = f"{PYTHON_CMD} {linter_path} . --diff"

    for scope_name, path in targets:
        if args.remove:
            if remove_hook(path):
                print(f"[OK] Removed completion hook from {scope_name}: {path}")
            else:
                print(f"[-] Hook was not present in {scope_name}: {path}")
        else:
            install_hook(path, cmd, args.event)
            print(f"[OK] Installed completion hook in {scope_name}: {path}")
            print(f"     Event: {args.event} (triggers when task finishes)")
            print(f"     Command: {cmd}")


if __name__ == "__main__":
    main()

