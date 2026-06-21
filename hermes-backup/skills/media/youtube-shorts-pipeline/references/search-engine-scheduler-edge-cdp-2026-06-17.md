# Search-Engine-Based News Scheduler with Edge CDP Auto-Management

**Created:** 2026-06-17  
**Project:** MashButtonGaming / `youtube-shorts-news-report-generator`  
**Cron Job ID:** `80c55b5a2392` (shorts-news-scheduler)

## Problem Solved

Replaced per-outlet RSS feed scraping (`src/scripts/main.py` → 20 feeds) with a **broad search engine approach** using direct HTTP requests to Bing & Yahoo. Added automatic Edge headless launch/check so the scheduler survives laptop restarts without manual intervention.

## Implementation

### Scheduler Script
`src/scripts/mashbutton_scheduler_search.py` — standalone, runs via `cronjob` with `no_agent=True`.

**Key features:**
- **Search queries:** 15 shooter game queries + 6 Twitter leaker queries (rotated each run)
- **Search backend:** `src/scripts/search_web.py` — direct HTML scraping of Bing & Yahoo (no browser/CDP required for search)
- **Edge CDP auto-management:** `ensure_edge_cdp()` checks port 9222, kills stale Edge processes, launches fresh headless instance with `--remote-debugging-port=9222`
- **Deduplication:** Against `editorial_state.json` (`used_stories` + `stories`) via URL and normalized title
- **Output:** Exactly 10 stories to `scheduler_output.json` with Discord-ready report printed to stdout
- **Blocking:** Filters e-commerce, social media, store domains via `BLOCKED_DOMAINS`

### Cronjob Configuration
```json
{
  "job_id": "80c55b5a2392",
  "name": "shorts-news-scheduler",
  "schedule": "0 10,13,16,19 * * *",  // 4x/day WIB
  "script": "mashbutton_scheduler_search.py",
  "no_agent": true,
  "enabled_toolsets": ["terminal", "file"],
  "workdir": "C:\\Users\\qthas\\Programming\\Belajar\\YouTube\\youtube-shorts-news-report-generator",
  "deliver": "discord"
}
```

### Edge Headless Launch Logic
```python
def ensure_edge_cdp() -> bool:
    if check_edge_cdp():  # HTTP GET /json/version
        return True
    # Kill existing msedge.exe
    subprocess.run(["taskkill", "/f", "/im", "msedge.exe"], capture_output=True)
    # Launch with user profile + CDP
    subprocess.Popen([
        edge_exe,
        f"--remote-debugging-port={EDGE_CDP_PORT}",
        "--headless=new",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run", "--no-default-browser-check",
        "--disable-extensions", "--disable-background-networking",
        "about:blank",
    ], creationflags=subprocess.DETACHED_PROCESS)
    # Poll for readiness
```

**Result:** On laptop restart, next scheduler tick auto-relaunches Edge headless — zero manual steps.

## Query Rotation (Example)
```python
SHOOTER_QUERIES = [
    "battlefield 6 news 2026",
    "call of duty modern warfare 4 news 2026",
    "valorant patch notes 2026",
    "counter-strike 2 update 2026",
    "overwatch 2 new hero 2026",
    "tactical shooter games 2026",
    "rainbow six siege update 2026",
    "escape from tarkov news 2026",
    "apex legends season 2026",
    "halo infinite update 2026",
    "destiny 2 news 2026",
    "fps games 2026 release",
    "third person shooter games 2026",
    "xbox showcase shooter games 2026",
    "playstation shooter games 2026",
]
TWITTER_LEAKER_QUERIES = [
    "billbil-kun leak 2026 shooter",
    "insider gaming leak 2026 fps",
    "tom henderson leak 2026",
    "jeff grubb leak 2026",
    "shpeshal nick leak 2026",
    "midori leak 2026",
]
```

## Output Format (`scheduler_output.json`)
```json
{
  "stories": [
    {
      "title": "Battlefield 6 2026 Roadmap Includes Gameplay Changes...",
      "published": "2026-06-17T09:53:31.038146",
      "source_domain": "insider-gaming.com",
      "official_url": "https://insider-gaming.com/battlefield-6-2026-roadmap...",
      "rationale": "Search query: battlefield 6 news 2026",
      "verify_query": "battlefield 6 news 2026"
    }
    // ... 9 more
  ]
}
```

## Discard Notes (What Didn't Work)
- **RSS feeds** (`main.py`): Returned non-gaming content (Polygon), limited coverage
- **Firecrawl/AI search**: Blocked by externally-managed Python environment, user explicitly banned paid tools
- **Browser/CDP for search**: Unreliable — CDP connection drops, browser_navigate fails with `Invalid CDP value: 'null'`
- **DuckDuckGo**: Blocked in user's country (requires VPN/DNS)

## Verification
```bash
cd C:/Users/qthas/Programming/Belajar/YouTube/youtube-shorts-news-report-generator
python src/scripts/mashbutton_scheduler_search.py
# → Prints Discord report, writes scheduler_output.json
cronjob action=run job_id=80c55b5a2392
# → Runs via scheduler, delivers to Discord
```

## Integration Points
- **Downstream:** `src/shorts_builder.py` reads `scheduler_output.json` for candidate stories
- **Pipeline fetch:** `src/scripts/main.py` now uses `search_web.py` (Bing/Yahoo) instead of RSS feeds — same broad search engine approach for the video build pipeline
- **Editorial state:** `src/editorial_state.py` / `editorial_state.json` for dedup + daily upload counter
- **Watchdog:** `shorts-news-watchdog` (job `bab0abf9f152`) monitors scheduler health
- **Cleanup:** `shorts-news-cleanup` (job `477b924aca59`) removes temp folders

## Future Extensions
- Add Google HTML search (requires different User-Agent / rate limiting)
- Expand Twitter leaker query list with more handles
- Add source authority weighting (official > insider > aggregator)
- Include date range filtering in search queries (last 72h only)

## Cleanup Performed (2026-06-17)
- Removed unused scheduler scripts: `src/scripts/scheduler_search.py`, `src/scripts/scheduler_search_free.py`
- Removed unused chromium binary: `tools/chromium/chrome-win.zip`
- Updated `.gitignore` to exclude runtime state files: `scheduler_output.json`, `editorial_state.json`, `analytics_log.json`
- Removed those files from git history (`git rm --cached` + push)
- Repo now clean: no uncommitted changes, no tracked runtime state files