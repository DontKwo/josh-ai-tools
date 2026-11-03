#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))


def run_git_command(repo_path: Path, git_args: List[str]) -> str:
    """Run a git command in the specified repository and return the output."""
    command: List[str] = ["git", "-C", str(repo_path)] + git_args
    process_result: subprocess.CompletedProcess[str] = subprocess.run(
        command, capture_output=True, text=True, check=False
    )
    return process_result.stdout.strip() if process_result.returncode == 0 else ""


def get_current_branch(repo_path: Path) -> str:
    """Get the current git branch."""
    return run_git_command(repo_path, ["branch", "--show-current"])


def get_dirty_file_count(repo_path: Path) -> int:
    """Get the count of dirty files."""
    command_output: str = run_git_command(repo_path, ["status", "--porcelain"])
    return len([status_line for status_line in command_output.splitlines() if status_line])


def get_unpushed_commits(repo_path: Path, branch_name: str) -> int:
    """Get the count of unpushed commits for the current branch."""
    if not branch_name:
        return 0
    command_output: str = run_git_command(repo_path, ["rev-list", "--count", f"@{'{u}'}..HEAD"])
    return int(command_output) if command_output.isdigit() else 0


def get_last_commit_info(repo_path: Path) -> Dict[str, str]:
    """Get the last commit date and message."""
    command_output: str = run_git_command(repo_path, ["log", "-1", "--format=%cd|%s", "--date=short"])
    info_parts: List[str] = command_output.split("|", 1)
    if len(info_parts) == 2:
        return {"date": info_parts[0], "message": info_parts[1]}
    return {"date": "", "message": ""}


def discover_git_repos(parent_directory: Path) -> List[Path]:
    """Find all git repositories in the immediate subdirectories of parent_directory."""
    repository_list: List[Path] = []
    if not parent_directory.is_dir():
        return repository_list
    for child_path in parent_directory.iterdir():
        if child_path.is_dir() and (child_path / ".git").is_dir():
            repository_list.append(child_path)
    return sorted(repository_list)


def get_repo_summary(repo_path: Path) -> Dict[str, Any]:
    """Get a summary of the git repository status."""
    branch_name: str = get_current_branch(repo_path)
    commit_information: Dict[str, str] = get_last_commit_info(repo_path)
    return {
        "name": repo_path.name,
        "branch": branch_name,
        "dirty_count": get_dirty_file_count(repo_path),
        "unpushed_count": get_unpushed_commits(repo_path, branch_name),
        "last_commit_date": commit_information["date"],
        "last_commit_message": commit_information["message"],
    }


def print_tabular_summary(summary_list: List[Dict[str, Any]]) -> None:
    """Print the repository summaries in a tabular format."""
    print(f"{'Repository':<20} | {'Branch':<15} | {'Dirty':<5} | {'Unpushed':<8} | {'Date':<10} | Message")
    print("-" * 80)
    for repo_summary in summary_list:
        repo_name: str = str(repo_summary["name"])[:19]
        repo_branch: str = str(repo_summary["branch"])[:14]
        dirty_str: str = str(repo_summary["dirty_count"])
        unpushed_str: str = str(repo_summary["unpushed_count"])
        date_str: str = str(repo_summary["last_commit_date"])
        msg_str: str = str(repo_summary["last_commit_message"])
        print(f"{repo_name:<20} | {repo_branch:<15} | {dirty_str:<5} | {unpushed_str:<8} | {date_str:<10} | {msg_str}")


def main() -> None:
    """Main entry point for the git summary script."""
    argument_parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Git repository summary")
    argument_parser.add_argument("directory", type=str, nargs="?", default=".", help="Parent directory")
    argument_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parsed_args: argparse.Namespace = argument_parser.parse_args()

    parent_directory: Path = Path(parsed_args.directory).resolve()
    found_repos: List[Path] = discover_git_repos(parent_directory)
    all_summaries: List[Dict[str, Any]] = [get_repo_summary(repo_path) for repo_path in found_repos]

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if parsed_args.json:
        print(json.dumps(all_summaries, indent=2))
    else:
        print_tabular_summary(all_summaries)


if __name__ == "__main__":
    main()
