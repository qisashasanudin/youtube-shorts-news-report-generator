# Stale captions.ass Sync Issue (2026-06-08)

## Issue
After updating `subtitle.txt` in an existing work dir, `captions/captions.ass` remained unchanged. This means the builder did not detect that the burned caption file was stale.

## Impact
Final MP4 delivery can be inconsistent if `captions.ass`, `audio/voiceover.mp3`, and the MP4 mtime are not compared before reporting success.

## Fix
Always inspect `captions.ass`, `audio/voiceover.mp3`, and `clips/reordered.mp4` relative to the final MP4 in `videos/TO_UPLOAD/`. If any input artifact predates the MP4, treat the render as stale and rebuild before claiming done.
