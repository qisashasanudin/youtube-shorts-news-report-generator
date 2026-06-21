# Work Directory Caching & Minimum Duration Notes

## Work Directory Caching Issue (2026-06-09)

**Problem:** The unified builder (`src/shorts_builder.py`) creates work directories named `videos/<DATE>-<SLUGIFIED_TITLE>/`. When rebuilding with the same title on the same calendar day:
- The existing work directory is reused
- Any cached `clips/trailer_full.mp4` from the previous run is reused
- The new `--youtube` URL is IGNORED — the builder skips download if `trailer_full.mp4` exists

**Symptom:** User requested Season 2 Gameplay Trailer (`cyIEnxicey8`) but builder used cached Season 2 Cinematic Trailer (`a1i801SDrJA`) because the title was identical.

**Fix Options:**
1. Delete the work directory before rebuilding:
   ```bash
   rm -rf "videos/2026-06-09-MARATHON_SEASON_2_LAUNCH_DISASTER_..."
   ```
2. Append a differentiator to the title (e.g., `_GAMEPLAY`, `_V2`) to force a fresh work directory
3. The builder does NOT re-download if `trailer_full.mp4` already exists in the work dir

**Prevention:** Before invoking the builder with a trailer change, either delete the stale work dir or modify the title slightly.

---

## YouTube Shorts Minimum Duration (2026-06-09)

**Problem:** Current pipeline output ~23.9 seconds — below YouTube Shorts platform minimum of 30 seconds.

**Root Cause:** The 82-word narration at current TTS rate (+25% edge-tts) produces ~23.9s audio. The shuffled trailer clips are trimmed to match audio duration exactly.

**Fix Options:**
1. Increase word count toward 100-word upper bound
2. Reduce TTS rate (remove `+25%` or use slower voice)
3. Add more trailer segments (increase clip pool or reduce clip length)
4. The builder should enforce `duration >= 30s` as a hard gate before final render verification

**Verification:** Output verification checklist now includes explicit duration >= 30s check.

---

## Quick Fix: `tpad` Filter for Post-Build Extension (2026-06-13)

**Problem:** Built video is 26.5s — below 30s minimum, but subtitles and content are correct. Re-running full pipeline would take minutes.

**Solution:** Use ffmpeg `tpad` filter to clone last frame and extend duration without re-running pipeline.

```bash
ffmpeg -y -i input.mp4 \
  -filter_complex "[0:v]tpad=stop_mode=clone:stop_duration=4[v]" \
  -map "[v]" -map 0:a -c:v libx264 -c:a aac -pix_fmt yuv420p output_extended.mp4
```

**Parameters:**
- `stop_mode=clone` — duplicates the last frame
- `stop_duration=4` — adds 4 seconds (adjust to reach 30s+)
- Re-encodes video; audio re-encoded to AAC

**Result:** 26.5s → 30.5s (meets 30s minimum)

**Advantages:**
- No trailer re-download, no TTS regeneration, no subtitle rebuild
- Preserves exact subtitle timing — subtitles end at original audio duration
- Fast (~4s for 30s video)
- Works as post-process on any finished MP4

**When to use:**
- Quick fix when video is 25-29s and re-running pipeline would take minutes
- After verifying subtitles are correct and only duration is short
- NOT a substitute for proper pipeline tuning (word count, TTS rate, clip count) for future builds

**See also:** `references/video-duration-extension-and-delivery-fallback.md` for full documentation including Telegram document delivery fallback.