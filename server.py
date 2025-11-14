"""
FastAPI web server for GitDash dashboard.
"""
import os
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from github_client import GitHubClient
from commit_agent import CommitAgent
from board import Board


# Global state
dashboard_data = None
last_refresh = None
github_client = None
commit_agent = None


async def background_refresh_task():
    """Background task to refresh dashboard every minute."""
    global dashboard_data, last_refresh

    while True:
        try:
            await asyncio.sleep(60)  # Wait 1 minute
            if os.getenv("GITHUB_TOKEN"):
                print("Background refresh triggered...")
                await refresh_dashboard(limit=15)
        except Exception as e:
            print(f"Background refresh error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup."""
    global github_client, commit_agent

    # Check for GitHub token
    if not os.getenv("GITHUB_TOKEN"):
        print("WARNING: GITHUB_TOKEN not set. Set it before making API calls.")

    # Initialize clients
    github_client = GitHubClient()
    commit_agent = CommitAgent(github_client)

    # Load cache if exists
    commit_agent.load_cache()

    # Start background refresh task
    refresh_task = asyncio.create_task(background_refresh_task())

    print("GitDash server initialized with background refresh")
    yield

    # Cancel background task on shutdown
    refresh_task.cancel()
    print("GitDash server shutting down")


app = FastAPI(title="GitDash", lifespan=lifespan)


async def refresh_dashboard(limit: int = None):
    """Refresh dashboard data from GitHub."""
    global dashboard_data, last_refresh

    if not os.getenv("GITHUB_TOKEN"):
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not set")

    # Update agent's as_of time to current time
    commit_agent.as_of = datetime.now()

    # Fetch repos
    repos = await github_client.get_repos(limit=limit)

    # Sync commits
    await commit_agent.sync_repos(repos)

    # Save cache
    commit_agent.save_cache()

    # Generate board
    board = Board(repos, commit_agent, as_of=datetime.now())
    projects = board.get_projects()

    # Update global state
    dashboard_data = {
        "projects": projects,
        "timestamp": datetime.now().isoformat(),
        "repo_count": len(repos)
    }
    last_refresh = datetime.now()

    return dashboard_data


@app.get("/")
async def root():
    """Serve the dashboard HTML page."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitDash - GitHub Activity Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Courier New', monospace;
            background: #0a0a0a;
            color: #d0d0d0;
            min-height: 100vh;
            padding: 2rem;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #333;
        }

        .title-section {
            display: flex;
            align-items: center;
            gap: 2rem;
        }

        .title {
            font-size: 1rem;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .score-panel {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .score-display {
            display: flex;
            align-items: baseline;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .score-label {
            font-size: 0.75rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .next-tier {
            font-size: 0.75rem;
            color: #777;
            font-style: italic;
            opacity: 0.8;
        }

        .total-score {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #ff6b6b, #ffa94d, #69db7c, #4dabf7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -1px;
        }

        .tier-label {
            font-size: 0.9rem;
            font-weight: 600;
            text-transform: lowercase;
            letter-spacing: 0.5px;
            text-shadow: 0 0 10px currentColor;
            transition: all 0.3s;
        }

        .progress-container {
            width: 200px;
            height: 6px;
            background: #222;
            border-radius: 3px;
            overflow: hidden;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
        }

        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b, #ffa94d, #69db7c, #4dabf7);
            transition: width 0.5s ease;
            border-radius: 3px;
            box-shadow: 0 0 10px currentColor;
        }

        .controls {
            display: flex;
            gap: 1rem;
            align-items: center;
        }

        .status {
            font-size: 0.85rem;
            color: #888;
        }

        .refresh-btn {
            background: transparent;
            border: 1px solid #555;
            color: #bbb;
            width: 36px;
            height: 36px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
        }

        .refresh-btn:hover {
            border-color: #777;
            color: #fff;
            background: #1a1a1a;
        }

        .refresh-btn:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }

        .dashboard {
            background: #0f0f0f;
            border: 1px solid #222;
            overflow: hidden;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        thead {
            background: #151515;
            border-bottom: 1px solid #333;
        }

        th, td {
            padding: 0.875rem 1rem;
            text-align: left;
            font-size: 1rem;
        }

        th {
            font-weight: 500;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 1px;
            color: #888;
        }

        tbody tr {
            border-bottom: 1px solid #1a1a1a;
            transition: background 0.15s;
        }

        tbody tr:hover {
            background: #151515;
        }

        .project-link {
            color: #c0c0c0;
            text-decoration: none;
            transition: color 0.2s;
        }

        .project-link:hover {
            color: #fff;
        }

        .commit-count {
            font-variant-numeric: tabular-nums;
        }

        .weight-critical { color: #ff6b6b; font-weight: 700; }  /* 50+ */
        .weight-high { color: #ffa94d; font-weight: 600; }      /* 25-49 */
        .weight-medium { color: #69db7c; font-weight: 500; }    /* 10-24 */
        .weight-low { color: #4dabf7; font-weight: 400; }       /* 1-9 */
        .weight-none { color: #555; font-weight: 300; }         /* 0 */

        .language {
            color: #909090;
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .working-state {
            color: #999;
            max-width: 400px;
            font-size: 0.9rem;
        }

        .loading {
            text-align: center;
            padding: 3rem;
            color: #888;
            font-size: 1rem;
        }

        .error {
            background: #1a0a0a;
            color: #c66;
            padding: 1rem;
            margin: 1rem 0;
            border-left: 2px solid #c66;
            font-size: 1rem;
        }

        .spinner {
            display: inline-block;
            width: 1.2rem;
            height: 1.2rem;
            border: 2px solid #222;
            border-top: 2px solid #666;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <div class="title-section">
                <div class="title">github activity</div>
                <div class="score-panel">
                    <div class="score-display">
                        <span class="score-label">score:</span>
                        <span class="total-score" id="totalScore">0</span>
                        <span class="score-label">tier:</span>
                        <span class="tier-label" id="tierLabel">slacker</span>
                        <span class="next-tier" id="nextTier">→ next: dabbler</span>
                    </div>
                    <div class="progress-container">
                        <div class="progress-bar" id="progressBar" style="width: 0%"></div>
                    </div>
                </div>
            </div>
            <div class="controls">
                <div class="status" id="status">loading...</div>
                <button onclick="refreshDashboard()" id="refreshBtn" class="refresh-btn" title="Refresh">
                    ↻
                </button>
            </div>
        </div>

        <div class="dashboard">
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>initializing...</p>
            </div>
            <div id="error" style="display: none;"></div>
            <table id="dashboardTable" style="display: none;">
                <thead>
                    <tr>
                        <th>project</th>
                        <th>3d</th>
                        <th>30d</th>
                        <th>lang</th>
                        <th>status</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                </tbody>
            </table>
        </div>
    </div>

    <script>
        let isRefreshing = false;

        async function loadDashboard() {
            // Poll backend for current state (doesn't trigger refresh)
            try {
                const response = await fetch('/api/dashboard');
                const data = await response.json();

                if (response.ok) {
                    renderDashboard(data);
                } else {
                    showError(data.detail || 'failed to load');
                }
            } catch (error) {
                showError('network error: ' + error.message);
            }
        }

        async function refreshDashboard() {
            // Manual refresh - triggers immediate backend fetch
            if (isRefreshing) return;

            isRefreshing = true;
            const btn = document.getElementById('refreshBtn');
            btn.disabled = true;

            try {
                const response = await fetch('/api/refresh', { method: 'POST' });
                const data = await response.json();

                if (response.ok) {
                    renderDashboard(data);
                } else {
                    showError(data.detail || 'failed to refresh');
                }
            } catch (error) {
                showError('network error: ' + error.message);
            } finally {
                isRefreshing = false;
                btn.disabled = false;
            }
        }

        const TIERS = [
            { min: 0, max: 49, name: 'slacker', color: '#444' },
            { min: 50, max: 99, name: 'dabbler', color: '#666' },
            { min: 100, max: 199, name: 'apprentice', color: '#4dabf7' },
            { min: 200, max: 299, name: 'craftsman', color: '#51cf66' },
            { min: 300, max: 399, name: 'specialist', color: '#69db7c' },
            { min: 400, max: 499, name: 'master', color: '#94d82d' },
            { min: 500, max: 749, name: 'prodigy', color: '#ffd43b' },
            { min: 750, max: 999, name: 'legend', color: '#ffa94d' },
            { min: 1000, max: 1499, name: 'machine', color: '#ff8787' },
            { min: 1500, max: 1999, name: 'demigod', color: '#ff6b6b' },
            { min: 2000, max: 2999, name: 'deity', color: '#fa5252' },
            { min: 3000, max: Infinity, name: 'transcendent', color: '#e03131' }
        ];

        function getTierInfo(score) {
            const tier = TIERS.find(t => score >= t.min && score <= t.max);
            const nextTier = TIERS.find(t => t.min > score);

            let progress = 0;
            if (nextTier) {
                const currentTierMin = tier.min;
                const nextTierMin = nextTier.min;
                const range = nextTierMin - currentTierMin;
                const current = score - currentTierMin;
                progress = (current / range) * 100;
            } else {
                progress = 100; // Max tier
            }

            return { tier, nextTier, progress };
        }

        function getWeightClass(weight) {
            if (weight >= 50) return 'weight-critical';
            if (weight >= 25) return 'weight-high';
            if (weight >= 10) return 'weight-medium';
            if (weight >= 1) return 'weight-low';
            return 'weight-none';
        }

        function getLanguageIcon(lang) {
            const icons = {
                'JavaScript': 'JS',
                'TypeScript': 'TS',
                'Python': 'PY',
                'Java': 'JAVA',
                'Go': 'GO',
                'Rust': 'RS',
                'C': 'C',
                'C++': 'C++',
                'Ruby': 'RB',
                'PHP': 'PHP',
                'HTML': 'HTML',
                'CSS': 'CSS',
                'Shell': 'SH',
                'Vue': 'VUE',
                'Kotlin': 'KT',
                'Swift': 'SWIFT',
                'Dart': 'DART',
                'Scala': 'SCALA',
                'Elixir': 'EX',
                'Haskell': 'HS',
                'N/A': '—'
            };
            return icons[lang] || lang.substring(0, 4).toUpperCase();
        }

        function renderDashboard(data) {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            document.getElementById('dashboardTable').style.display = 'table';

            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';

            // Calculate total score
            let totalScore = 0;

            data.projects.forEach(project => {
                const weightClass = getWeightClass(project.weight);
                const langIcon = getLanguageIcon(project.language);

                totalScore += project.weight;

                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><a href="${escapeHtml(project.url)}" target="_blank" class="project-link">${escapeHtml(project.project)}</a></td>
                    <td class="commit-count ${weightClass}">${project.commit_count_3d}</td>
                    <td class="commit-count ${weightClass}">${project.commit_count_30d}</td>
                    <td><span class="language">${langIcon}</span></td>
                    <td class="working-state">${escapeHtml(project.working_state)}</td>
                `;
                tbody.appendChild(row);
            });

            // Update total score and tier
            const tierInfo = getTierInfo(totalScore);

            document.getElementById('totalScore').textContent = totalScore;

            const tierLabel = document.getElementById('tierLabel');
            tierLabel.textContent = tierInfo.tier.name;
            tierLabel.style.color = tierInfo.tier.color;

            const nextTierElement = document.getElementById('nextTier');
            if (tierInfo.nextTier) {
                nextTierElement.textContent = `→ next: ${tierInfo.nextTier.name}`;
                nextTierElement.style.display = 'inline';
            } else {
                nextTierElement.style.display = 'none';
            }

            document.getElementById('progressBar').style.width = `${tierInfo.progress}%`;

            const timestamp = new Date(data.timestamp).toLocaleString();
            document.getElementById('status').textContent =
                `${data.repo_count} repos • ${timestamp}`;
        }

        function showError(message) {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('dashboardTable').style.display = 'none';
            const errorDiv = document.getElementById('error');
            errorDiv.className = 'error';
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Load on page load
        loadDashboard();

        // Auto-refresh every minute
        setInterval(loadDashboard, 60 * 1000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/dashboard")
async def get_dashboard():
    """Get current dashboard data (read-only, doesn't trigger refresh)."""
    global dashboard_data

    if dashboard_data is None:
        # First load - fetch data once
        await refresh_dashboard(limit=15)

    return JSONResponse(dashboard_data)


@app.post("/api/refresh")
async def refresh():
    """Manually refresh dashboard data from GitHub."""
    return await refresh_dashboard(limit=15)


@app.get("/api/status")
async def status():
    """Get server status."""
    return {
        "status": "ok",
        "last_refresh": last_refresh.isoformat() if last_refresh else None,
        "has_data": dashboard_data is not None,
        "github_token_set": bool(os.getenv("GITHUB_TOKEN"))
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
