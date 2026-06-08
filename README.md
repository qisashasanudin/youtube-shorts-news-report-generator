# MashButtonGaming YouTube Shorts News Generator

One-shot builder for vertical game news Shorts from official trailer footage. The pipeline produces a ready-to-upload MP4 and posts a proposal to Telegram for approval before any build or upload.

## Project Layout

- `src/shorts_builder.py` — unified renderer. Downloads the trailer, generates TTS narration, builds captions, selects shuffled trailer chunks, and outputs the final MP4.
- `src/editorial_state.py` — tracks used stories and per-day upload counts.
- `src/scripts/youtube_upload.py` — optional manual upload helper for YouTube.
- `videos/TO_UPLOAD/` — final MP4 output with a clean title-based filename.
- `editorial_state.json` — editorial ledger.

## Workflow

1. Propose exactly one fresh gaming news story on Telegram: trailer URL, title, and 50–100 word subtitle.
2. Wait for explicit approval.
3. Build the Short with `src/shorts_builder.py`.
4. Send the finished MP4 to Telegram.
5. Upload to YouTube only when explicitly approved.

## Editorial Rules

- Trailer sources must be official. Prefer reveal, then gameplay, then update, then developer video.
- Maximum source trailer size: 500 MB.
- Story freshness limit: 72 hours.
- Deduplicate against `editorial_state.json`.
- Daily capacity for new uploads is capped.

## Script Requirements

- Subtitle text must be 50–100 words to keep narration duration aimed closer to 20s for better view-to-swipe performance.
- Opening ends with: "...and here's what you need to know."
- Closing starts with: "but what do you think?" and ends with an open-ended question.
- Title style is sensational, concise, and news-oriented. It must clearly mention the franchise or key terms.
- The final MP4 filename must match the title text, with hashtags included in the filename when useful for organization.
- Never place the phrase "and here's what you need to know" in the final MP4 filename.

## Scheduler Behavior

- The scheduler runs once per day at 20:00.
- It proposes one candidate on Telegram, then stops.
- Do not auto-build or auto-upload from the scheduler.

## Upload Helper Notes

- `youtube_upload.py` is manual-first.
- Default privacy is private.
- Hashtags are stripped from the YouTube title and moved into the description plus tags fields to keep click-focused titles clean.
- If `client_secrets.json` or `token.json` is missing or missing scopes, the uploader cannot run until OAuth is repaired.
