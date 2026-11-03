import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import git_summary


class TestGitSummary(unittest.TestCase):
    """Tests for the git_summary script."""

    def test_run_git_command_success(self) -> None:
        """Test run_git_command on success."""
        with patch("subprocess.run") as mock_run:
            mock_process: MagicMock = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "output\n"
            mock_run.return_value = mock_process
            result: str = git_summary.run_git_command(Path("repo"), ["status"])
            self.assertEqual(result, "output")

    def test_run_git_command_failure(self) -> None:
        """Test run_git_command on failure."""
        with patch("subprocess.run") as mock_run:
            mock_process: MagicMock = MagicMock()
            mock_process.returncode = 1
            mock_run.return_value = mock_process
            result: str = git_summary.run_git_command(Path("repo"), ["status"])
            self.assertEqual(result, "")

    @patch("git_summary.run_git_command")
    def test_get_current_branch(self, mock_run_git_command: MagicMock) -> None:
        """Test get_current_branch."""
        mock_run_git_command.return_value = "main"
        result: str = git_summary.get_current_branch(Path("repo"))
        self.assertEqual(result, "main")

    @patch("git_summary.run_git_command")
    def test_get_dirty_file_count(self, mock_run_git_command: MagicMock) -> None:
        """Test get_dirty_file_count."""
        mock_run_git_command.return_value = " M file1.py\n?? file2.py"
        result: int = git_summary.get_dirty_file_count(Path("repo"))
        self.assertEqual(result, 2)

    @patch("git_summary.run_git_command")
    def test_get_unpushed_commits(self, mock_run_git_command: MagicMock) -> None:
        """Test get_unpushed_commits."""
        mock_run_git_command.return_value = "3"
        result: int = git_summary.get_unpushed_commits(Path("repo"), "main")
        self.assertEqual(result, 3)

    def test_get_unpushed_commits_no_branch(self) -> None:
        """Test get_unpushed_commits with no branch."""
        result: int = git_summary.get_unpushed_commits(Path("repo"), "")
        self.assertEqual(result, 0)

    @patch("git_summary.run_git_command")
    def test_get_last_commit_info(self, mock_run_git_command: MagicMock) -> None:
        """Test get_last_commit_info."""
        mock_run_git_command.return_value = "2023-10-25|Initial commit"
        result: dict[str, str] = git_summary.get_last_commit_info(Path("repo"))
        self.assertEqual(result, {"date": "2023-10-25", "message": "Initial commit"})

    @patch("git_summary.run_git_command")
    def test_get_last_commit_info_empty(self, mock_run_git_command: MagicMock) -> None:
        """Test get_last_commit_info with empty output."""
        mock_run_git_command.return_value = ""
        result: dict[str, str] = git_summary.get_last_commit_info(Path("repo"))
        self.assertEqual(result, {"date": "", "message": ""})

    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.iterdir")
    def test_discover_git_repos(self, mock_iterdir: MagicMock, mock_is_dir: MagicMock) -> None:
        """Test discover_git_repos."""
        mock_is_dir.side_effect = lambda: True

        # Mock paths
        repo1 = MagicMock(spec=Path)
        repo1.is_dir.return_value = True
        repo1_git = MagicMock(spec=Path)
        repo1_git.is_dir.return_value = True
        repo1.__truediv__.return_value = repo1_git
        repo1.__lt__.return_value = False # For sorting

        repo2 = MagicMock(spec=Path)
        repo2.is_dir.return_value = True
        repo2_git = MagicMock(spec=Path)
        repo2_git.is_dir.return_value = False
        repo2.__truediv__.return_value = repo2_git

        repo3 = MagicMock(spec=Path)
        repo3.is_dir.return_value = True
        repo3_git = MagicMock(spec=Path)
        repo3_git.is_dir.return_value = True
        repo3.__truediv__.return_value = repo3_git
        repo3.__lt__.return_value = True # For sorting

        mock_iterdir.return_value = [repo1, repo2, repo3]

        parent = Path("parent")
        result: list[Path] = git_summary.discover_git_repos(parent)
        self.assertEqual(len(result), 2)
        # Should be sorted, so repo3 comes first (because repo3 < repo1 is True)
        self.assertEqual(result, [repo3, repo1])

    @patch("git_summary.get_current_branch")
    @patch("git_summary.get_last_commit_info")
    @patch("git_summary.get_dirty_file_count")
    @patch("git_summary.get_unpushed_commits")
    def test_get_repo_summary(
        self,
        mock_get_unpushed_commits: MagicMock,
        mock_get_dirty_file_count: MagicMock,
        mock_get_last_commit_info: MagicMock,
        mock_get_current_branch: MagicMock,
    ) -> None:
        """Test get_repo_summary."""
        mock_get_current_branch.return_value = "main"
        mock_get_last_commit_info.return_value = {"date": "2023-10-25", "message": "msg"}
        mock_get_dirty_file_count.return_value = 1
        mock_get_unpushed_commits.return_value = 2

        repo = Path("repo")
        result: dict[str, Any] = git_summary.get_repo_summary(repo)

        expected = {
            "name": "repo",
            "branch": "main",
            "dirty_count": 1,
            "unpushed_count": 2,
            "last_commit_date": "2023-10-25",
            "last_commit_message": "msg",
        }
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
