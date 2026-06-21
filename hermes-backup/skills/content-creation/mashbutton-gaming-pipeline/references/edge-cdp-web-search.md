# Edge CDP Web Search — Firecrawl Replacement (2026-06-15)

## Problem
Nous Portal Firecrawl credits exhausted ($0.10/month Free tier → ~2.6 days at 4×/day scheduler). User demands **zero-cost** operation. Inference model (Nemotron 3 Ultra via Nous) is free; only tool calls cost credits.

## Solution: Edge Browser + CDP (localhost:9222)

### Prerequisites
1. Start Edge with remote debugging:
   ```bash
   "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\edge-debug"
   ```
2. In Hermes: `/browser connect` to attach

### Search Implementation Pattern

**DuckDuckGo HTML (no JS required, fast):**
```python
# Navigate to search
browser_navigate(url=f"https://html.duckduckgo.com/html/?q={query}")
# Extract results from .result__snippet, .result__title, .result__url
```

**Bing HTML (richer snippets):**
```python
browser_navigate(url=f"https://www.bing.com/search?q={query}")
# Extract from .b_caption, .b_title, cite
```

**Google (requires JS, more complex):**
```python
browser_navigate(url=f"https://www.google.com/search?q={query}")
# Extract from .g, .VwiC3b, .LC20lb
```

### CDP Extraction Snippet
```javascript
// Run via browser_console(expression=...)
document.querySelectorAll('.result__snippet').forEach(el => console.log(el.innerText))
```

### Agent Workflow for Scheduler
1. **Start Edge CDP** (one-time at session start or via startup script)
2. **For each search query**: `browser_navigate` → `browser_console` extraction → parse results
3. **Return structured results** matching `web_search` format: `[{url, title, description}, ...]`
4. **No Nous credits consumed**

### Integration with Scheduler Job
- Update `shorts-news-scheduler` job: replace `web` toolset with `browser`
- Load new `edge-cdp-search` skill (to be created) or use inline browser commands
- Scheduler runs 4×/day → 40 searches/day → **$0.00 cost**

### Fallback Chain (when CDP unavailable)
1. **Edge CDP + DuckDuckGo** (primary, zero cost)
2. **curl + Bing HTML scrape** (backup, see `web-search-tool-limitation-and-workaround.md`)
3. **Nous Firecrawl** (last resort, only if credits available)

### Advantages
- **True zero-cost** — no API credits, no subscription
- **Full browser control** — can handle JS, pagination, complex selectors
- **Local execution** — no external dependency
- **Reuses existing browser toolset** — no new infrastructure

### Limitations
- Requires Edge running with CDP (manual start or startup script)
- Slower than API (~2-5s per search vs ~0.5s)
- Brittle selectors if search engine HTML changes
- Cannot run headless in cron without display (use `--headless=new` for Edge 109+)

### Edge Headless CDP (for cron)
```bash
msedge.exe --headless=new --remote-debugging-port=9222 --user-data-dir="C:\temp\edge-debug"
```
Works in scheduled tasks with proper desktop session.

### Scheduler Prompt Update Required
When switching to Edge CDP search, the scheduler prompt must:
- Use `browser` toolset instead of `web`
- Call browser tools directly (no `web_search` function)
- Handle pagination manually if needed
- Return 10 candidates in existing output format

### Reference Implementation Checklist
- [ ] Create `edge-cdp-search` skill with search functions
- [ ] Update scheduler job toolset: `web` → `browser`
- [ ] Add Edge CDP startup to gateway launch script
- [ ] Test 40 searches/day for stability
- [ ] Document selector maintenance schedule