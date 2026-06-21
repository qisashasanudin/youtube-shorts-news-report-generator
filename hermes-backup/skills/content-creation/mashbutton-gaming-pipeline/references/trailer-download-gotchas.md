# Trailer Download Gotchas (Added 2026-06-11)

## yt-dlp Command Not Found

In the project's Windows `.venv`, the `yt-dlp` console script may not be on PATH. Use module invocation instead:

```bash
python -m yt_dlp [args...]
```

The unified builder (`src/shorts_builder.py`) handles this internally via `YoutubeDL` Python API, but manual downloads for testing should use `python -m yt_dlp`.

## Builder Argument Format

The unified entrypoint requires exactly three arguments:

```bash
.venv\Scripts\python.exe src\shorts_builder.py --youtube "URL" --title "Exact Title" --subtitle "Narration text 50-100 words"
```

**Common mistakes:**
- ❌ `--trailer` instead of `--youtube`
- ❌ `--narration` instead of `--subtitle`
- ❌ `--output` instead of letting the builder derive output from `--title`

## AV1 Codec from YouTube (2026-06-11)

YouTube now serves AV1 (av01) video streams for 1080p content. The pipeline handles this but ffmpeg emits **non-monotonic DTS warnings** during the reordered concat stage:

```
[vost#0:0/copy @ ...] Non-monotonic DTS; previous: 1501536, current: 1431629; changing to 1501537.
```

These warnings are benign — the final render completes successfully at 30+ seconds with correct A/V sync. No action needed unless the final MP4 has visible sync issues.

## Telegram Document Fallback (2026-06-11)

When `send_message` with `MEDIA:<path>` times out for MP4s > 5 MB, resend the **same MEDIA tag** — Telegram delivers as a downloadable document (paperclip icon) instead of inline video. This is reliable and should be the standard fallback.