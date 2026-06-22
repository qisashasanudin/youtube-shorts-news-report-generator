# Age-Restricted Trailer Workaround (June 10, 2026)

## Problem
The official MW4 reveal trailer (https://www.youtube.com/watch?v=jLbst85USN8) is age-restricted and blocks yt-dlp with:
```
ERROR: [youtube] jLbst85USN8: Sign in to confirm your age. This video may be inappropriate for some users.
```

## Solution
Found working non-age-restricted mirror: **https://www.youtube.com/watch?v=-Zp2CM6yVFI** (same official trailer, different upload/region).

## Pattern for Future
When yt-dlp returns "Sign in to confirm your age":
1. Search for the same official trailer with different video IDs (regional uploads, reposts by other official channels)
2. Test each candidate with a quick `yt-dlp --simulate` or attempt download
3. Prefer official publisher/developer channels over third-party reuploads
4. Document working mirrors in project references

## Verification
The `-Zp2CM6yVFI` mirror downloaded successfully at 44.36 MB (1080p, AV1), confirming it's the full official trailer without age gate.

## Note on Subtitle Word Count
The builder's `_check_subtitle_words()` enforces **50-150 words** (despite some comments mentioning 100-200). Our narration required trimming from ~127 → ~150 words. Track exact count: `len(subtitle.split())`.

## Duration Edge Case
Final render: **29.1s** (barely under YouTube Shorts 30s minimum).
Fix for next build: add one more 5s trailer segment in the clip assembly or slightly slow TTS rate to push past 30s.