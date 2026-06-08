# MashButtonGaming YouTube Shorts News Generator

One-shot builder for vertical game news Shorts from official trailer footage. The pipeline produces a ready-to-upload MP4 and posts a proposal to Telegram for approval before any build or upload.

## Platform Priority

- **TikTok**: primary platform. Target aggressive posting cadence for growth.
- **YouTube Shorts**: secondary/selective uploads. Use only for high-signal stories (score >= 75).
- Same finished video asset can be reused across both platforms.

## Project Layout

- `src/shorts_builder.py` — unified renderer. Downloads trailer, generates TTS narration, builds captions, selects shuffled trailer chunks, and outputs the final MP4.
- `src/editorial_state.py` — tracks used stories and per-day upload counts.
- `src/scripts/youtube_upload.py` — manual upload helper for YouTube.
- `src/scripts/tiktok_upload.py` — generates TikTok-ready metadata package from an existing MP4.
- `videos/TO_UPLOAD/` — final MP4 output with a clean title-based filename.
- `videos/tiktok_meta/` — TikTok metadata JSON packages ready for manual/assisted upload.
- `editorial_state.json` — editorial ledger.

## Workflow

1. Scheduler proposes one fresh gaming news story on Telegram: trailer URL, title, 50–100 word subtitle, story score, and target platform(s).
2. Wait for explicit approval before building.
3. Build the Short with `src/shorts_builder.py`.
4. Send the finished MP4 to Telegram.
5. Generate TikTok upload package with `src/scripts/tiktok_upload.py`.
6. Upload to TikTok immediately when ready.
7. Upload to YouTube only when explicitly approved and story score is high enough.

## Editorial Rules

- Trailer sources must be official. Prefer reveal, then gameplay, then update, then developer video.
- Maximum source trailer size: 500 MB.
- Story freshness limit: 48 hours.
- Deduplicate against `editorial_state.json`.
- TikTok daily target: 6–8 posts/day when story supply allows.
- YouTube daily cap: 3–4/day for the first 30 days on the channel.

## Script Requirements

- Subtitle text must be 50–100 words to keep narration duration aimed closer to 20s for better view-to-swipe performance.
- Title style is sensational, concise, and news-oriented. It must clearly mention the franchise or key terms.
- The final MP4 filename must match the title text.
- Hashtags must not appear in the YouTube title; moved to description/tags instead.

## Scheduler Behavior

- The scheduler runs every 2 hours during 08:00–22:00.
- It proposes one candidate on Telegram, then stops.
- Do not auto-build or auto-upload from the scheduler.

## Upload Helper Notes

- `youtube_upload.py` is manual-first. Default privacy is private.
- `tiktok_upload.py` generates a metadata package. TikTok upload may still require manual/assisted posting or an approved TikTok developer integration.
- Hashtags are stripped from the YouTube title and moved into the description plus tags fields to keep click-focused titles clean.
- If `client_secrets.json` or `token.json` is missing or missing scopes, the uploader cannot run until OAuth is repaired.
