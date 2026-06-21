# MashButtonGaming YouTube Shorts News Generator

One-shot builder for vertical game news Shorts from official trailer footage.
The pipeline produces a ready-to-upload MP4 from three inputs: trailer URL, title, and 50–100 word narration.

## Platform Priority

- **TikTok**: primary platform. Target aggressive posting cadence for growth.
- **YouTube Shorts**: secondary/selective uploads. Use only for high-signal stories.
- Same finished video asset can be reused across both platforms.

## Project Layout

- `src/shorts_builder.py` — **single unified renderer**. Downloads trailer via yt-dlp, generates TTS narration (edge-tts Brian +25%), builds word-level ASS captions via faster-whisper, selects shuffled 5s trailer chunks, and outputs the final 720×1280 MP4.
- `src/editorial_state.py` — tracks used stories and per-day upload counts.
- `src/scripts/youtube_upload.py` — manual upload helper for YouTube.
- `src/scripts/tiktok_upload.py` — generates TikTok-ready metadata package from an existing MP4.
- `videos/TO_UPLOAD/` — final MP4 output with a clean title-based filename.
- `videos/tiktok_meta/` — TikTok metadata JSON packages ready for manual/assisted upload.
- `editorial_state.json` — editorial ledger (gitignored).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  HERMES CRON (job 80c55b5a2392) — runs 4×/day               │
│  → browser_navigate → Bing News (CDP on port 9222)          │
│  → extracts 10 fresh shooter/FPS stories                   │
│  → delivers formatted list to Discord                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (you pick one in Discord)
┌─────────────────────────────────────────────────────────────┐
│  python src/shorts_builder.py                               │
│    --youtube "https://youtu.be/..."                         │
│    --title "BOMBASTIC CLICKBAIT TITLE"                      │
│    --subtitle "50-100 word narration, plain words..."       │
│  → videos/TO_UPLOAD/{TITLE}.mp4 (720×1280, subs + audio)    │
└─────────────────────────────────────────────────────────────┘
```

**No web search logic in source code** — all search is handled by Hermes gateway CDP in cron jobs.
**Single source file**: `src/shorts_builder.py` (527 lines).

## Workflow

1. Hermes cron delivers 10 candidate stories to Discord (09:00, 12:00, 15:00, 18:00).
2. You pick one story from the list.
3. Run the builder with 3 inputs:
   ```bash
   python src/shorts_builder.py --youtube "<url>" --title "<TITLE>" --subtitle "<50-150 words>"
   ```
4. Finished MP4 lands in `videos/TO_UPLOAD/`.
5. (Optional) Upload to TikTok/YouTube via helper scripts.

## Editorial Rules

- Trailer sources must be official. Prefer reveal → gameplay → update → dev video.
- Maximum source trailer size: 500 MB.
- Story freshness limit: 7 days (enforced by Hermes search query).
- Deduplicate against `editorial_state.json`.
- Subtitle text: **50–100 words** (for ~20s narration, better view-to-swipe).
- Title: bombastic, sensorial, clickbaity — mention franchise/key terms.
- Final MP4 filename matches the title text.
- Hashtags stripped from YouTube title → moved to description/tags.

## Scheduler Behavior

- Cron job `80c55b5a2392` runs 4×/day via Hermes agent (browser toolset).
- Uses Hermes CDP (Edge headless on port 9222) for Bing News search.
- No local search code in repo — all web search is gateway-managed.
- Delivers story list to Discord for human selection.

## Upload Helper Notes

- `youtube_upload.py` is manual-first. Default privacy: private.
- `tiktok_upload.py` generates a metadata package.
- Hashtags removed from YouTube title, moved to description + tags.
- Requires `client_secrets.json` and `token.json` for OAuth.
