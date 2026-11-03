import unittest
from unittest.mock import patch
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from changelog_generator import Commit, parse_commit_message, get_git_commits, categorize_commits, generate_markdown

class TestChangelogGenerator(unittest.TestCase):
    def test_parse_commit_message_feat_scope(self) -> None:
        commit_obj = parse_commit_message("hash1", "Alice", "feat(api): add new endpoint")
        self.assertEqual(commit_obj.type_, "feat")
        self.assertEqual(commit_obj.scope, "api")
        self.assertEqual(commit_obj.description, "add new endpoint")

    def test_parse_commit_message_fix_no_scope(self) -> None:
        commit_obj = parse_commit_message("hash2", "Bob", "fix: correct typo")
        self.assertEqual(commit_obj.type_, "fix")
        self.assertEqual(commit_obj.scope, "")
        self.assertEqual(commit_obj.description, "correct typo")

    def test_parse_commit_message_other(self) -> None:
        commit_obj = parse_commit_message("hash3", "Charlie", "Merge branch 'main'")
        self.assertEqual(commit_obj.type_, "other")
        self.assertEqual(commit_obj.scope, "")
        self.assertEqual(commit_obj.description, "Merge branch 'main'")

    @patch("subprocess.run")
    def test_get_git_commits(self, mock_subprocess_run: unittest.mock.Mock) -> None:
        # Mock git log output
        mock_process = unittest.mock.Mock()
        mock_process.stdout = "h1|Alice|feat: a\nh2|Bob|fix: b\n"
        mock_subprocess_run.return_value = mock_process

        commits_list = get_git_commits("v1.0.0", "HEAD")

        self.assertEqual(len(commits_list), 2)
        self.assertEqual(commits_list[0].hash, "h1")
        self.assertEqual(commits_list[1].author, "Bob")

    def test_categorize_commits(self) -> None:
        commits_list = [
            Commit("h1", "A", "feat", "api", "a", "msg"),
            Commit("h2", "B", "fix", "", "b", "msg"),
            Commit("h3", "C", "feat", "", "c", "msg"),
            Commit("h4", "D", "other", "", "d", "msg"),
        ]

        grouped_commits = categorize_commits(commits_list)

        self.assertEqual(len(grouped_commits["feat"]), 2)
        self.assertEqual(len(grouped_commits["fix"]), 1)
        self.assertEqual(len(grouped_commits["other"]), 1)
        self.assertEqual(len(grouped_commits["docs"]), 0)

    def test_generate_markdown(self) -> None:
        commits_list = [
            Commit("1234567890", "Alice", "feat", "api", "add endpoint", "msg"),
            Commit("abcdef1234", "Bob", "fix", "", "correct typo", "msg"),
        ]
        grouped_commits = categorize_commits(commits_list)

        markdown_output = generate_markdown("1.1.0", "2023-10-27", grouped_commits)

        self.assertIn("## [1.1.0] - 2023-10-27", markdown_output)
        self.assertIn("### Added", markdown_output)
        self.assertIn("- **api:** add endpoint (1234567 by Alice)", markdown_output)
        self.assertIn("### Fixed", markdown_output)
        self.assertIn("- correct typo (abcdef1 by Bob)", markdown_output)
        self.assertNotIn("### Performance", markdown_output)

if __name__ == '__main__':
    unittest.main()
