# Age-Gated YouTube Trailer Workarounds (Validated 2026-06-11)

## Problem
Official Call of Duty / Warzone / Activision trailers are frequently age-restricted on YouTube, causing `yt-dlp` to fail with:
```
Sign in to confirm your age. This video may be inappropriate for some users.
Use --cookies-from-browser or --cookies for the authentication.
```

## Validated Workarounds (in order of preference)

### 1. Android Player Client + Format 18 (Primary)
```bash
python -m yt_dlp --extractor-args "youtube:player_client=android" \
  -f "18/best[height<=360][ext=mp4]" \
  --merge-output-format mp4 -o "trailer.%(ext)s" "URL"
```
- Bypasses age gate for most restricted videos
- Returns 360p MP4 (format 18) — acceptable for commentary/analysis fallback footage
- Used successfully for Warzone EOS commentary video (gCWqVJzTVGc), ~32 MB download

### 2. Non-Age-Restricted Commentary/Analysis Videos
Search for creator breakdowns of the same announcement:
- Query: `"Warzone PS4 Xbox One shutdown" site:youtube.com`
- Filter: Non-age-restricted, 5-15 min duration, clear game footage
- Used successfully: "CALL OF DUTY Is Taking WARZONE OFFLINE..." (gCWqVJzTVGc) — 9 min analysis with gameplay clips
- **Advantage:** Often includes more varied footage than single trailer

### 3. Regional/Alternative Official Uploads
Same official trailer may exist under different video IDs:
- Search: `"Modern Warfare 4 reveal trailer" site:youtube.com Call of Duty`
- Check: Call of Duty channel, Xbox channel, regional channels (Call of Duty UK, etc.)
- Documented working mirror for MW4: `-Zp2CM6yVFI` (see `trailer-agegate-workaround-2026-06-10.md`)

## Decision Tree
```
Is official trailer age-gated?
├── YES → Try Workaround 1 (android + format 18)
│   ├── Works → Use it (accept lower quality)
│   └── Fails → Try Workaround 2 (commentary video)
│       ├── Found good one → Use it
│       └── Not found → Try Workaround 3 (alt official upload)
│           ├── Found → Use it
│           └── Not found → ABORT: surface to user, do not proceed with bad footage
└── NO → Use official trailer with standard 1080p+ selector
```

## Quality Standards
- **Minimum:** 360p MP4 (format 18) — only for commentary fallback
- **Preferred:** 720p+ from non-gated source
- **Ideal:** 1080p+ from official trailer
- **Never:** Streamer clips, unlicensed reaction, fan edits

## Builder Integration
`src/shorts_builder.py` already attempts multi-client fallback (android → web → best). When age-gate persists:
1. Builder will fail after all attempts
2. Manual intervention required: download via Workaround 1 or 2 above
3. Place downloaded file at `videos/<workdir>/clips/trailer_full.mp4`
4. Re-run builder — it will reuse existing `trailer_full.mp4` (reuse guard)

## File Size Note
- Format 18 (360p): ~30-50 MB for 5-10 min videos — well under 500 MB limit
- Commentary videos: 20-80 MB typical — safe
- 4K official trailers: can exceed 500 MB — builder's size guard catches this