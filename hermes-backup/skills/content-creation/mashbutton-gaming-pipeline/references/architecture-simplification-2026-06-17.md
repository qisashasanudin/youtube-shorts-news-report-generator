# Architecture Simplification (2026-06-17)

## Summary
Consolidated the entire pipeline to a **single builder script** (`src/shorts_builder.py`) and **externalized all web search to Hermes gateway CDP** via cron job agent mode. Removed 6 experimental scripts and 909 lines of dead code.

## Deleted Files (commit d3f9969)
| File | Lines | Reason |
|------|-------|--------|
| `src/scripts/main.py` | 328 | Auto-pipeline with local search (replaced by Hermes cron) |
| `src/scripts/mashbutton_scheduler_search.py` | 300 | Local scheduler with hardcoded queries |
| `src/scripts/search_web.py` | 281 | Generic search helper (unused after externalization) |
| `src/scripts/search_engine.py` | — | Never fully integrated |
| `src/scripts/ensure_edge_cdp.py` | — | CDP management now handled by Hermes gateway |
| `src/scripts/build_short.py` | ~200 | Experimental unified wrapper (replaced by `shorts_builder.py`) |

**Total: 6 files, ~909 lines removed**

## Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  HERMES CRON (job 80c55b5a2392) — runs 4×/day               │
│  • Agent mode: no_agent=false, enabled_toolsets=["browser","file"] │
│  • browser_navigate → Bing News (CDP on port 9222)          │
│  • Extracts 10 fresh shooter/FPS stories                   │
│  • Delivers formatted list to Discord                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (user picks one in Discord)
┌─────────────────────────────────────────────────────────────┐
│  python src/shorts_builder.py                               │
│    --youtube "https://youtu.be/..."                         │
│    --title "BOMBASTIC CLICKBAIT TITLE"                      │
│    --subtitle "50-100 word narration, plain words..."       │
│  → videos/TO_UPLOAD/{TITLE}.mp4 (720×1280, subs + audio)    │
└─────────────────────────────────────────────────────────────┘
```

## Key Principles Enforced
1. **Zero local search code** — all web search via Hermes gateway CDP
2. **Single source file** — `src/shorts_builder.py` (527 lines) is the only builder
3. **Human-in-the-loop** — Discord delivery for story selection, no auto-build/upload
4. **tmpfiles.org delivery** — primary method for Discord/Telegram (native media fails silently)
5. **Broad queries only** — no hardcoded game titles in scheduler prompts

## Cron Job Details
- **Job ID**: `80c55b5a2392`
- **Schedule**: 4×/day (09:00, 12:00, 15:00, 18:00 WIB)
- **Mode**: Agent mode with browser toolset
- **Workdir**: `C:\Users\qthas\Programming\Belajar\YouTube\youtube-shorts-news-report-generator`
- **Output**: `scheduler_output.json` (gitignored), Discord-formatted stdout

## Build Command
```bash
cd C:\Users\qthas\Programming\Belajar\YouTube\youtube-shorts-news-report-generator
.venv\Scripts\python.exe src/shorts_builder.py \
  --youtube "https://youtu.be/VIDEO_ID" \
  --title "BOMBASTIC TITLE" \
  --subtitle "50-100 words of narration with proper punctuation"
```

## Validation Checklist (Pre-Deploy)
- [ ] Final MP4 exists in `videos/TO_UPLOAD/` with size ≥ 1 MB
- [ ] Duration ≥ 30 seconds (YouTube Shorts minimum)
- [ ] Burned-in subtitles visible at active cue timestamp
- [ ] File delivered via tmpfiles.org link (not native media)

## Known Gotchas Resolved
| Issue | Resolution |
|-------|------------|
| Workdir caching reuses stale trailer | Delete `videos/<date>-<slug>/` or change title slightly |
| Hermes CDP shows `null` endpoint | Restart Hermes gateway process (laptop restart didn't reload config) |
| Browser tools fail with `Invalid CDP value: 'null'` | Use `hermes gateway status` + `tasklist \| grep -i hermes` to verify |
| Native Discord/Telegram upload fails | Use `curl -F "file=@..." https://tmpfiles.org/api/v1/upload` |
| Subtitle word count < 50 or > 100 | Builder exits immediately; enforce 50-100 range in draft |
| Age-gated trailer | Use `--extractor-args "youtube:player_client=android"` format 18 (360p) |

## Files Updated This Session
- `README.md` — architecture diagram, unified workflow, no web search in code
- `TSD.md` — updated cron job IDs, single builder, Hermes CDP → Discord flow
- `.gitignore` — runtime JSONs (`scheduler_output.json`, `editorial_state.json`, `analytics_log.json`) gitignored + purged from remote history
- `src/editorial_state.py` → `src/scripts/editorial_state.py` — moved into `src/scripts/`, fixed path resolution (`parents[2]` instead of `parents[1]`), verified CLI (`check`, `count`, `mark`) and build integration