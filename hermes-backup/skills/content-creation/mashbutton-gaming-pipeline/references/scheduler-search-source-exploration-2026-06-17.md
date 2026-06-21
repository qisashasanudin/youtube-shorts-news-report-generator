# Scheduler Search Source Exploration (2026-06-17)

## Outcome — Hermes Gateway CDP (Final)

Per-outlet scraping removed. All web search moved to **Hermes gateway browser tools (CDP)** via scheduler agent. No local search scripts in repo.

## Architecture

- **Scheduler cron job:** Agent mode (`no_agent: false`) with `enabled_toolsets: ["browser", "file"]`
- **Search method:** Hermes gateway CDP → Bing News search
- **No local search code** — all web search externalized to gateway

## Search Strategy

**Two broad queries (no hardcoded game titles):**
- `"gaming news 2026 shooter FPS this week"` (general)
- `"gaming leak 2026 shooter FPS this week"` (leakers/insiders)

**Agent workflow:**
1. `browser_navigate` → Bing News search URLs
2. `browser_snapshot(full=true)` → extract structured results (title, snippet, source, relative time)
3. `browser_click` on links → canonical URLs
4. `read_file` editorial_state.json → dedupe
5. `write_file` scheduler_output.json → 10 stories

**Filtering:** Shooter/FPS relevance, ≤7 days old, not in used_stories URLs

## Blockers Explored (and abandoned)

| Approach | Result |
|----------|--------|
| Bing HTML scrape (direct HTTP) | 200 OK but zero parser matches for broad queries; locale forced to Indonesian |
| Yahoo HTML | 500 `INKApi Error` |
| DuckDuckGo HTML | User confirmed blocked in country (VPN required) |
| Site-specific Bing queries | Localized to Indonesian/generic; unreliable for FPS/TPS |
| Site-specific RSS (Polygon, GameSpot, etc.) | Works but limited scope; replaced by broad Bing News |

## User Rules Preserved

- No hardcoded game titles in queries
- No paid/search-gateway tools in the scheduler
- Keep exact 10-story quota per scheduler run
- Send real article URLs; never placeholders

## Current Implementation

- **Zero local search code** in `src/scripts/`
- **Scheduler:** Hermes gateway CDP via browser toolset
- **Builder:** Reads `scheduler_output.json` only
- **Cost:** $0.00/month (gateway CDP included in Nous subscription)
