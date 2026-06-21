# ASS Subtitle Positioning Notes

## Verified working placement for 720x1280 Shorts

- Preferred anchor: `Alignment=5` in the ASS Default style.
- Vertical offset: `MarginV=150`.
- Font: `Whoosh`, size `120`.
- Effect: bottom-center placement that clears the bottom navigation UI on YouTube Shorts while staying legible.

## Why this is style-driven, not per-line

Per-dialogue overrides can bypass the style line unpredictably. Use the style for positioning; avoid hardcoding alignment markers inside `Dialogue:` lines.

## Current style line

`Style: Default,Whoosh,120,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,6,1.2,5,5,5,0,0,150`

## Verification expectation

A successful ffmpeg subtitle burn exit code alone does not prove subtitle visibility. If placement is suspect, inspect one frame after render and confirm caption visibility before declaring success.
