## Subtitle margin/caption position fix (2026-06-06)

Issue:
- User reported on-screen subtitles were too high/cropped at center, wanted them slightly lower.

Findings:
- `scripts/config.py` had `SUBTITLE_MARGIN_V = 0` and `SUBTITLE_ALIGNMENT = 5`, but it was ignored.
- The active render pipeline reads from `scripts/ai_channel_scripts/subtitles.py`, which hardcodes `SUBTITLE_ALIGNMENT = 2` and `SUBTITLE_MARGIN_V = 580`.
- Result: changing `config.py` did nothing; subtitles used bottom alignment with extreme bottom margin.

Fix applied:
- In `scripts/ai_channel_scripts/subtitles.py`, set `SUBTITLE_ALIGNMENT = 5` and `SUBTITLE_MARGIN_V = 180`.
- In `config.py`, also set `SUBTITLE_MARGIN_V = 60` and `SUBTITLE_ALIGNMENT = 5` to keep both files in sync.

Visual result:
- `Alignment=5` keeps subtitles centered horizontally.
- `MarginV=180` pushes text slightly below vertical center, closer to lower third without pinning it to bottom edge.

Lesson:
- When adjusting subtitle position in this project, always edit `scripts/ai_channel_scripts/subtitles.py` directly.
- `scripts/config.py` is convenient alignment but not respected by the render path.
- Rebuild render after changing ASS constants.
