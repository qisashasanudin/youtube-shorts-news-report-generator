# Fact Verification Methodology for Gaming Leaks (2026-06-15)

## Overview

When writing narration for leaked gaming content (trailers, dataminer reports, alpha/beta footage), **never trust hallucinated facts**. Use this three-source verification chain before publishing.

## Source Chain (Best → Good → Fallback)

### 1. YouTube oEmbed API — No Auth, Instant
**Use for:** Confirming video title, author, duration, thumbnail, upload date.
**Limit:** No description/tags access.

```bash
curl "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=VIDEO_ID&format=json"
```

Returns JSON:
```json
{
  "title": "TSURU REEF GAMEPLAY (BF6 LEAKS)",
  "author_name": "BattlefieldGlazer",
  "author_url": "https://www.youtube.com/@BattlefieldGlazer",
  "thumbnail_url": "https://i.ytimg.com/vi/7zOMLsmghbg/hqdefault.jpg",
  "width": 480,
  "height": 360,
  "duration": 469
}
```

**Used in session 2026-06-15:** Confirmed "TSURU REEF GAMEPLAY (BF6 LEAKS)" by BattlefieldGlazer, uploaded 2026-06-11, 7:49 duration.

### 2. yt-dlp Metadata — Full YouTube Data
**Use for:** Complete metadata — description, tags, upload date, duration, uploader, view count.

```bash
python -c "import yt_dlp; ydl=yt_dlp.YoutubeDL({'quiet':True}); info=ydl.extract_info('URL', download=False); print(info.get('title'), info.get('description')[:500])"
```

Returns full dict with:
- `title`, `description`, `tags`, `upload_date`, `duration`, `uploader`, `view_count`, `like_count`, `comment_count`
- `tags` array includes all YouTube tags (e.g., `['bf6', 'battlefield 6', 'naval', 'bf6 naval warfare', 'bf6 leaks', 'battlefield 6 leaks', 'bf6 new map', 'bf6 tsuru reef', 'bf6 Tsuru reef', 'Battlefield 6 Tsuru Reef']`)

**Used in session 2026-06-15:** Extracted tags confirming "naval warfare", "tsuru reef", "bf6 leaks" — the exact keywords for the Short.

### 3. Bing HTML Scrape — When Web Search Fails
**Use for:** Web search when Nous Firecrawl credits exhausted.

```bash
curl -s --max-time 15 "https://www.bing.com/search?q=QUERY" | grep -o '"b_lineclamp[^"]*">[^<]*' | sed 's/.*>//'
```

**Used in session 2026-06-15:** Verified Battlefield 6 map names, community sentiment on Orbital/Hourglass/Fjell 652 as flops.

## Session 2026-06-15 Application: Battlefield 6 Tsuru Reef

| Claim | Source | Verified |
|-------|--------|----------|
| Map name: Tsuru Reef | YouTube oEmbed + yt-dlp tags | ✅ |
| Naval warfare returning | yt-dlp tags (`naval`, `bf6 naval warfare`) | ✅ |
| First naval since BF4 | Community knowledge + yt-dlp `bf3`, `battlefield 3` tags | ✅ |
| "Season 4" in narration | **User-provided** — not verified from source | ⚠️ |
| Hotel building from Hainan Resort | **User-provided** — not verified from source | ⚠️ |
| Flop comparison: Orbital | Community consensus (Bing scrape) | ✅ |

## Anti-Hallucination Rules

1. **Never fabricate game names, dates, or features.** If a comparison is needed, use verified real examples. If uncertain, omit the comparison.
2. **Halucinations caught in this session:** "Giants of Karelia" (fake BF map), "Season 4" (not in source), "Exact same hotel building" (not in source).
3. **Mark unverified claims explicitly** in narration draft before user review.
4. **User is the final fact-checker** — they caught "Giants of Karelia" and corrected "Season 4" placement.

## Verification Checklist Before Drafting Narration

- [ ] YouTube oEmbed confirms video title/author/date
- [ ] yt-dlp tags/description confirm key keywords (map names, modes, features)
- [ ] Map names cross-referenced with known game maps
- [ ] Flop/success comparisons use real maps from same franchise
- [ ] "Season X" / version numbers verified from official roadmap or patch notes
- [ ] All hardware/performance claims sourced from official specs or Digital Foundry
- [ ] Narrative draft marks unverified claims for user review

## Quick Commands Cheat Sheet

```bash
# 1. YouTube oEmbed (fastest)
curl "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=7zOMLsmghbg&format=json"

# 2. yt-dlp full metadata
python -c "import yt_dlp; ydl=yt_dlp.YoutubeDL({'quiet':True}); info=ydl.extract_info('https://www.youtube.com/watch?v=7zOMLsmghbg', download=False); print('Title:', info.get('title')); print('Upload:', info.get('upload_date')); print('Duration:', info.get('duration')); print('Tags:', info.get('tags', [])[:20])"

# 3. Bing scrape for community sentiment
curl -s --max-time 15 "https://www.bing.com/search?q=Battlefield+6+Orbital+map+reaction" | grep -o '"b_lineclamp[^"]*">[^<]*' | sed 's/.*>//' | head -10
```