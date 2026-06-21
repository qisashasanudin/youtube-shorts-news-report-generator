# ASS Burn Verification Notes (2026-06-06)

- Burned ASS subtitles via ffmpeg `ass='...'` render as video-frame overlay.
- Expected ffprobe result for a correctly burned short: `h264` video + `aac` audio only.
- A missing subtitle stream in ffprobe is **not** evidence of a failed subtitle burn.
- Use visual inspection or subtitle OCR to confirm rendered captions.
- If captions are missing from frames, check ASS path escaping and font-family match first.
