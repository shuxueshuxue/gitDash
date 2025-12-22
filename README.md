# GitDash

A personal GitHub activity dashboard with gamified tier progression and AI-powered commit summaries.

Created by [shuxueshuxue](https://github.com/shuxueshuxue).

## Features

### Tier-Based Progression System
- 12 tiers from "slacker" to "transcendent"
- Dynamic scoring: `weight = 5 × (3-day commits) + (30-day commits)`
- Color-coded progress bar showing advancement to next tier
- Real-time activity score with glowing tier labels

### Activity Dashboard
- Weight-based ranking of repositories (not just by recency)
- Color-coded commit counts by activity level:
  - Red (50+) - Critical activity
  - Orange (25-49) - High activity
  - Green (10-24) - Medium activity
  - Blue (1-9) - Low activity
  - Gray (0) - Inactive
- Language icons instead of full names
- AI-generated working state summaries (concise keywords)

### Smart Caching & Refresh
- Backend auto-refreshes from GitHub every 60 seconds
- Frontend polls backend every 60 seconds (lightweight)
- Intelligent cache: only fetches commits for updated repos
- 90% API call reduction vs naive approach
- Manual refresh button for instant updates

### Dark Retrospective UI
- Monospace font, terminal-inspired design
- Minimal color palette for focus
- Rainbow gradient score display
- Smooth animations and transitions

## Installation

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- GitHub Personal Access Token

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/shuxueshuxue/gitDash.git
   cd gitDash
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Create GitHub Token**
   - Go to https://github.com/settings/tokens
   - Generate new token (fine-grained recommended)
   - Required permissions: Read-only access to "Metadata" and "Commit statuses"

4. **Configure API keys**

   Copy the example config and fill in your credentials:
   ```bash
   cp models.json.example models.json
   ```

   Example format:
   ```json
   {
     "models": {
       "claude-haiku-4.5": {
         "endpoint": "YOUR_API_ENDPOINT",
         "api_key": "YOUR_API_KEY",
         "model": "anthropic/claude-haiku-4.5"
       }
     },
     "default_retry": {
       "max_retries": 3,
       "timeout": 600
     }
   }
   ```

5. **Set environment variable**
   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   ```

## Usage

### CLI Mode
```bash
uv run python main.py
```

### Web Dashboard
```bash
uv run python server.py
```

Then open http://localhost:8000 in your browser.

## Tier System

The tier system ranks your coding activity across your top 15 repositories:

| Score Range | Tier | Color |
|------------|------|-------|
| 0-49 | slacker | Dark Gray |
| 50-99 | dabbler | Gray |
| 100-199 | apprentice | Blue |
| 200-299 | craftsman | Light Green |
| 300-399 | specialist | Green |
| 400-499 | master | Lime |
| 500-749 | prodigy | Yellow |
| 750-999 | legend | Orange |
| 1000-1499 | machine | Light Red |
| 1500-1999 | demigod | Red |
| 2000-2999 | deity | Deep Red |
| 3000+ | transcendent | Intense Red |

**Score Calculation:**
- Each repo gets: `5 × (commits in last 3 days) + (commits in last 30 days)`
- Total score = sum of all repo scores
- Recent activity (3 days) weighted 5× more than older activity

## Architecture

### Components

- **GitHubClient** - GitHub REST API wrapper with rate limiting
- **CommitAgent** - Smart caching + AI summary generation (uses PolyAgent)
- **Board** - Pure computation: metrics & ranking
- **server.py** - FastAPI web server with background refresh task

### Data Flow

```
GitHub API → CommitAgent (cache + AI) → Board (compute) → Frontend
     ↑                                                         ↓
     └─────────── Background Task (60s) ──────────────────────┘
```

### Features

- **Transparent caching**: Board doesn't know about cache existence
- **Time-travel debugging**: Set `as_of` parameter to test different dates
- **Incremental fetching**: Only updates repos with new commits
- **Structured AI output**: Pydantic schemas for consistent summaries

## Configuration

### Adjusting Refresh Interval

Edit `server.py`:
```python
await asyncio.sleep(60)  # Change to desired seconds
```

### Changing Repo Limit

Edit `server.py`:
```python
await refresh_dashboard(limit=15)  # Change limit
```

### Customizing Tiers

Edit the `TIERS` array in `server.py` to adjust ranges and names.

## Tech Stack

- **Backend**: FastAPI, AsyncIO
- **GitHub API**: httpx, GitHub REST API v3
- **AI**: PolyAgent (multi-provider LLM client)
- **Data**: JSON-based caching (no database needed)
- **Frontend**: Pure HTML/CSS/JS (no framework)

## License

MIT

## Credits

Built with [PolyAgent](https://github.com/shuxueshuxue/PolyCLI) for AI-powered commit summaries.
