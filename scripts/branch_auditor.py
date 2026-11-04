#!/usr/bin/env python3
import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))


def run_git_command(git_args: List[str]) -> str:
    """Run a git command and return its standard output."""
    process: subprocess.CompletedProcess[str] = subprocess.run(
        ["git"] + git_args, capture_output=True, text=True, check=False
    )
    return process.stdout.strip() if process.returncode == 0 else ""


def get_default_branch() -> str:
    """Determine the default branch for the repository."""
    remote_head: str = run_git_command(["symbolic-ref", "refs/remotes/origin/HEAD"])
    if remote_head:
        return remote_head.split("/")[-1]

    local_branches: str = run_git_command(["branch"])
    if "* main" in local_branches or "  main" in local_branches:
        return "main"
    return "master"


def get_merged_branches(default_branch: str) -> List[str]:
    """Get all local and remote branches merged into the default branch."""
    output: str = run_git_command(["branch", "-a", "--merged", default_branch])
    branches: List[str] = []

    for line in output.splitlines():
        clean_name: str = line.strip().strip("* ")
        if clean_name and "->" not in clean_name and clean_name != default_branch:
            if clean_name.startswith("remotes/origin/"):
                if clean_name.split("/")[-1] != default_branch:
                    branches.append(clean_name)
            else:
                branches.append(clean_name)

    return branches


def get_stale_unmerged_branches(default_branch: str) -> List[Tuple[str, str]]:
    """Identify unmerged branches that are stale (> 30 days)."""
    output: str = run_git_command(["branch", "-a", "--no-merged", default_branch])
    stale_branches: List[Tuple[str, str]] = []

    for line in output.splitlines():
        branch_name: str = line.strip().strip("* ")
        if not branch_name or "->" in branch_name or branch_name == default_branch:
            continue

        date_str: str = run_git_command(["log", "-1", "--format=%cI", branch_name])
        if not date_str:
            continue

        try:
            commit_date: datetime = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            days_old: int = (datetime.now(commit_date.tzinfo) - commit_date).days
            if days_old > 30:
                stale_branches.append((branch_name, str(days_old)))
        except ValueError:
            continue

    return stale_branches


def prune_merged_branches(branches: List[str], is_dry_run: bool) -> None:
    """Delete merged local branches."""
    for branch_name in branches:
        if not branch_name.startswith("remotes/"):
            print(f"Deleting local tracking branch: {branch_name}")
            if not is_dry_run:
                run_git_command(["branch", "-d", branch_name])


def main() -> None:
    """Main execution entry point."""
    argument_parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Audit git branches.")
    argument_parser.add_argument("--dry-run", action="store_true", help="Print actions without modifying state.")
    argument_parser.add_argument("--prune-merged", action="store_true", help="Delete merged local branches.")
    parsed_args: argparse.Namespace = argument_parser.parse_args()

    default_branch: str = get_default_branch()
    print(f"Default branch identified as: {default_branch}\n")

    merged_list: List[str] = get_merged_branches(default_branch)
    print("Merged branches (local and remote):")
    for b in merged_list:
        print(f"  - {b}")

    print("\nStale unmerged branches (> 30 days):")
    stale_list: List[Tuple[str, str]] = get_stale_unmerged_branches(default_branch)
    for b, days in stale_list:
        print(f"  - {b} ({days} days old)")

    if parsed_args.prune_merged:
        print("\nPruning merged local branches:")
        prune_merged_branches(merged_list, parsed_args.dry_run)


if __name__ == "__main__":
    main()
