---
name: browser-search
description: Search the web using Hermes built-in browser tools (Bing) — no Firecrawl credits needed. Uses browser_navigate + browser_console to extract results.
category: web
---

# Browser Search Skill (Bing via Built-in Tools)

**Purpose**: Replace Firecrawl/web_search with Hermes built-in browser automation for free web searches.

**Prerequisites**:
- `browser` toolset enabled (available by default)
- No separate browser/CDP management needed

## Usage

Load this skill, then use the search pattern:

```python
# 1. Navigate to Bing search
browser_navigate("https://www.bing.com/search?q={query}")

# 2. Extract results
browser_console(expression="""
Array.from(document.querySelectorAll('main li')).slice(0, 10).map(r => {
  const link = r.querySelector('a[href^="http"]');
  const titleEl = r.querySelector('h2, h3, [role="heading"]');
  const snippetEl = r.querySelector('p:not([class*="icon"]), .b_caption');
  return {
    title: titleEl ? titleEl.innerText.trim() : link?.innerText.trim() || '',
    url: link ? link.href : '',
    description: snippetEl ? snippetEl.innerText.trim() : ''
  };
}).filter(r => r.title && r.url && r.title.length > 5)
""")
```

## Standardized Output Format

Returns array of:
```json
[
  {"title": "...", "url": "...", "description": "..."},
  ...
]
```

## Selectors for Bing (current)

- Result containers: `main li` (list items in main search results)
- Title: `h2, h3, [role="heading"]` within result
- URL: `a[href^="http"]` (first link)
- Snippet: `p:not([class*="icon"]), .b_caption`

## Rate Limits & Etiquette

- Add 2-3s delay between searches
- Bing shows ~10 results per page
- URLs are Bing redirect links — extract clean URL if needed

## Integration with Scheduler

Update scheduler job:
- Toolsets: `["browser", "terminal", "file"]` (replace `web`)
- Load this skill in job config
- **Pre-step**: Run ensure script to guarantee Edge CDP is up:
  ```bash
  terminal(command="python C:/Users/qthas/AppData/Local/hermes/skills/web/edge-search/scripts/ensure_edge_cdp.py")
  ```
- Then use browser_navigate + browser_console for searches

**Pipeline integration:** See `mashbutton-gaming-pipeline` skill → `references/browser-search-integration-2026-06-15.md` for full zero-cost scheduler integration details.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Empty results | Wait longer after navigate, check selectors in DevTools |
| Bing redirect URLs | Accept as-is, or follow redirect to get clean URL |
| Bot detection | Add delays, rotate queries, use residential proxy if needed |
| Timeout | Increase navigation timeout, simplify query |
| **CDP port mismatch** | Hermes config (`browser.cdp_url`) must match the browser's `--remote-debugging-port`. Default is 9222; if browser runs on 9223, update config. |

## Configuration

- **Hermes built-in browser tools** (used by cronjobs with `enabled_toolsets: ["browser"]`): Connect to `browser.cdp_url` in Hermes config (default `http://127.0.0.1:9222`).
- **Browser launch**: Start Edge/Chrome with `--remote-debugging-port=9223` (or your chosen port).

```bash
# Example: Launch Edge on port 9223
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9223
```

## On-Demand Edge Launch (When Hermes Needs It)

The `ensure_edge_cdp.py` script runs **on-demand** when the cronjob executes — no startup scripts, no Task Scheduler. The cronjob runs it via terminal before using browser tools:

```bash
# Cronjob pre-step (runs automatically each tick)
python C:/Users/qthas/AppData/Local/hermes/skills/web/edge-search/scripts/ensure_edge_cdp.py
```

The script:
1. Checks if CDP endpoint `http://127.0.0.1:9223/json/version` responds
2. If not, launches Edge with `--remote-debugging-port=9223` (isolated profile)
3. Waits up to 30s for CDP to be ready
4. Exits 0 on success, 1 on failure (cronjob will report error)

## Files in Skill

- `scripts/browser_search.py` - Python helper using Hermes browser tools
- `scripts/ensure_edge_cdp.py` - Auto-detect/launch Edge on port 9223 (on-demand via cronjob)