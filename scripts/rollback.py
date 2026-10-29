#!/usr/bin/env python3
"""Snapshot Checkpoint & Rollback Manager for AI Refactoring.
Takes instant lightweight snapshots of workspace files before letting AI tools edit code,
enabling one-key rollback and diff previews if an AI hallucinates or breaks tests.
"""
import argparse
import datetime
import json
import shutil
import sys
from pathlib import Path

CHECKPOINT_DIR = Path(".ai_checkpoints")

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except OSError:
        sys.stdout = sys.stdout


def get_checkpoint_dir(workspace: Path) -> Path:
    return workspace / ".ai_checkpoints"


def list_checkpoints(ws: Path) -> list[dict]:
    cp_dir = get_checkpoint_dir(ws)
    if not cp_dir.exists():
        return []

    checkpoints: list[dict] = []
    for f in sorted(cp_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            checkpoints.append(data)
        except Exception:
            continue
    return checkpoints


def save_checkpoint(ws: Path, name: str | None = None) -> str:
    cp_dir = get_checkpoint_dir(ws)
    cp_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = (name or f"snapshot_{timestamp}").replace(" ", "_")

    # Collect tracked/modified files
    # Scans files in workspace (ignoring .git, caches, venv)
    ignore_dirs = {".git", ".venv", "venv", "__pycache__", ".ai_checkpoints", "node_modules", "dist", "build"}

    captured_files: dict[str, str] = {}
    for p in ws.rglob("*"):
        if not p.is_file():
            continue
        if any(part in ignore_dirs for part in p.parts):
            continue
        try:
            rel = str(p.relative_to(ws))
            # Read text
            captured_files[rel] = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

    checkpoint_data = {
        "name": clean_name,
        "timestamp": datetime.datetime.now().isoformat(),
        "total_files": len(captured_files),
        "files": captured_files,
    }

    target_file = cp_dir / f"{clean_name}.json"
    target_file.write_text(json.dumps(checkpoint_data, indent=2), encoding="utf-8")
    return clean_name


def restore_checkpoint(ws: Path, name: str | None = None) -> bool:
    cp_dir = get_checkpoint_dir(ws)
    if not cp_dir.exists():
        print(f"Error: No checkpoints found in {cp_dir}", file=sys.stderr)
        return False

    if name:
        target_file = cp_dir / f"{name}.json"
    else:
        # Use most recent
        all_cps = sorted(cp_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not all_cps:
            print("Error: No checkpoints found to restore.", file=sys.stderr)
            return False
        target_file = all_cps[0]

    if not target_file.is_file():
        print(f"Error: Checkpoint '{name}' does not exist.", file=sys.stderr)
        return False

    try:
        data = json.loads(target_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error reading checkpoint: {e}", file=sys.stderr)
        return False

    restored_count = 0
    for rel_path, content in data.get("files", {}).items():
        file_path = ws / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        restored_count += 1

    print(f"[OK] Restored checkpoint '{data.get('name')}' ({restored_count} files restored).")
    return True


def diff_checkpoint(ws: Path, name: str | None = None) -> None:
    cp_dir = get_checkpoint_dir(ws)
    if not cp_dir.exists():
        print("No checkpoints found.", file=sys.stderr)
        return

    if name:
        target_file = cp_dir / f"{name}.json"
    else:
        all_cps = sorted(cp_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not all_cps:
            print("No checkpoints found.", file=sys.stderr)
            return
        target_file = all_cps[0]

    data = json.loads(target_file.read_text(encoding="utf-8"))
    saved_files = data.get("files", {})

    modified: list[str] = []
    added: list[str] = []
    deleted: list[str] = []

    ignore_dirs = {".git", ".venv", "venv", "__pycache__", ".ai_checkpoints", "node_modules", "dist", "build"}
    current_files: dict[str, str] = {}
    for p in ws.rglob("*"):
        if not p.is_file():
            continue
        if any(part in ignore_dirs for part in p.parts):
            continue
        try:
            rel = str(p.relative_to(ws))
            current_files[rel] = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

    for rel, saved_content in saved_files.items():
        if rel not in current_files:
            deleted.append(rel)
        elif current_files[rel] != saved_content:
            modified.append(rel)

    for rel in current_files:
        if rel not in saved_files:
            added.append(rel)

    print(f"--- Differences against Checkpoint: {data.get('name')} ({data.get('timestamp')}) ---")
    if not modified and not added and not deleted:
        print("[OK] Workspace matches checkpoint exactly. Zero changes.")
        return

    if modified:
        print(f"\n[~] Modified ({len(modified)}):")
        for f in modified:
            print(f"  * {f}")
    if added:
        print(f"\n[+] Added ({len(added)}):")
        for f in added:
            print(f"  + {f}")
    if deleted:
        print(f"\n[-] Deleted ({len(deleted)}):")
        for f in deleted:
            print(f"  - {f}")


def clear_checkpoints(ws: Path) -> None:
    cp_dir = get_checkpoint_dir(ws)
    if cp_dir.exists():
        shutil.rmtree(cp_dir)
        print("[OK] All saved checkpoints removed.")
    else:
        print("No checkpoints exist.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Snapshot Checkpoint & Rollback Manager for AI Code Edits"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # save
    save_parser = subparsers.add_parser("save", help="Create an instant workspace checkpoint")
    save_parser.add_argument("name", nargs="?", help="Optional checkpoint name")

    # restore
    restore_parser = subparsers.add_parser("restore", help="Restore workspace to a checkpoint")
    restore_parser.add_argument("name", nargs="?", help="Checkpoint name (default: most recent)")

    # diff
    diff_parser = subparsers.add_parser("diff", help="View changes compared to a checkpoint")
    diff_parser.add_argument("name", nargs="?", help="Checkpoint name (default: most recent)")

    # list
    subparsers.add_parser("list", help="List all available checkpoints")

    # clear
    subparsers.add_parser("clear", help="Clear all stored checkpoints")

    args = parser.parse_args()
    ws = Path.cwd()

    if args.command == "save":
        saved_name = save_checkpoint(ws, args.name)
        print(f"[OK] Checkpoint saved: '{saved_name}'")
    elif args.command == "restore":
        if not restore_checkpoint(ws, args.name):
            return 1
    elif args.command == "diff":
        diff_checkpoint(ws, args.name)
    elif args.command == "list":
        cps = list_checkpoints(ws)
        if not cps:
            print("No saved checkpoints found.")
        else:
            print(f"Saved Checkpoints ({len(cps)}):")
            for checkpoint_info in cps:
                print(f"  * {checkpoint_info.get('name')}  [{checkpoint_info.get('timestamp')}]  ({checkpoint_info.get('total_files')} files)")
    elif args.command == "clear":
        clear_checkpoints(ws)

    return 0


if __name__ == "__main__":
    sys.exit(main())

