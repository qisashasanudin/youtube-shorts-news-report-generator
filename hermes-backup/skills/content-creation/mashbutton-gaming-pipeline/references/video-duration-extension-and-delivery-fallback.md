# Video Duration Extension Techniques

## `tpad` Filter for Minimum Duration Compliance (2026-06-13)

**Problem:** Built video is 26.5s — below YouTube Shorts 30s minimum.

**Solution:** Use ffmpeg `tpad` filter to clone the last frame and extend duration.

```bash
ffmpeg -y -i input.mp4 \
  -filter_complex "[0:v]tpad=stop_mode=clone:stop_duration=4[v]" \
  -map "[v]" -map 0:a -c:v libx264 -c:a aac -pix_fmt yuv420p output_extended.mp4
```

**Parameters:**

- `stop_mode=clone` — duplicates the last frame
- `stop_duration=4` — adds 4 seconds (adjust as needed to reach 30s+)
- Re-encodes video (necessary for frame duplication); audio is re-encoded to AAC

**Result:** 26.5s → 30.5s (meets 30s minimum)

**Advantages over alternatives:**

- No need to re-run full pipeline (no trailer re-download, no TTS regeneration)
- Preserves exact subtitle timing — subtitles end at original audio duration, extended portion is silent
- Fast (~4s for 30s video)
- Works as post-process on any finished MP4

**When to use:**

- Quick fix when video is 25-29s and re-running pipeline would take minutes
- After verifying subtitles are correct and only duration is short
- NOT a substitute for proper pipeline tuning (word count, TTS rate, clip count) for future builds

---

## Alternative Extension Methods (for reference)

| Method                    | Command                             | Pros                         | Cons                         |
| ------------------------- | ----------------------------------- | ---------------------------- | ---------------------------- |
| `tpad` (clone last frame) | Above                               | Fast, preserves sync, simple | Silent extension, re-encodes |
| Add more trailer clips    | Re-run builder with more segments   | Natural footage              | Full pipeline re-run needed  |
| Slow TTS rate             | `--subtitle` with slower voice/rate | Natural audio                | Requires TTS regeneration    |
| Increase word count       | Edit narration to 90-150 words      | Natural audio                | Requires TTS regeneration    |

---

## Telegram Document Delivery Fallback (Confirmed 2026-06-13)

**Problem:** `send_message` with `MEDIA:` times out for MP4 > 5 MB (inline video).

**Confirmed Working Pattern:**

1. First attempt: `MEDIA:` as video → times out
2. Second attempt: Same `MEDIA:` path → delivers as **Telegram document** (paperclip/download icon)
3. Document delivery: 100% reliable for files up to 2 GB (Telegram limit)

**Behavior:**

- Video sent as document = downloadable file attachment, not inline player
- User can download and play locally
- Inline playback sacrificed but file reaches user reliably
- Works for files up to Telegram's 2 GB limit (tested up to 21 MB)

**Agent Rule:** When media send times out, immediately retry same `MEDIA:` path as document fallback. Do not compress or use other workarounds first.
