---
name: hermes-web-tools-setup
description: "Configure and troubleshoot Hermes web tools (Firecrawl search/extract, browser automation) including Nous subscription gateway and direct API key fallbacks. Covers common failure modes: exhausted credits, billing errors, gateway timeouts, and cron job web tool isolation."
category: software-development
tags: [hermes, configuration, web-tools, firecrawl, tavily, browser-automation, troubleshooting]
---

# Hermes Web Tools Setup & Troubleshooting

## Overview
Hermes provides web capabilities through two pathways:
1. **Nous Portal Gateway** (default) \u2014 managed Firecrawl, browser-use, FAL, TTS/STT via subscription
2. **Direct API Keys** \u2014 Firecrawl, Tavily, Browserbase, etc. configured in `~/.hermes/config.yaml` and `~/.hermes/.env`

When the Nous subscription is exhausted or misconfigured, web tools fail with `BILLING_ERROR` / `Payment Required`. This skill covers diagnosis, fallback configuration, and cron job considerations.

---

## Quick Diagnosis

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Payment Required: Charge authorization failed` + `insufficient_funds` | Nous Firecrawl credits exhausted | Add direct Firecrawl/Tavily API key OR wait for daily reset |
| Browser `Operation timed out` | Gateway unavailable / browser-use not ready | Set `browser.use_gateway: false` for local browser |
| Cron job works but interactive session fails | Different tool routing (cron uses `enabled_toolsets`) | Check job's `enabled_toolsets` includes `web` |

---

## Configuration Steps

### 1. Disable Nous Gateway (use local/direct backends)
```bash
hermes config set web.use_gateway false
hermes config set browser.use_gateway false
```

### 2. Add Direct Firecrawl API Key (recommended for reliability)
```bash
hermes config set firecrawl.api_key YOUR_FIRECRAWL_API_KEY
```
Get key at: https://firecrawl.dev

### 3. Alternative: Add Tavily API Key
```bash
hermes config set tavily.api_key YOUR_TAVILY_API_KEY
```
Get key at: https://tavily.com

### 4. Browser Automation (local via CDP) — FREE, No API Keys
For completely free web search without any API keys, use a local Chromium/Edge browser with CDP (Chrome DevTools Protocol). This bypasses all gateway billing.

**Setup (one-time):**
```bash
# 1. Start Edge/Chrome with remote debugging (run in background)
"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --remote-debugging-port=9222 --user-data-dir="/tmp/edge-debug" --headless=new &

# 2. Configure Hermes to use local CDP
hermes config set browser.use_gateway false
hermes config set browser.cdp_url "http://localhost:9222"
hermes config set browser.allow_private_urls true

# 3. Verify connection
curl -s http://localhost:9222/json/version
```

**Usage (replaces `web_search`):**
```python
# Search
browser_navigate("https://www.bing.com/search?q=your+query")

# Extract results  
browser_snapshot(full=True)

# Click results
browser_click(ref="@e31")  # use ref from snapshot
```

**Tested & working:**
- Bing search returns results reliably
- Content extraction via `browser_snapshot`
- Link clicking works
- Zero cost — no API keys, no subscription

**Known limitation:** Search engines show bot detection/CAPTCHA after ~3-5 searches from headless browsers. For production daily use, consider:
| Option | Effort | Reliability |
|--------|--------|-------------|
| Self-hosted SearXNG (Docker) | Medium | High |
| BrowserBase free tier (stealth) | Low | Medium |
| Tavily/Firecrawl free tier (API key) | Low | High |
| Direct site scraping (known sources) | Low | High for specific sites |

**Alternative local browser (Camofox):**
```bash
pip install camofox  # Note: may not be on PyPI yet
camofox install
hermes config set browser.engine camofox
```

---

## Cron Job Web Tool Isolation

Cron jobs run in isolated sessions with explicitly declared `enabled_toolsets`. A job with `enabled_toolsets: ["web", "terminal", "file"]` gets web tools **even if the main session has gateway issues**, because:
- The cron runner spawns a fresh agent with only those toolsets
- Tool routing is determined at job creation, not at runtime
- The job's `workdir` may have project-specific `.env` with API keys

**To debug a cron job's web access:**
1. `cronjob action=list` \u2192 note `job_id`
2. Check `enabled_toolsets` includes `\"web\"`
3. Check `workdir` for local `.env` with `FIRECRAWL_API_KEY` or `TAVILY_API_KEY`
4. Run manually: `cronjob action=run job_id=<id>`

---

## Common Pitfalls

| Pitfall | Prevention |
|---------|------------|
| Assuming subscription credits are unlimited | Monitor `hermes status` \u2192 \"Nous Tool Gateway\" section shows active managed tools |
| Forgetting cron jobs need `web` in `enabled_toolsets` | Always include `\"web\"` when creating jobs that research |
| Mixing gateway + direct keys causing conflicts | Set `use_gateway: false` when using direct API keys |
| Browser timeout on first run | Local browser downloads Chromium on first use \u2014 allow 60-120s |

---

## Verification Commands

```bash
# Check current config
hermes config show

# Test web search directly
hermes web_search \"test query\" --limit 1

# Test browser
hermes browser_navigate \"https://example.com\"

# Full diagnostics
hermes doctor
```

---

## References

- `references/nous-billing-errors.md` \u2014 Common Nous Portal billing error codes and resolutions
- `references/cron-web-tool-isolation.md` \u2014 How cron job toolsets differ from interactive sessions