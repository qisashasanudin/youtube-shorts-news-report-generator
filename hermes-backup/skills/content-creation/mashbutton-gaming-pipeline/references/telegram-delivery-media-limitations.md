# Telegram Media Delivery Limitations

## Issue Summary

When sending MP4 videos > 5 MB via `send_message` with `MEDIA:<absolute_path>`:
- Hermes gateway returns `success: true` and a message ID
- But the video often **does not appear** in the user's chat (neither inline nor as file attachment)
- Text/caption portions may arrive successfully while the media silently fails
- This is a platform/media-gateway limitation, not a file/path error

## Observed Behavior (Session 2026-06-09)

| File | Size | Attempts | Result |
|------|------|----------|--------|
| Original TERMINAL_WAR | 5.1 MB | 4 | API success, user sees nothing |
| /tmp copy | 5.1 MB | 2 | API success, user sees nothing |
| Compressed 480p | ~1.5 MB | 1 | API success, user sees nothing |
| Text-only test | N/A | 2 | ✅ Arrives instantly |

## User-Side Verification Checklist

When delivery appears to fail:
1. **Check for paperclip/file icon** — large MP4s often render as downloadable files, not inline video
2. **Open Telegram Web** (web.telegram.org) — often shows media the mobile app hides
3. **Restart Telegram app** or clear cache
4. **Verify same account** receiving the DMs

## Workarounds

1. **Provide local absolute path** for manual drag-and-drop — 100% reliable
2. **Send as Telegram document (fallback)** — when `MEDIA:` times out, resend the same path; Telegram delivers as downloadable file attachment (paperclip icon) which is reliable for MP4s > 5 MB
3. **Compress to 480p** (~1-2 MB) before sending:
   ```bash
   ffmpeg -i input.mp4 -vf "scale=480:854" -c:v libx264 -crf 28 -preset fast -c:a aac -b:a 64k output.mp4
   ```
4. **Manual upload with explicit permission** — user runs upload themselves
5. **Split into chunks** if platform limit is confirmed

## Confirmed Document Fallback Pattern (2026-06-11, re-verified 2026-06-13)

| File | Size | Media Send | Document Send |
|------|------|------------|---------------|
| HAEX Short | 6.5 MB | ❌ Timeout | ✅ Success |
| Warzone EOS Short | 15 MB | ❌ Timeout | ✅ Success |
| Ghost Recon Project OVR | 6.0 MB | ❌ Timeout | ✅ Success |

**Pattern:** Same `MEDIA:/absolute/path` — first attempt times out as inline video, second attempt delivers as **Telegram document** (paperclip icon). Document delivery preserves file for user download; inline playback sacrificed but deliverable reaches user.

**Agent Rule:** When media send times out, immediately retry same `MEDIA:` path as document fallback. Do not compress or use other workarounds first.

---

## "No deliverable text or media remained" Error (2026-06-13)

**Symptom:** `send_message` with only `MEDIA:<path>` returns:
```
{"error": "No deliverable text or media remained after processing MEDIA tags"}
```

**Root Cause:** Telegram gateway requires at least some text content alongside the media tag when sending as inline video.

**Fix:** Prepend any text before the `MEDIA:` tag:
```bash
# Fails
MEDIA:/path/to/video.mp4

# Works
Video: MEDIA:/path/to/video.mp4
# or
Here is the file: MEDIA:/path/to/video.mp4
```

**Agent Rule:** Always include a text prefix (even minimal like "Video:") when sending `MEDIA:` tags. If the error occurs, retry immediately with text prefix.

---

## External Mirror Fallback: tmpfiles.org (2026-06-13)

When both inline video and document send fail (or user cannot see the file):

1. Upload to tmpfiles.org via curl:
   ```bash
   curl -F "file=@/absolute/path/to/video.mp4" https://tmpfiles.org/api/v1/upload
   ```
2. Response provides a direct download URL:
   ```
   https://tmpfiles.org/wrwPMcfP60x6/video_name.mp4
   ```
3. Send the URL to user via text message — no platform media gateway involved.

**Advantages:**
- Bypasses Telegram media delivery entirely
- Works for files up to tmpfiles.org limit (~100 MB)
- Direct download, no platform processing
- User can save immediately on any device

**Agent Rule:** After document fallback fails or user reports missing file, offer tmpfiles.org link as guaranteed backup. Do not re-retry platform delivery.

## Agent Behavior Rules

- Do NOT blind-retry identical media sends
- Surface the exact verified local file path ONCE, then stop
- Do NOT claim "sent" or "delivered" if only caption text arrived
- If API returns success but user reports missing video, treat as delivery failure
- Offer workarounds immediately rather than re-sending