"""
CommitAgent - Manages commit caching and AI summary generation.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from pydantic import BaseModel, Field
from polycli import PolyAgent


class CommitSummary(BaseModel):
    """Structured summary of recent commits."""
    summary: str = Field(description="3-5 keywords describing recent work, no subject, just activities (e.g., 'refactoring auth, fixing bugs, adding tests')")
    focus_areas: list[str] = Field(description="Key areas being worked on (max 3 items)")


class CommitAgent:
    """Orchestrates commit fetching, caching, and AI summarization."""

    def __init__(self, github_client, as_of: datetime | None = None):
        """
        Initialize CommitAgent.

        Args:
            github_client: GitHubClient instance for fetching commits
            as_of: Virtual "current time" for time-travel debugging
        """
        self.github = github_client
        self.cache = {}  # {repo_id: {"commits": [], "last_fetched": str, "summary": str, "summary_at": str}}
        self.ai = PolyAgent()
        self.as_of = as_of or datetime.now()

    async def sync_repos(self, repos: list[dict]) -> None:
        """
        Sync commits for repos that have been updated.

        Args:
            repos: List of repo dicts with id, name, owner, updated_at
        """
        for repo in repos:
            repo_id = str(repo["id"])  # Convert to string for JSON cache lookup
            updated_at = repo["updated_at"]

            # Check if we need to fetch
            # Parse timestamps as timezone-aware datetime objects for proper comparison
            needs_fetch = True
            if repo_id in self.cache:
                last_fetched_str = self.cache[repo_id].get("last_fetched")
                if last_fetched_str:
                    # Parse both timestamps to timezone-aware datetime objects
                    updated_at_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    last_fetched_dt = datetime.fromisoformat(last_fetched_str)
                    # Convert naive local time to UTC properly
                    if last_fetched_dt.tzinfo is None:
                        # Assume last_fetched is in local time, convert to UTC
                        last_fetched_dt = last_fetched_dt.astimezone(timezone.utc)

                    if updated_at_dt <= last_fetched_dt:
                        needs_fetch = False

            if needs_fetch:
                try:
                    print(f"Fetching commits for {repo['name']}...")
                    # Only fetch last 30 days (our longest window) from most recent branch
                    since = self.as_of - timedelta(days=30)
                    commits = await self.github.get_commits(
                        owner=repo["owner"],
                        repo=repo["name"],
                        since=since,
                        per_page=100,
                        use_most_recent_branch=True
                    )

                    # Store in cache
                    self.cache[repo_id] = {
                        "commits": commits,
                        "last_fetched": self.as_of.isoformat(),
                        "summary": None,
                        "summary_at": None,
                    }

                    # Generate AI summary for recent commits
                    if commits:
                        summary = await self._generate_summary(repo["name"], commits[:5])
                        self.cache[repo_id]["summary"] = summary
                        self.cache[repo_id]["summary_at"] = self.as_of.isoformat()
                except Exception as e:
                    print(f"  Error fetching {repo['name']}: {str(e)}")
                    # Store empty cache entry so we don't retry immediately
                    self.cache[repo_id] = {
                        "commits": [],
                        "last_fetched": self.as_of.isoformat(),
                        "summary": f"Error: {str(e)[:50]}",
                        "summary_at": self.as_of.isoformat(),
                    }

    async def _generate_summary(self, repo_name: str, recent_commits: list[dict]) -> str:
        """
        Generate AI summary of recent commits.

        Args:
            repo_name: Repository name
            recent_commits: List of recent commits (up to 5)

        Returns:
            Summary string
        """
        if not recent_commits:
            return "No recent activity"

        # Format commit messages for AI
        commit_text = f"Repository: {repo_name}\n\nRecent commits:\n"
        for i, commit in enumerate(recent_commits, 1):
            commit_text += f"{i}. {commit['message']}\n"

        prompt = f"""{commit_text}

Provide 3-5 keywords describing the work, no subject term. Example: "fixing UI bugs, refactoring auth, adding tests" """

        try:
            result = self.ai.run(
                prompt=prompt,
                model="claude-haiku-4.5",
                cli="no-tools",
                ephemeral=True,  # Don't save to conversation history
                schema_cls=CommitSummary
            )

            if result.has_data():
                return result.data["summary"]
            return result.content.strip()
        except Exception as e:
            return f"Summary generation failed: {str(e)}"

    def get_commits(self, repo_id: int) -> list[dict]:
        """Get cached commits for a repo."""
        repo_id = str(repo_id)  # Convert to string for JSON cache lookup
        if repo_id in self.cache:
            return self.cache[repo_id].get("commits", [])
        return []

    def get_summary(self, repo_id: int) -> str:
        """Get AI summary for a repo."""
        repo_id = str(repo_id)  # Convert to string for JSON cache lookup
        if repo_id in self.cache:
            return self.cache[repo_id].get("summary") or "No summary available"
        return "Not synced yet"

    def save_cache(self, filepath: str = "cache.json") -> None:
        """Save cache to JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.cache, f, indent=2)
        print(f"Cache saved to {filepath}")

    def load_cache(self, filepath: str = "cache.json") -> None:
        """Load cache from JSON file."""
        path = Path(filepath)
        if path.exists():
            with open(filepath, "r") as f:
                self.cache = json.load(f)
            print(f"Cache loaded from {filepath}")
        else:
            print(f"No cache file found at {filepath}")
