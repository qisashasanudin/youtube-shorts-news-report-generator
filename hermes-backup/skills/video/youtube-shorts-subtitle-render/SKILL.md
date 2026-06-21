---
name: youtube-shorts-subtitle-render
description: Render 720×1280 YouTube Shorts with burned-in Whoosh font subtitles using proven ffmpeg pipeline.
trigger: When building or rendering YouTube Shorts with burned-in subtitles, or when subtitle font/style needs to match an existing gold standard.
---

# YouTube Shorts Subtitle Render Pipeline

## Purpose
Render 720×1280 YouTube Shorts with burned-in Whoosh font subtitles using proven ffmpeg pipeline.

## Dependencies
- ffmpeg with libass, libx264, libfreetype support
- Whoosh font files: `assets/fonts/whoosh/Whoosh.otf` and `Whoosh.ttf`
- Silent Hill gold standard style: uppercase, Whoosh 64pt bold, MarginV=150, centered horizontal

## Project Layout
```
videos/
  TO_UPLOAD/                 <- single shared upload folder
  <project-slug>/
    script/
      script.txt             <- narration text, one line
      title.txt              <- final upload filename base
    audio/voiceover.mp3
    captions_vtt/captions.vtt
    captions_ass/captions.ass
    clips/
      trailer_full.mp4
      reordered.mp4
      filelist.txt
      part_*.mp4
    render/final.mp4
    assets/fonts/whoosh/
      Whoosh.otf
      Whoosh.ttf
```
Path hygiene: avoid spaces in project root path on Windows; use a short relative CWD when invoking ffmpeg so `ass=` filter arguments don't break on `Program Files`-style quoting.

## Steps

### 0. Script length target
Use **100–200 words**. Enforce minimum **30 seconds** for final video duration.

### 1. Generate script
`script/script.txt`: one long line, hook + "and here's what you need to know" + info + engagement question.
`script/title.txt`: exact title only, no date prefix.

### 2. Generate TTS audio
```bash
edge-tts --voice en-US-GuyNeural --rate '+15%' -f script/script.txt --write-media audio/voiceover.mp3
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 audio/voiceover.mp3
```
Only proceed if duration≥30s. If too short, extend script and regenerate.

### 3. Generate VTT captions
```bash
python scripts/make_vtt_small.py audio/voiceover.mp3 captions_vtt/captions.vtt
python scripts/vtt_to_ass.py captions_vtt/captions.vtt captions_ass/captions.ass
```

ASS style line (current active):
```
Style: Default,Whoosh,120,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,6,1.2,5,5,5,150,0,0,0
```

Key preferences captured from recent review:
- Subtitle placement target: lower-middle, between center and bottom. Do NOT anchor to the very bottom edge.
- Do NOT force per-event alignment with `{\\an5}` in the Dialogue line. Let the style alignment control layout so MarginV can shift placement properly.

Engagement text rule:
- Engagement wording is not hardcoded. It must come from the `--subtitle` text passed to the builder, and should be generated as part of that LLM-written body. Do not inject fixed phrases inside the pipeline.

### 4. Build shuffled edit
Determine edit target from TTS duration (rounded up to nearest 5s boundary), then:
```bash
cd clips && python build_edit.py
```
Expected: `reordered.mp4` at target duration.

### 5. Render final with burned-in subtitles
Run from inside project root so paths stay relative:
```bash
ffmpeg -y \
  -i clips/reordered.mp4 \
  -i audio/voiceover.mp3 \
  -filter_complex "[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,ass=captions_ass/captions.ass:fontsdir=assets/fonts/whoosh[v]" \
  -map "[v]" -map 1:a \
  -c:v libx264 -c:a aac -shortest \
  render/final.mp4
```

### 6. Verify
Check: width=720, height=1280, duration matches voiceover.
Extract frame:
```bash
ffmpeg -ss 2 -i render/final.mp4 -frames:v 1 render/frame_check.jpg
```
Confirm Whoosh font and upper position from frame. If font falls back, patch ASS header and re-render.

### 7. Copy to shared TO_UPLOAD
```bash
cp render/final.mp4 "videos/TO_UPLOAD/$(cat script/title.txt).mp4"
```

## Pitfalls
- Do NOT delete `captions_ass/captions.ass` before render.
- Avoid Windows spaces-in-path drive failures: use relative paths and run ffmpeg from project root.
- `filelist.txt` must use Unix newlines for ffmpeg concat demuxer.
- If ffmpeg log shows `fontselect: (Arial, 700, 0) -> Arial-BoldMT`, regenerate ASS after patching header.
- Only claim success after both an ffprobe duration check and a frame-level visual check pass.
- ASS override tags: do NOT emit per-event `{\an5}` override tags. They override the style-level alignment and ignore `MarginV` tuning.
- If subtitle normalization produces a leading `-` on a word (e.g. `game-changing` → `-changing`), strip it before writing the Dialogue line. Check the first ~20 Dialogue lines of the generated ASS for stray leading dashes and rebuild if found.
- Windows primary runtime: use the project `.venv` for Edge TTS rather than WSL. Edge TTS is Windows-only; discovered path may be under the Hermes venv, e.g. `C:/Users/qthas/AppData/Local/hermes/hermes-agent/venv/Scripts/edge-tts.EXE`.
- Enforce ≥30s final video duration. If too short, extend script and regenerate.
## Verified Working
- Project: tomb-raider-legacyofatlantis-june2026
- Output: 720×1280, 30.03s, Whoosh subtitles in shared TO_UPLOAD
- Date: 2026-06-06

- Project: mashbuttongaming (2026-06-17) - Unified builder `build_short.py` taking 3 inputs (--title, --narration, --youtube), outputting to `videos/TO_UPLOAD/{TITLE}.mp4`. Verified end-to-end: yt-dlp download → edge-tts → faster-whisper word alignment → ASS → shuffled 5s clip splice → ffmpeg subtitle burn + audio mux. 720×1280, ~8-11s duration, 2-3MB.

## Unified Builder Pattern (build_short.py)

### New 3-Input Interface (human + agent)
```bash
# CLI
python src/scripts/build_short.py --title "TITLE" --narration "50-150 words" --youtube "URL"

# Import (agent)
from build_short import build_short
build_short(title="...", narration="...", youtube_url="...")
```

**Inputs (exactly 3):**
- `--title` — News title (filename stem)
- `--narration` — Voiceover script (30-150 words, plain sentences)
- `--youtube` — YouTube trailer URL (background footage)

**Output:** `videos/TO_UPLOAD/{TITLE}.mp4` — vertical 720×1280 Short with burned captions + audio

**Pipeline (re-use existing Whoosh pipeline):**
1. `yt-dlp` download (1080p mp4, best quality)
2. `edge-tts` (en-US-BrianMultilingualNeural, +25%) → `voiceover.mp3`
3. `faster-whisper small` word timestamps → `captions.ass` (Whoosh 120pt, MarginV 150)
4. Slice trailer → 5s chunks → shuffle → concat to narration duration
5. `ffmpeg` scale 720×1280 + `ass=` filter + audio mux → final MP4

This replaces both `main.py` (auto-pipeline) and `shorts_builder.py` (manual one-shot). Cron job finds stories → delivers to Discord → you pick → run `build_short.py` with the 3 inputs.