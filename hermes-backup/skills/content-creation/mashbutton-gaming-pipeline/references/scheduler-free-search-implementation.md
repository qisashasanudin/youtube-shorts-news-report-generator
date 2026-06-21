# Scheduler Free Search Implementation Notes

## Current Working Setup (2026-06-17)

**Job:** `shorts-news-scheduler` (ID: `80c55b5a2392`)
**Mode:** `no_agent=False` (agent mode) with `enabled_toolsets: ["browser", "file"]`
**Schedule:** `0 10,13,16,19 * * *` (4x/day)
**Delivery:** `discord`

## Architecture: Hermes Gateway CDP via Browser Toolset

The scheduler now runs as an **agent job** that uses Hermes gateway's browser tools (CDP on port 9222) to search Bing News directly:

1. **browser_navigate** → Bing News search (`https://www.bing.com/news/search?q=gaming+news+2026+shooter+FPS+this+week`)
2. **browser_snapshot(full=true)** → extracts structured news results (titles, snippets, sources, relative times)
3. **browser_click** → follows links to get canonical article URLs
4. **read_file** → loads `editorial_state.json` for URL deduplication
5. **write_file** → writes `scheduler_output.json` with exactly 10 stories
6. **stdout** → Discord-formatted report delivered automatically

**Zero local search code in repo** — all web search is through Hermes gateway CDP.

## Cron Job Configuration

```json
{
  "job_id": "80c55b5a2392",
  "no_agent": false,
  "enabled_toolsets": ["browser", "file"],
  "prompt": "You are the MashButtonGaming Shorts news scheduler. Find 10 fresh (≤7 days) shooter/FPS gaming news stories using Hermes browser CDP... (full prompt in job config)"
}
```

## Search Strategy

Two broad queries (no hardcoded game titles):
- `"gaming news 2026 shooter FPS this week"` (general)
- `"gaming leak 2026 shooter FPS this week"` (leakers/insiders)

Results filtered for:
- Shooter/FPS relevance (tactical, battle royale, extraction, Halo, CoD, Valorant, etc.)
- Reputable gaming sites (IGN, GameSpot, PC Gamer, Game Rant, Kotaku, Eurogamer, Polygon, etc.)
- ≤7 days old (relative time from Bing News: "2 days ago", "3 days ago")
- Not in `editorial_state.json` used_stories URLs

## Discord Report Format

The agent prints a human-readable report to stdout:

```
Scheduler results: 10 stories
1. Story Title Here
   URL: https://example.com/article
   Source: example.com
...
```

## Automation Contract

The user explicitly requires full automation. Never suggest "run this manually" as a permanent solution. If the scheduler breaks:
1. Fix the prompt/config
2. Update the job (`cronjob action='update'`)
3. Rerun the job (`cronjob action='run'`)
4. Verify `scheduler_output.json` has 10 valid stories

## Pipeline Integration

- **Scheduler** (cron job): Uses Hermes CDP → writes `scheduler_output.json`
- **main.py** (video builder): Reads `scheduler_output.json` only → builds Short
- **No search code in src/scripts/** — pure video pipeline

## Path Resolution

`main.py` reads `scheduler_output.json` from project root:
```python
scheduler_output = Path(__file__).resolve().parent.parent.parent / "scheduler_output.json"
```

## Advantages Over Previous Approach

- **True zero-cost** — no Firecrawl, no paid tools, no local HTTP scraping
- **Reliable** — Bing News HTML is stable, structured, and returns fresh results
- **Agent-native** — leverages Hermes gateway CDP directly
- **No browser management** — gateway handles CDP connection
- **Clean separation** — scheduler = search, builder = video