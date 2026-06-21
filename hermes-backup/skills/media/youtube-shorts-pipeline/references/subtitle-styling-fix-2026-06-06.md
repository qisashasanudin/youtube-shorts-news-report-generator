# Subtitle styling fix: ASS base style vs inline overrides

## Problem
Captions rendered too small and plain, even though `force_style` in the ffmpeg filter tried to set large bold text.

## Root cause
The generated ASS had contradictory styling:
- Base `Style:` line used tiny font size (`10`) and thin outline (`1.5`)
- Per-cue event lines added inline overrides like `{\bord2.5\fs20\b1\3a&H00&}`
- ffmpeg/libass also passed `force_style='FontSize=64,Outline=2,...'`

These three layers fought each other. The result was small, plain captions.

## Fix applied
Make the ASS base style the single source of truth for subtitle appearance:
- Raise base style font size to `64`
- Set outline to `2.5`, shadow to `0.3`, alignment `2` (bottom-center)
- Keep bold flag `-1` in the style line
- Remove inline per-cue overrides entirely; event text is now just `WORD`
- Keep `fontsdir=assets/fonts/whoosh` on the ffmpeg subtitles filter
- `force_style` can stay as a safety net, but the ASS style line now carries the real values

## Verified
After the fix, a mid-video frame check at an active cue timestamp showed visible large white text at the bottom of the frame, matching the channel's intended Whoosh-style caption look.

## Lessons
- ASS-first styling is more reliable than mixing inline overrides + `force_style` + tiny base style.
- When subtitles look wrong, inspect the rendered ASS first, then a rendered frame at a known cue time.
- Do not verify subtitle presence with `ffprobe` stream listings; burned captions are part of video frames.
