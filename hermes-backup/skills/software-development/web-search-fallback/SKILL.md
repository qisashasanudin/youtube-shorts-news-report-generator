---
name: web-search-fallback
description: "Free web search: local browser/HTML scraping (primary) → optional Nous gateway fallback. Firecrawl is NOT used by default."
version: 1.0.0
author: Hermes Agent
tags: [web, search, fallback, browser, nous]
---

# Web Search Fallback Skill

Provides a search workflow that uses free local HTML scraping as the default, with optional browser/managed fallbacks. Firecrawl is NOT used by default.

## Usage

**`search_web` does NOT exist until you register the tool** (see Installation below). Loading this skill alone does not create it.

```python
# AFTER registering the tool (one-time or per-session):
search_web(query="battlefield 6 tsuru reef", limit=5)
# → tries free HTML scraper first, falls back to managed ONLY on error
```

Returns unified results from either source.

## Configuration

**Default Hermes config (what you have now):**
- `web.use_gateway: true`, `web.backend: firecrawl` → `web_search` tool hits Firecrawl (managed, bills via Nous)
- `browser.cdp_url: "http://localhost:9222"` → enables local browser tools (`browser_navigate`, etc.)

This skill documents an **alternative tool** (`search_web`) that uses the local browser as primary. It does not change the default `web_search` behavior.

## Fallback Triggers

**Only active AFTER you register `search_web` tool.**

- Billing errors (402, insufficient funds)
- Timeout errors (>30s)
- Network errors
- Empty results from primary HTML scraper

Without registration: `web_search` hits Firecrawl → fails with 402 → **stops dead**. No auto-fallback occurs.

## Implementation

The tool tries `web_search` first. On specific error patterns, it switches to `browser_navigate` + `browser_snapshot` on Bing/Startpage.

## Installation

The `search_web` tool must be registered with Hermes. Since skill tool auto-discovery only scans `tools/*.py` in the skill directory, you have two options:

### Option 1: Manual install (one-time)
```bash
# Copy the tool to Hermes core tools directory
cp ~/.hermes/skills/software-development/web-search-fallback/scripts/search_fallback_tool.py ~/.hermes/hermes-agent/tools/search_fallback.py

# Restart Hermes or run /reload in session
```

### Option 2: Load via skill script (per session)
```python
# In a session, run:
exec(open("~/.hermes/skills/software-development/web-search-fallback/scripts/register_tool.py").read())
```

### Option 3: Add to your config.yaml toolsets
```yaml
toolsets:
- hermes-cli
- web-search-fallback  # if packaged as toolset
---

## Tool Registration Files

- `scripts/search_fallback.py` — Core fallback logic
- `scripts/search_fallback_tool.py` — Hermes tool registration (copy to `~/.hermes/hermes-agent/tools/`)
- `scripts/register_tool.py` — Dynamic registration script for current session

## Reference Files

- `references/bing-snapshot-parsing.md` — Bing accessibility tree parsing patterns and extraction logic
- `references/hermes-tool-dispatch.md` — Critical Hermes tool handler signature pattern (args dict + kwargs)

---

## ⚠️ CRITICAL: This Skill Does NOT Auto-Hook

**This is a REFERENCE SKILL — it documents a pattern, it does not intercept tool calls.**

| What you might expect | Reality |
|----------------------|---------|
| "Fallback" triggers automatically on billing error | **No.** `web_search` tool hits Firecrawl first. Only AFTER you install/register `search_fallback_tool.py` does `search_web` exist and auto-fallback. |
| Loading this skill enables free search | **No.** Skill loading only puts this markdown in context. You must register the tool (see below). |
| Agent knows to use browser_navigate directly | **No.** Agent defaults to `web_search` tool (managed backend). You must explicitly direct it or register the fallback tool. |

### For "no spend / local only" users right now:
**Just use `browser_navigate` + `browser_snapshot` directly.** Skip the managed tool entirely. Example:
```python
browser_navigate("https://www.bing.com/search?q=your+query")
browser_snapshot(full=True)  # parse results, click links, extract data
```
No registration, no billing, no config changes needed — works immediately if CDP is connected.

---

## Key Implementation Notes (from session debugging)

### Hermes Tool Dispatch Pattern
Hermes tool registry calls handlers with `(args: dict, **kwargs)` — the first argument is always an `args` dict containing schema parameters. The handler must extract `query`, `limit` from `args`, and `task_id` from `kwargs`:

```python
def _search_web_dispatch(args: dict, **kwargs) -> str:
    query = args.get("query", "")
    limit = args.get("limit", 5)
    task_id = kwargs.pop("task_id", None)  # pop to avoid duplicate kwarg
    return search_web_tool(query=query, limit=limit, task_id=task_id, **kwargs)

registry.register(name="search_web", handler=_search_web_dispatch, ...)
```

## Primary search method (free)

Default to local HTML scraping before any managed search backend:
- Project-local script: `src/scripts/search_web.py` is the free search helper.
- Reference implementation: `video-ai-hoax-detector-api/app/nlp/web_search.py` is the source of truth for the free method.

## ⚠️ Critical: Tool Registration Required for Auto-Fallback

**The `search_web` tool does NOT auto-load.** Skill auto-discovery only scans `tools/*.py` in the skill directory. Until registered, billing errors (402, insufficient funds) on `web_search` will NOT trigger automatic fallback — you must manually use `browser_navigate` + `browser_snapshot` as shown in this session.

### Quick Registration (one-time, persists across sessions)

```bash
# Copy the tool to Hermes core tools directory
cp ~/.hermes/skills/software-development/web-search-fallback/scripts/search_fallback_tool.py ~/.hermes/hermes-agent/tools/search_fallback.py

# Restart Hermes or run /reload in session
```

### Per-Session Dynamic Registration (if you can't modify core tools)

```python
# In any session, run once:
exec(open("~/.hermes/skills/software-development/web-search-fallback/scripts/register_tool.py").read())
```

After either method, `search_web(query="...", limit=5)` becomes available and **will auto-fallback on billing errors, timeouts, network errors, or empty results**.

## Local Browser Setup (Edge on Windows, one-time)
```bash
# Verify CDP is reachable before relying on browser-based search:
curl -s http://127.0.0.1:9222/json/version

# Configure Hermes:
hermes config set browser.cdp_url "http://127.0.0.1:9222"
```

Important: if Edge is already running, launch a separate debug instance with a different `--user-data-dir`. Existing Edge processes do not inherit `--remote-debugging-port`.

## Windows gateway + CDP gotcha

**Do not keep retrying scheduler-side browser search when `browser_navigate` returns `Invalid CDP value: 'null'`.** That means the active gateway session is not picking up the updated CDP URL, even if `config.yaml` is correct. In that state, browser-based search is unavailable for that turning. Switch the scheduler path to a deterministic local script (`scheduler_search.py`) instead of retrying browser navigation.

## Fallback Strategy

If the scheduler prompt cannot produce output through AI-driven browsing or managed web search:
1. Use `src/scripts/search_web.py` or `src/scripts/scheduler_search.py` to collect results.
2. Have the cron job use `no_agent=True` with the script path.
3. Keep the job automated; avoid user-manual execution as the fix.

## Scheduler-Friendly Wrapper Pattern

Use script-backed scheduler jobs, not AI/prompt-driven search:
- Prefer actual article feeds over broad category search.
- Reject category/index URLs before they reach `scheduler_output.json`.
- Dedupe against `editorial_state.json`.
- Write `scheduler_output.json` directly from a deterministic script.
- Cron job should be `no_agent=True` with a stable `script` path.
- If `scheduler_output.json` has fewer than the expected number of real articles after a run, the next action is source/config review, not another blind scheduler rerun.

## Fallback Triggers
- Managed search backend unavailable / install blocked (PEP 668, billing)
- Timeout errors (>20-30s)
- Network errors
- Empty results from primary HTML scraper
- Browser fallback unreachable due to missing CDP endpoint

### Bing Results Parsing
The fallback navigates to `https://www.bing.com/search?q=<query>` and parses the accessibility tree snapshot. Key patterns:
- **Result links**: `- link "domain.com" [ref=eXX]`
- **Result titles**: `- heading "Title" [level=2, ref=eYY]`
- **Snippets**: `- paragraph` followed by `- StaticText "snippet text"`

**Filter out nav bar elements**: `back to bing`, `microsoft rewards`, `sign in`, `images`, `videos`, `maps`, `all`, `search`

### Fallback Trigger Patterns
```python
FALLBACK_TRIGGERS = [
    r"billing error", r"insufficient.*funds", r"payment required",
    r"charge authorization failed", r"402", r"timeout",
    r"ERR_CONNECTION_TIMED_OUT", r"ERR_NETWORK_CHANGED",
]
```

### Known Limitations
| Issue | Impact | Workaround |
|-------|--------|------------|
| Browser fallback slow (~20s) | High latency | Use free API tier for production |
| Snippets sometimes empty | Less context | Improve `format_bing_results` |
| Bing bot detection | Fails after ~5 searches | Use SearXNG or API key |
| Windows log rotation error | Cosmetic | Ignore - doesn't affect function |

### Local Browser Troubleshooting
- Symptom: `browser_navigate` returns `Invalid CDP value: 'null'`
- Fix: set `~/.hermes/config.yaml` `browser.cdp_url: "http://127.0.0.1:9222"`, then restart/reload Hermes so the running session picks up the new browser config.
- Symptom: Edge is already running, but port 9222 is not listening
- Fix: do not rely on existing Edge processes inheriting remote-debugging flags. Launch a separate debug instance with a dedicated `--user-data-dir`.

### Reference Implementations

- `video-ai-hoax-detector-api/app/nlp/web_search.py` — free reference Bing/Yahoo HTML search with authority scoring and dedupe.

```bash
# Tavily: 1,000 searches/mo free
hermes config set tavily.api_key YOUR_KEY

# Self-hosted SearXNG (Docker)
docker run -d -p 8888:8080 searxng/searxng
hermes config set web.search_backend searxng
hermes config set searxng.url http://localhost:8888
```