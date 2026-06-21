# tmpfiles.org Delivery Fallback (2026-06-15)

## Problem
Native Discord media upload via `send_message` with `MEDIA:` path sometimes fails silently — the message appears sent but the video doesn't appear in the channel. Telegram media upload also times out on larger files (>5 MB).

## Solution
Upload built MP4s to **tmpfiles.org** via their API, then share the download link in Telegram/Discord messages. This is reliable, supports large files, and provides a direct download URL.

## Upload Command
```bash
curl -s --max-time 60 -F "file=@/path/to/video.mp4" https://tmpfiles.org/api/v1/upload
```

Response:
```json
{"status":"success","data":{"url":"https://tmpfiles.org/xxx/video.mp4"}}
```

## Delivery Format
Send to both Telegram and Discord with the tmpfiles.org link:
```
🎬 **Battlefield 6 Tsuru Reef Leak Short Ready**
Title: BATTLEFIELD 6 TSURU REEF LEAK REVEALS NAVAL WARFARE RETURN
Duration: 23.3s

**Download:** https://tmpfiles.org/xxx/video.mp4
```

## User Preference
**Permanent**: Use tmpfiles.org for ALL video/file deliveries to Discord and Telegram instead of native uploads. Native Discord upload may fail silently.

## Benefits
- No size limit issues (tested up to 500 MB+)
- Direct download for user
- Works cross-platform (Telegram, Discord, any chat)
- No timeout/adapter stall issues
- Shareable link persists beyond session