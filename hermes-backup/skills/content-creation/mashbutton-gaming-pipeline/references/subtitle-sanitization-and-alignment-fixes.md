# Subtitle Sanitization and Alignment Fixes

## Problem
Hyphenated/dashed subtitle text caused caption sync drift because:
- Hyphens collapse into single tokens in some TTS/STT flows
- Word counts and token boundaries no longer match the caption alignment window
- Long-tail mismatch clusters accumulated timing error across 100–200 word narrations

## Fix Applied (2026-06-07)
- Added `_sanitize_subtitle()` in `src/shorts_builder.py`
- Replaced dashes with spaces before word-count checks
- Applied immediately after CLI arg parse

## Rule of Thumb
If captions are visually off-sync in long-form narration, inspect the raw `--subtitle` text for dashes/hyphens before tweaking matcher thresholds.

## Caption Source Split (2026-06-07)
Use hand-written `--subtitle` strictly for TTS audio. For on-screen captions, use `faster-whisper` STT word tokens from the generated voiceover.

## Alignment Rule (2026-06-07)
Advance the Whisper token cursor exactly +1 for every displayed word. Match when possible, fall back to the current token's timing when not. Do not insert hardcoded engagement text, hooks, or filler inside the builder; `--subtitle` remains the single source of truth for narration only.

## Verified Output
- `PROLOGUE GO WAYBACK HALTED` — 46.800s, 6.2 MB
- Caption key terms present: `HALTED.`, `GREENE`, `PLAYERUNKNOWN`, `MELBA`, `STUDIO`
- Rebuilt `RTX SPARK UNVEILED` after default voice revert to `en-US-RogerNeural`; final output confirmed in `videos/TO_UPLOAD/rtx-spark-unveiled.mp4`

## Silent Subtitles And Driver Path (2026-06-07)
On Windows, ffmpeg may report success and show no visible subtitles after `_render_burn_subs()` because the subtitle burn happens in a separate command from the driver filter string and can bypass the intended `[v]`/reorder branch.
Avoid assuming subtitles are invisible because of ASS data. Fix the rendering flow to create the driver-filtered video with `[v]`, then render the subtitle burn from that path in a separate pass.