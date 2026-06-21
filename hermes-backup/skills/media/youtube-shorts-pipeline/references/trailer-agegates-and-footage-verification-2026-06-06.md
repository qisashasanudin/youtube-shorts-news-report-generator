# YouTube Shorts — Trailer Age-Gate + Footage Verification Notes (2026-06-06)

## Issue summary
- Multiple State of Play videos were **age-restricted** during this session; `yt-dlp` returned errors like `Sign in to confirm your age`.
- One downloaded "State of Play recap" video actually contained unrelated/recap graphics rather than the target game footage.

## Verified non-age-restricted source found
- Silent Hill: Townfall | State of Play: June 2026
- URL: `https://www.youtube.com/watch?v=IS7FedAUKp8`
- Format: 4.86 MiB, H.264, 640x360, 29.97 fps
- Result: download succeeded; no authentication required.

## Fallback behavior
- Fallback to another official game reveal if a target trailer is age-gated.
- PlayStation.Blog State of Play recap page lists all titles and links; use it for URL discovery when direct reveal URLs are restricted.

## Footage verification protocol
- After download, run:
  ```bash
  ffmpeg -y -ss 00:00:03 -i clips/trailer_full.mp4 -frames:v 1 -q:v 2 -update 1 render/probe_check.jpg
  ```
- Inspect extracted frame immediately with vision analysis.
- If the frame contains recap overlays, channel graphics, or non-target content, discard and try another URL from the official State of Play playlist or PlayStation.Blog deep-dive embedded player.

## Preferred render path
- Use `subtitles=` VTT burn in WSL Ubuntu ffmpeg.
- Keep ASS as a secondary fallback only when VTT path fails.
- Hard-trim final to voiceover duration with `-shortest`.
