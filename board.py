"""
Board - Dashboard computation and display logic.
"""
from datetime import datetime, timedelta
from typing import TypedDict


class ProjectRow(TypedDict):
    """Dashboard row for a single project."""
    project: str
    commit_count_3d: int
    commit_count_30d: int
    language: str
    working_state: str
    loc: int  # Future: lines of code


class Board:
    """Computes dashboard metrics from repo and commit data."""

    def __init__(self, repos: list[dict], commit_agent, as_of: datetime | None = None):
        """
        Initialize Board.

        Args:
            repos: List of repo dicts from GitHub
            commit_agent: CommitAgent instance for getting commits/summaries
            as_of: Timestamp to compute metrics relative to (for time-travel debugging)
        """
        self.repos = repos
        self.agent = commit_agent
        self.as_of = as_of or datetime.now()

    def get_projects(self) -> list[ProjectRow]:
        """
        Compute dashboard rows for all projects.

        Returns:
            List of ProjectRow dicts
        """
        projects = []

        for repo in self.repos:
            repo_id = repo["id"]
            commits = self.agent.get_commits(repo_id)

            row: ProjectRow = {
                "project": repo["name"],
                "commit_count_3d": self._count_commits_in_window(commits, days=3),
                "commit_count_30d": self._count_commits_in_window(commits, days=30),
                "language": repo["language"] or "N/A",
                "working_state": self.agent.get_summary(repo_id),
                "loc": 0,  # Placeholder for future implementation
            }
            projects.append(row)

        return projects

    def _count_commits_in_window(self, commits: list[dict], days: int) -> int:
        """
        Count commits within a time window.

        Args:
            commits: List of commit dicts with "date" field
            days: Number of days to look back from as_of

        Returns:
            Count of commits in the window
        """
        cutoff = self.as_of - timedelta(days=days)
        count = 0

        for commit in commits:
            # Parse ISO format date from GitHub
            commit_date = datetime.fromisoformat(commit["date"].replace("Z", "+00:00"))
            # Make as_of timezone-aware for comparison if needed
            cutoff_aware = cutoff.replace(tzinfo=commit_date.tzinfo) if commit_date.tzinfo else cutoff

            if commit_date >= cutoff_aware:
                count += 1

        return count
