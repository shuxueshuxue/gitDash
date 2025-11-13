"""
GitDash - Personal GitHub Activity Dashboard
"""
import asyncio
from datetime import datetime
from github_client import GitHubClient
from commit_agent import CommitAgent
from board import Board


async def main(as_of: datetime | None = None):
    """
    Run the dashboard.

    Args:
        as_of: Virtual "current time" for time-travel debugging (default: now)
    """
    as_of = as_of or datetime.now()

    print("=" * 80)
    print("GitDash - Personal GitHub Activity Dashboard")
    print(f"Time: {as_of.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

    # Initialize components
    github = GitHubClient()
    agent = CommitAgent(github, as_of=as_of)

    # Try to load existing cache
    agent.load_cache()

    # Fetch repos (limit to 3 for testing)
    print("Fetching repositories...\n")
    repos = await github.get_repos(limit=3)

    if not repos:
        print("No repositories found. Make sure GITHUB_TOKEN is set.")
        return

    print(f"Found {len(repos)} repositories\n")

    # Sync commits and generate summaries
    print("Syncing commits and generating AI summaries...\n")
    await agent.sync_repos(repos)

    # Save cache for next time
    agent.save_cache()
    print()

    # Create board and get dashboard data
    board = Board(repos, agent, as_of=as_of)
    projects = board.get_projects()

    # Display dashboard
    print("=" * 80)
    print("DASHBOARD")
    print("=" * 80)
    print(f"{'Project':<20} {'3d':<5} {'30d':<6} {'Language':<12} {'Working State'}")
    print("-" * 80)

    for proj in projects:
        project = proj["project"][:18]
        count_3d = proj["commit_count_3d"]
        count_30d = proj["commit_count_30d"]
        lang = (proj["language"] or "N/A")[:10]
        state = proj["working_state"][:35] + "..." if len(proj["working_state"]) > 38 else proj["working_state"]

        print(f"{project:<20} {count_3d:<5} {count_30d:<6} {lang:<12} {state}")

    print("=" * 80)

    # Show rate limit
    rate_info = await github.get_rate_limit()
    core = rate_info["resources"]["core"]
    print(f"\nAPI Rate Limit: {core['remaining']}/{core['limit']} remaining")
    print(f"Resets at: {datetime.fromtimestamp(core['reset']).strftime('%H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
