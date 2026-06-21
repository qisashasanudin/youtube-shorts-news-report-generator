# Subtitle Rendering Debug — Tomb Raider short

Project: `shorts/2026-06-06-tomb-raider-legacy-of-atlantis`
Evidence date: 2026-06-05

## Asserted fact confirmed

Subtitles are **visibly absent** in rendered MP4 despite successful subtitle layer attachment and local font file loading.

## ffmpeg/libass debug evidence

```
[Parsed_ass_0] Loading font file '.../render\\burbank_big_condensed.otf'
[Parsed_ass_0] Added subtitle file: '.../render/captions.ass' (2 styles, 140 events)
[Parsed_ass_0] Using font provider directwrite (with GDI)
fontselect: (Burbank Big Condensed, 700, 0) -> Arial-BoldMT, 0, Arial-BoldMT
```

`Added subtitle file:` confirms the ASS parser loaded successfully. `fontselect` resolves the requested Burbank style to `Arial-BoldMT`, which means the OTF's internal family/style names do not match `Burbank Big Condensed`.

## Root cause

- `fontsdir` pointing to `<project>/render/` works and the OTF loads.
- libass via DirectWrite+directwrite cannot resolve the glyph run because the OTF fails the family/style name match.
- Fallback substitution to Arial occurs silently; subtitle rendering produces no visible pixels in the monitored frame.

## Next required fix

Determine the OTF's actual `nameID == 1` (family) and `nameID == 4` (full name) values with `fontTools` or an equivalent OTF name table inspection, then update `SUBTITLE_FONT_NAME` in `subtitles.py` to the exact internal family name.

Without this exact internal family match, subtitle visibility cannot be restored.
