# Browser Search Integration (Zero-Cost) — **Updated 2026-06-17**

**Session:** 2026-06-17  
**Problem:** Scheduler (`shorts-news-scheduler`) was using Firecrawl via `web` toolset (~$0.000966/search, ~$0.0386/day, burning $0.10 Free-tier credits in ~2.6 days)  
**Solution:** Replace Firecrawl with Hermes gateway browser tools (Bing News search via CDP) — **$0.00 credits**. No local search code in repo.

## Current Implementation: Agent Mode + Hermes Gateway CDP

### Scheduler Cron Job Config (`80c55b5a2392`)
```json
{
  "no_agent": false,
  "enabled_toolsets": ["browser", "file"],
  "prompt": "You are the MashButtonGaming Shorts news scheduler. Find 10 fresh (≤7 days) shooter/FPS gaming news stories using Hermes browser CDP..."
}
```

**Key change:** Agent mode (`no_agent: false`) with `browser` toolset — the Hermes gateway handles CDP connection internally.

### Agent Workflow (Tested Working 2026-06-17)

1. **browser_navigate** → Bing News search (2 queries):
   - `https://www.bing.com/news/search?q=gaming+news+2026+shooter+FPS+this+week`
   - `https://www.bing.com/news/search?q=gaming+leak+2026+shooter+FPS+this+week`

2. **browser_snapshot(full=true)** → Extracts structured news results:
   - Title (heading level 2)
   - Snippet (StaticText)
   - Source (image alt: "DualShockers", "Push Square", "PC Gamer", etc.)
   - Relative time ("2 days ago", "6 days ago")

3. **browser_click** on result links → get canonical article URLs

4. **read_file** `editorial_state.json` → URL deduplication

5. **write_file** `scheduler_output.json` → 10 stories in standard format

6. **stdout** → Discord-formatted report delivered automatically

### Cost Impact
| Component | Before | After |
|-----------|--------|-------|
| Scheduler searches | Firecrawl ($0.000966/ea) | Hermes gateway browser ($0.00) |
| Daily credit burn | ~$0.0386/day | $0.00 |
| Monthly credit survival | ~2.6 days | **Indefinite** |
| Nemotron inference | Free (Nous Portal) | Free |

### Scheduler Frequency Preserved
- **MUST stay at 4×/day** (10:00, 13:00, 16:00, 19:00 WIB)
- User explicitly rejected reducing cadence for credit savings
- Zero-cost gateway browser search removes the credit constraint entirely

### Pipeline Integration (Clean Separation)

- **Scheduler (cron job):** Hermes gateway CDP → writes `scheduler_output.json`
- **main.py (video builder):** Reads `scheduler_output.json` only → pure video pipeline
- **No search code in src/scripts/** — all web search externalized to gateway

### Files
- Scheduler cron job: `80c55b5a2392` (updated to agent mode + browser toolset)
- Project: `C:/Users/qthas/Programming/Belajar/YouTube/youtube-shorts-news-report-generator`
- `src/scripts/main.py` updated to read from `scheduler_output.json`
- All local search scripts removed from repo (`search_web.py`, `search_engine.py`, `mashbutton_scheduler_search.py`)