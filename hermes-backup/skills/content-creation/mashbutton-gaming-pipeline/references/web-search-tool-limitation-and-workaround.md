# Web Search Tool Limitation & Workaround (2026-06-15)

## Problem

The `web_search` and `web_extract` tools in Hermes Agent route through the **Nous Portal Firecrawl gateway** regardless of config settings.

**Config that does NOT work:**
```yaml
web:
  backend: duckduckgo
  use_gateway: false
```

The tool implementation hardcodes the Nous gateway call. When Nous subscription credits are exhausted (billing error, $0 balance), both tools fail with:
```
Firecrawl search failed: Payment Required: Failed to search. {'code': 'BILLING_ERROR', ... 'error': 'Insufficient available balance for requested reservation', 'code': 'insufficient_funds' ...}
```

This happened on 2026-06-15 when the scheduler's Firecrawl credits were depleted (~10 min after successful run).

## Workaround: Direct curl + Bing HTML Scrape

When web search fails with billing error, immediately switch to curl+Bing HTML:

```bash
# Basic search
curl -s --max-time 15 "https://www.bing.com/search?q=QUERY" | grep -o '"b_lineclamp[^"]*">[^<]*' | sed 's/.*>//'

# Game-specific search
curl -s --max-time 15 "https://www.bing.com/search?q=Battlefield+6+Tsuru+Reef+alpha+leak" | grep -o '"b_lineclamp[^"]*">[^<]*' | sed 's/.*>//'

# Site-specific search
curl -s --max-time 15 "https://www.bing.com/search?q=site%3Areddit.com+Battlefield+6+Tsuru+Reef" | grep -o '"b_lineclamp[^"]*">[^<]*' | sed 's/.*>//'
```

Output is snippets from Bing's `b_lineclamp` class. Parse with `sed`/`grep`.

## Alternative: YouTube oEmbed API (No Auth)

For YouTube video metadata (title, author, duration, thumbnail):
```bash
curl "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=VIDEO_ID&format=json"
```

Returns JSON: `title`, `author_name`, `author_url`, `thumbnail_url`, `width`, `height`, `duration`.

## Alternative: yt-dlp Metadata (Used by Builder)

```bash
python -c "import yt_dlp; ydl=yt_dlp.YoutubeDL({'quiet':True}); info=ydl.extract_info('URL', download=False); print(info.get('title'), info.get('description')[:500])"
```

Returns full metadata: title, description, tags, upload_date, duration, uploader, view_count, etc.

## Agent Rule

**When web search fails with billing error, immediately switch to curl+Bing scrape. Do not retry Nous tools.** The billing error indicates exhausted credits; retries will only waste time.

## Root Cause (for future debugging)

The Hermes `web` toolset implementation calls the Nous Portal gateway directly. Config values `web.backend` and `web.use_gateway` are ignored by the tool handler. The only ways to get free search:
1. Add Firecrawl/Tavily API key to config
2. Self-host SearXNG instance
3. Use local curl+Bing/Google/DuckDuckGo scrape (shown above)

This is a tool implementation limitation, not a config issue.