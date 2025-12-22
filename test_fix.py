"""
Test that pushed_at fix works for ink-and-memory repo.
"""
import asyncio
from github_client import GitHubClient
from commit_agent import CommitAgent
from datetime import datetime


async def test_fix():
    """Test that using pushed_at allows detecting feature branch commits."""
    client = GitHubClient()
    agent = CommitAgent(client, as_of=datetime.now())

    # Get repos
    repos = await client.get_repos(limit=15)

    # Find ink-and-memory
    ink_repo = next((r for r in repos if r['name'] == 'ink-and-memory'), None)

    if not ink_repo:
        print("ERROR: ink-and-memory repo not found")
        return

    print("=" * 80)
    print("TESTING FIX: Using pushed_at instead of updated_at")
    print("=" * 80)
    print(f"Repo: {ink_repo['name']}")
    print(f"Timestamp field being used (via 'updated_at' key): {ink_repo['updated_at']}")
    print()

    # Sync repos to fetch commits
    print("Syncing commits...")
    await agent.sync_repos([ink_repo])
    print()

    # Get commit counts
    commits = agent.get_commits(ink_repo['id'])
    print(f"Total commits fetched (last 30 days): {len(commits)}")

    if commits:
        print(f"\nLatest 5 commits:")
        for i, commit in enumerate(commits[:5], 1):
            print(f"  {i}. {commit['date']} - {commit['message'][:60]}")

    # Count recent commits
    now = datetime.now()
    from datetime import timedelta, timezone
    three_days_ago = now - timedelta(days=3)

    commits_3d = sum(1 for c in commits
                     if datetime.fromisoformat(c['date'].replace('Z', '+00:00')) >= three_days_ago.replace(tzinfo=timezone.utc))

    print(f"\nCommits in last 3 days: {commits_3d}")
    print()

    if commits_3d >= 6:
        print("✓ SUCCESS: Detected feature branch commits!")
        print("  The fix is working - pushed_at field triggered a refresh")
    elif commits_3d == 1:
        print("✗ FAILURE: Only detected main branch commit")
        print("  The fix didn't work - feature branch commits not detected")
    else:
        print(f"? PARTIAL: Detected {commits_3d} commits (expected 6 from feature branch)")


if __name__ == "__main__":
    asyncio.run(test_fix())
