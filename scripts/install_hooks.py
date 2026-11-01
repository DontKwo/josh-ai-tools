#!/usr/bin/env python3
"""Installs or uninstalls Git pre-commit enforcement hooks.
Ensures claudemd_linter.py is executed automatically on staged files before commit.
"""

import argparse
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import IS_WINDOWS

REPO_ROOT = Path(__file__).resolve().parent.parent
LINTER_SCRIPT = REPO_ROOT / "scripts" / "claudemd_linter.py"

PYTHON_CMD = "python" if IS_WINDOWS else "python3"


def create_hook_content() -> str:
    # Git hooks run in POSIX sh shell environment
    linter_posix = str(LINTER_SCRIPT).replace("\\", "/")
    return f"""#!/usr/bin/env sh
# Pre-commit hook installed by josh-ai-tools
# Runs claudemd_linter on staged files before allowing commit

echo "Running claudemd_linter on staged files..."
if command -v uv >/dev/null 2>&1; then
    uv run --no-project python "{linter_posix}" --staged
else
    {PYTHON_CMD} "{linter_posix}" --staged
fi

if [ $? -ne 0 ]; then
    echo ""
    echo "[!] COMMIT REJECTED: claudemd_linter found rule violations."
    echo "    Fix all violations listed above before committing."
    echo "    To bypass only if truly necessary: git commit --no-verify"
    exit 1
fi

exit 0
"""


def install_hook(target_repo: Path, action: str = "ask") -> None:
    git_dir = target_repo / ".git"
    if not git_dir.is_dir():
        print(f"[!] Error: {target_repo} is not a git repository (.git folder not found).")
        return

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_file = hooks_dir / "pre-commit"

    content = create_hook_content()

    if hook_file.exists():
        if action == "ask":
            print(f"\n[?] Existing pre-commit hook found at: {hook_file}")
            print("    [O] Overwrite")
            print("    [A] Append to existing hook")
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

        if action == "skip":
            print(f"[-] Skipped: {hook_file}")
            return
        if action == "append":
            with open(hook_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n# --- Appended by josh-ai-tools ---\n{content}\n")
            print(f"[+] Appended linter hook to: {hook_file}")
        elif action == "overwrite":
            hook_file.write_text(content, encoding="utf-8")
            print(f"[+] Overwrote pre-commit hook at: {hook_file}")
    else:
        hook_file.write_text(content, encoding="utf-8")
        print(f"[+] Created pre-commit hook at: {hook_file}")

    # Ensure executable permissions on POSIX systems
    try:
        hook_file.chmod(hook_file.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        return


def uninstall_hook(target_repo: Path) -> None:
    hook_file = target_repo / ".git" / "hooks" / "pre-commit"
    if hook_file.exists():
        hook_file.unlink()
        print(f"[+] Removed pre-commit hook from {hook_file}")
    else:
        print(f"[-] No pre-commit hook found in {target_repo}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Install claudemd_linter git pre-commit hook.")
    parser.add_argument("target", nargs="?", default=".", help="Target git repository path (default: current directory)")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall pre-commit hook")
    parser.add_argument("--action", choices=["ask", "overwrite", "append", "skip"], default="ask")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if args.uninstall:
        uninstall_hook(target)
    else:
        install_hook(target, action=args.action)


if __name__ == "__main__":
    main()
