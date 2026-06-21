# Subtitle Render Isolation — 2026-06-06

## Why this exists

User asked: "create a new subtitle script from scratch as a competitor to the existing one, then test both and compare."

This documents the MVP comparison procedure that worked when `create.py` subtitles were not visibly rendering.

## Verified reproduction workspace

Use an isolated workspace outside the project tree to avoid quoting/font lookup interference:

- Windows neutral dir: `C:\ai_channel_mvp\shorts\<slug>\compare_work\`
- Temp equivalent: `/tmp/ai_subtitle_test/` or `/tmp/compare_work/`

Copy only the render inputs:

- `scaled.mp4`
- `voiceover.mp3`
- `captions.ass` (legacy OR MVP)

Also copy the font used by the MVP for local resolution:

- e.g., `burbank_big_condensed.otf` -> render folder

## Minimal command that worked

```bash
WORK=C:/Users/qthas/ai_channel_compare
mkdir -p "$WORK/render"
PROJECT=C:/Users/qthas/Videos/Youtube Projects/AI Channel/shorts/2026-06-06-tomb-raider-legacy-of-atlantis

cp "$PROJECT/output_tmp/scaled.mp4" "$WORK/scaled.mp4"
cp "$PROJECT/audio/voiceover.mp3"   "$WORK/voiceover.mp3"
cp "$PROJECT/render/compare_mvp.ass" "$WORK/render/captions.ass"

cd "$WORK/render"
ffmpeg -y -i "$WORK/scaled.mp4" -i "$WORK/voiceover.mp3" \
  -filter_complex "[0:v]ass=captions.ass:fontsdir='$PWD',pad=720:1280:(720-iw)/2:0:color=black[outv]" \
  -map "[outv]" -map 1:a -c:v libx264 -preset veryfast -crf 20 -c:a aac -b:a 192k -shortest "$WORK/render/compare_mvp.mp4"
```

## What to look for in ffmpeg output

Success indicators:

- `Added subtitle file: 'captions.ass' (N styles, M events)`
- `fontselect: (<FontName>, <weight>, <slant>) -> <ResolvedFont>, ...`

Do not trust an MP4 file's existence as subtitle success.

## Visual check rule

After render:

```bash
ffmpeg -y -ss 0.5 -i out.mp4 -frames:v 1 sample.jpg
```

Inspect `sample.jpg` visually for burned text. ASS burns create no subtitle stream; `ffprobe` stream listings are expected to show only video/audio.

## Known failure modes

- `ass_read_file(...): fopen failed` while the file exists: ASS or font path was passed through nested quoting/quoted-msys path translation. Move the file to a path without spaces.
- `fontselect: (Burbank Big Condensed, 700, 0) -> Arial-BoldMT`: font family/style mismatch. Fix by matching the exact internal family name from the OTF.
- Empty subtitle text in a frame after `Added subtitle file`: likely font fallback rendered invisible/zero-size text.

Record the actual user-facing problem phrase when the user reports not seeing subtitles. Do not re-run a fuller pipeline without checking whether the existing ASS still contains the expected first-cue word (e.g. `TOMB`) and whether the frame was taken from the true final output path (`<project>/render/<slug>.mp4`) rather than a comparison scratch file. Use the same `0.5s` first-frame probe as the default subtitle-visible reproduction check for Windows subtitle renders.

## Command caveat
When stripping markdown-fenced command blocks, remove the surrounding fences before execution; otherwise shell and shellcheck will reject the literal line ` ```\` before the actual ffmpeg invocation runs.

## Next step after MVP
Replace `create.py` subtitle quoting with the same working pattern before restoring full-pipeline cleanup behavior.