# Copy-Mode Assembly Fix

## Problem
- Direct builder runs timed out during the final concat/render stage.
- The bottleneck was multiple full re-encode passes in `build_segmented_edit()`:
  - chunk extraction with `ultrafast / CRF 28`
  - concat merge with `veryfast / CRF 18`
  - optional trim pass with `veryfast / CRF 18`
- Combined with 4K source footage, these CPU-heavy encodes exceeded the terminal timeout and caused repeated build failures.

## Fix
Change all three edit-stage ffmpeg invocations in `build_segmented_edit()` to stream copy:
- chunk extraction: `-c copy -an`
- concat: `-f concat -safe 0 -c copy -an`
- trim: `-t <duration> -c copy`

Only the final subtitle burn still re-encodes once to 720x1280 H.264; that is the only required transcode.

## Evidence
- Before: timeout after ~600s, `reordered.mp4` never finished (stalled at ~9.71s elapsed).
- After: build completed successfully; final MP4 = `53.450s`, `27.76 MB`.
- Concat/trim passes now run at ~247x-249x speed because they are stream copies.

## Tradeoffs
- Pro: Eliminates CPU re-encode bottleneck completely.
- Pro: Source quality preserved until final burn stage.
- Con: Stream copy cannot fix broken timestamps or transcode to a different codec during edit-stage assembly.
- Con: Final burn stage is still the only quality-controlled transcode.

## Implementation
Patched `src/shorts_builder.py`:
- Removed all `-c:v libx264 -preset ... -crf ... -pix_fmt yuv420p` blocks from chunk extraction, concat, and trim.
- Replaced with `-c copy` (and `-an` for audio-less intermediate files).
- Committed and pushed to `master` (commit `f885d34`).
