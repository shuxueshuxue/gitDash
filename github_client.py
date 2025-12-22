"""
Simple GitHub API client wrapper for exploring your repositories.
"""
import os
from datetime import datetime, timedelta
from typing import Any
import httpx


class GitHubClient:
    """Lightweight wrapper around GitHub REST API."""

    def __init__(self, token: str | None = None):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token (or set GITHUB_TOKEN env var)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def get(self, endpoint: str, params: dict | None = None) -> dict | list:
        """Make GET request to GitHub API."""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params or {})
            response.raise_for_status()
            return response.json()

    async def get_repos(self, username: str | None = None, type: str = "owner", limit: int | None = None) -> list[dict]:
        """
        Fetch user's repositories.

        Args:
            username: GitHub username (if None, fetches authenticated user's repos)
            type: Repository type filter - "owner", "public", "member", etc.
            limit: Maximum number of repos to return (for testing)

        Returns:
            List of repository objects with id, name, owner, language, updated_at
        """
        if username:
            endpoint = f"/users/{username}/repos"
        else:
            endpoint = "/user/repos"

        params = {"type": type, "sort": "updated", "per_page": limit or 100}
        repos = await self.get(endpoint, params)

        # Normalize to our schema
        result = []
        for repo in repos[:limit] if limit else repos:
            result.append({
                "id": repo["id"],
                "name": repo["name"],
                "owner": repo["owner"]["login"],
                "language": repo["language"],
                "updated_at": repo["pushed_at"],  # Use pushed_at to detect commits on all branches
            })
        return result

    async def get_most_recent_branch(self, owner: str, repo: str) -> str | None:
        """
        Find the most recently active branch in a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Branch name with most recent commit, or None if error
        """
        try:
            endpoint = f"/repos/{owner}/{repo}/branches"
            branches = await self.get(endpoint, {"per_page": 100})

            if not branches:
                return None

            # Find branch with most recent commit
            most_recent = None
            most_recent_date = None

            for branch in branches:
                # Get commit details for each branch head
                commit_sha = branch["commit"]["sha"]
                commit_endpoint = f"/repos/{owner}/{repo}/commits/{commit_sha}"
                commit_detail = await self.get(commit_endpoint)
                commit_date = commit_detail["commit"]["author"]["date"]

                if most_recent_date is None or commit_date > most_recent_date:
                    most_recent_date = commit_date
                    most_recent = branch["name"]

            return most_recent
        except Exception as e:
            print(f"Warning: Could not determine most recent branch: {e}")
            return None

    async def get_commits(
        self,
        owner: str,
        repo: str,
        since: datetime | None = None,
        until: datetime | None = None,
        per_page: int = 100,
        branch: str | None = None,
        use_most_recent_branch: bool = False
    ) -> list[dict]:
        """
        Fetch commits for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            since: Only commits after this date
            until: Only commits before this date
            per_page: Results per page (max 100)
            branch: Specific branch to fetch from
            use_most_recent_branch: If True, auto-detect most recently active branch

        Returns:
            List of commit objects with sha, message, date, author
        """
        # Determine which branch to use
        if use_most_recent_branch:
            branch = await self.get_most_recent_branch(owner, repo)
            if branch:
                print(f"  Using most recent branch: {branch}")

        endpoint = f"/repos/{owner}/{repo}/commits"
        params = {"per_page": per_page}

        if branch:
            params["sha"] = branch
        if since:
            params["since"] = since.isoformat()
        if until:
            params["until"] = until.isoformat()

        raw_commits = await self.get(endpoint, params)

        # Normalize to our schema
        result = []
        for commit in raw_commits:
            result.append({
                "sha": commit["sha"],
                "message": commit["commit"]["message"],
                "date": commit["commit"]["author"]["date"],
                "author": commit["commit"]["author"]["name"],
            })
        return result

    async def get_rate_limit(self) -> dict:
        """Check current API rate limit status."""
        return await self.get("/rate_limit")


async def explore_repos():
    """Quick exploration script to see your repos."""
    client = GitHubClient()

    print("🔍 Fetching your repositories...\n")

    # Get authenticated user's repos
    repos = await client.get_repos()

    print(f"Found {len(repos)} repositories:\n")
    print(f"{'Repository':<40} {'Updated':<20} {'Language':<15} {'Stars'}")
    print("-" * 90)

    for repo in repos[:20]:  # Show first 20
        name = repo['name'][:38]
        updated = repo['updated_at'][:10]
        language = (repo['language'] or 'N/A')[:13]
        stars = repo['stargazers_count']

        print(f"{name:<40} {updated:<20} {language:<15} {stars}")

    print("\n" + "=" * 90)

    # Show rate limit
    rate_limit = await client.get_rate_limit()
    core = rate_limit['resources']['core']
    print(f"\n⚡ API Rate Limit: {core['remaining']}/{core['limit']} remaining")
    print(f"   Resets at: {datetime.fromtimestamp(core['reset']).strftime('%H:%M:%S')}")

    return repos


if __name__ == "__main__":
    import asyncio
    asyncio.run(explore_repos())
