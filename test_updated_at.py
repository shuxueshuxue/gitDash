"""
Test to verify GitHub's updated_at field behavior for non-default branches.
"""
import asyncio
from datetime import datetime
from github_client import GitHubClient


async def investigate_updated_at():
    """Check ink-and-memory repo's updated_at field."""
    client = GitHubClient()

    # Get repo metadata
    print("Fetching ink-and-memory repo metadata...\n")
    repo_data = await client.get("/repos/shuxueshuxue/ink-and-memory")

    print("=" * 80)
    print("REPO METADATA")
    print("=" * 80)
    print(f"Name: {repo_data['name']}")
    print(f"Default branch: {repo_data['default_branch']}")
    print(f"Updated at: {repo_data['updated_at']}")
    print(f"Pushed at: {repo_data['pushed_at']}")
    print()

    # Get default branch (main) commits
    print("=" * 80)
    print("DEFAULT BRANCH (main) - Last 5 commits")
    print("=" * 80)
    main_commits = await client.get_commits(
        owner="shuxueshuxue",
        repo="ink-and-memory",
        branch="main",
        per_page=5
    )
    for commit in main_commits[:5]:
        print(f"  {commit['date']} - {commit['message'][:50]}")

    # Get feature/deck-system branch commits
    print("\n" + "=" * 80)
    print("FEATURE/DECK-SYSTEM BRANCH - Last 5 commits")
    print("=" * 80)
    feature_commits = await client.get_commits(
        owner="shuxueshuxue",
        repo="ink-and-memory",
        branch="feature/deck-system",
        per_page=5
    )
    for commit in feature_commits[:5]:
        print(f"  {commit['date']} - {commit['message'][:50]}")

    # Compare timestamps
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    repo_updated = datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00'))
    repo_pushed = datetime.fromisoformat(repo_data['pushed_at'].replace('Z', '+00:00'))

    latest_main = datetime.fromisoformat(main_commits[0]['date'].replace('Z', '+00:00'))
    latest_feature = datetime.fromisoformat(feature_commits[0]['date'].replace('Z', '+00:00'))

    print(f"Repo updated_at: {repo_updated}")
    print(f"Repo pushed_at:  {repo_pushed}")
    print(f"Latest on main:  {latest_main}")
    print(f"Latest on feature/deck-system: {latest_feature}")
    print()

    print("Comparison:")
    print(f"  updated_at == pushed_at? {repo_updated == repo_pushed}")
    print(f"  pushed_at == latest feature commit? {repo_pushed == latest_feature}")
    print(f"  updated_at reflects feature branch? {repo_updated >= latest_feature}")
    print()

    if repo_pushed == latest_feature:
        print("✓ RESULT: pushed_at DOES update for non-default branch commits")
        print("  The cache logic should use 'pushed_at' instead of 'updated_at'")
    else:
        print("✗ RESULT: Neither field reflects the latest commit on feature branch")


if __name__ == "__main__":
    asyncio.run(investigate_updated_at())
