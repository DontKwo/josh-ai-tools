import subprocess
import re
import argparse
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Commit:
    hash: str
    author: str
    type_: str
    scope: str
    description: str
    original_message: str

def parse_commit_message(hash_str: str, author: str, message: str) -> Commit:
    # Match conventional commit format: type(scope): description
    match_result = re.match(r"^([a-zA-Z]+)(?:\(([^)]+)\))?:\s*(.+)$", message)
    if match_result:
        commit_type = match_result.group(1).lower()
        commit_scope = match_result.group(2) if match_result.group(2) else ""
        commit_desc = match_result.group(3)
        return Commit(hash_str, author, commit_type, commit_scope, commit_desc, message)
    return Commit(hash_str, author, "other", "", message, message)

def get_git_commits(start_rev: Optional[str] = None, end_rev: str = "HEAD") -> List[Commit]:
    rev_range = f"{start_rev}..{end_rev}" if start_rev else end_rev
    command = ["git", "log", rev_range, "--format=%H|%an|%s"]
    process_result = subprocess.run(command, capture_output=True, text=True, check=True)
    commits_list = []

    for line in process_result.stdout.strip().split("\n"):
        if not line:
            continue
        line_parts = line.split("|", 2)
        if len(line_parts) == 3:
            commits_list.append(parse_commit_message(line_parts[0], line_parts[1], line_parts[2]))

    return commits_list

def categorize_commits(commits_list: List[Commit]) -> Dict[str, List[Commit]]:
    grouped_commits: Dict[str, List[Commit]] = {
        "feat": [], "fix": [], "perf": [], "docs": [],
        "refactor": [], "test": [], "chore": [], "other": []
    }
    for commit_obj in commits_list:
        if commit_obj.type_ in grouped_commits:
            grouped_commits[commit_obj.type_].append(commit_obj)
        else:
            grouped_commits["other"].append(commit_obj)
    return grouped_commits

def generate_markdown(version_name: str, publish_date: str, grouped_commits: Dict[str, List[Commit]]) -> str:
    output_lines = [f"## [{version_name}] - {publish_date}"]

    section_titles = {
        "feat": "Added",
        "fix": "Fixed",
        "perf": "Performance",
        "docs": "Documentation",
        "refactor": "Refactored",
        "test": "Tests",
        "chore": "Chores",
        "other": "Other"
    }

    for category_key, title_name in section_titles.items():
        if grouped_commits.get(category_key):
            output_lines.append(f"\n### {title_name}")
            for commit_obj in grouped_commits[category_key]:
                scope_prefix = f"**{commit_obj.scope}:** " if commit_obj.scope else ""
                short_hash = commit_obj.hash[:7]
                output_lines.append(f"- {scope_prefix}{commit_obj.description} ({short_hash} by {commit_obj.author})")

    return "\n".join(output_lines) + "\n"

def main() -> None:
    arg_parser = argparse.ArgumentParser(description="Generate changelog")
    arg_parser.add_argument("--start", type=str, help="Start revision", default=None)
    arg_parser.add_argument("--end", type=str, help="End revision", default="HEAD")
    arg_parser.add_argument("--version", type=str, help="Version name", required=True)
    parsed_args = arg_parser.parse_args()

    commits_list = get_git_commits(parsed_args.start, parsed_args.end)
    grouped_commits = categorize_commits(commits_list)
    current_date = datetime.now().strftime("%Y-%m-%d")

    markdown_output = generate_markdown(parsed_args.version, current_date, grouped_commits)
    print(markdown_output)

if __name__ == "__main__":
    main()
