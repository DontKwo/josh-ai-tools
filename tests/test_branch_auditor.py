import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import branch_auditor


class TestBranchAuditor(unittest.TestCase):
    """Test suite for the branch auditor script."""

    @patch("branch_auditor.run_git_command")
    def test_get_default_branch_remote(self, mock_run: MagicMock) -> None:
        """Test getting default branch from remote symbolic ref."""
        mock_run.return_value = "refs/remotes/origin/main"
        result: str = branch_auditor.get_default_branch()
        self.assertEqual(result, "main")
        mock_run.assert_called_once_with(["symbolic-ref", "refs/remotes/origin/HEAD"])

    @patch("branch_auditor.run_git_command")
    def test_get_default_branch_local_fallback(self, mock_run: MagicMock) -> None:
        """Test getting default branch via local branch fallback."""
        def side_effect(args: List[str]) -> str:
            if args[0] == "symbolic-ref":
                return ""
            if args[0] == "branch":
                return "  feature\n* master\n"
            return ""

        mock_run.side_effect = side_effect
        result: str = branch_auditor.get_default_branch()
        self.assertEqual(result, "master")

    @patch("branch_auditor.run_git_command")
    def test_get_merged_branches(self, mock_run: MagicMock) -> None:
        """Test getting merged local and remote branches."""
        mock_run.return_value = "  feature-1\n* main\n  remotes/origin/feature-1\n  remotes/origin/HEAD -> origin/main"
        result: List[str] = branch_auditor.get_merged_branches("main")

        self.assertIn("feature-1", result)
        self.assertIn("remotes/origin/feature-1", result)
        self.assertNotIn("main", result)
        self.assertNotIn("remotes/origin/HEAD -> origin/main", result)

    @patch("branch_auditor.run_git_command")
    def test_get_stale_unmerged_branches(self, mock_run: MagicMock) -> None:
        """Test finding stale unmerged branches."""
        stale_date: str = (datetime.now() - timedelta(days=40)).isoformat()
        recent_date: str = (datetime.now() - timedelta(days=10)).isoformat()

        def side_effect(args: List[str]) -> str:
            if args[0] == "branch":
                return "  stale-branch\n  recent-branch\n"
            if args[0] == "log":
                if args[-1] == "stale-branch":
                    return stale_date
                if args[-1] == "recent-branch":
                    return recent_date
            return ""

        mock_run.side_effect = side_effect
        result: List[tuple[str, str]] = branch_auditor.get_stale_unmerged_branches("main")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "stale-branch")
        self.assertTrue(int(result[0][1]) >= 40)

    @patch("branch_auditor.run_git_command")
    def test_prune_merged_branches(self, mock_run: MagicMock) -> None:
        """Test pruning of merged branches."""
        branches: List[str] = ["feature-a", "remotes/origin/feature-a"]

        branch_auditor.prune_merged_branches(branches, is_dry_run=True)
        mock_run.assert_not_called()

        branch_auditor.prune_merged_branches(branches, is_dry_run=False)
        mock_run.assert_called_once_with(["branch", "-d", "feature-a"])

if __name__ == "__main__":
    unittest.main()
