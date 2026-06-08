# youtube-shorts-news-report-generator

Generates vertical YouTube Shorts news/report videos from an official trailer/reference URL,
TTS narration, burned-in captions, and automated editorial scheduling.

## Status

- Main renderer: `src/shorts_builder.py`
- Editorial state: `src/editorial_state.py`
- Manual upload helper: `src/scripts/youtube_upload.py`
- Scheduler: Hermes cron jobs (8x/day)
- Cleanup: daily temp/build folder cleanup
- Default branch: `master`

## What the system does

One-shot build:
1. Download official YouTube source with `yt-dlp`
2. Generate TTS voiceover with Edge TTS
3. Extract shuffled 5s trailer chunks, concat/trim with stream copy
4. Generate ASS captions aligned to TTS via faster-whisper word timestamps
5. Burn captions into 720x1280 final MP4
6. Verify output file size + duration

Editorial automation:
- Discovers qualifying stories within 72 hours
- Scores stories and removes duplicates across runs
- Builds one video per run, up to 8 per day
- Delivers finished MP4s to Telegram

## Constraints enforced by the builder

- `--subtitle` text must be 100-200 words
- Output filename is sanitized for filesystem safety
- `assets/` content is loaded from repo-relative paths so caption font lookup is consistent
- Final video duration must be within Shorts limits
- Footage is selected from official sources only; ranked priority is enforced at the editorial/orchestration layer

## Content rules

- Title must not include: `and here's what you need to know`
- Subtitle first sentence must end with: `and here's what you need to know.`
- Subtitle closing engagement sentence must start with: `but what do you think?`
- Subtitle closing engagement sentence must end with an open-ended question ending with `?`

## Repo layout

Top-level:
```text
src/
  editorial_state.py
  scripts/
    youtube_upload.py
    requirements.txt
  shorts_builder.py
assets/
  fonts/
    whoosh/
      Whoosh.otf
      Whoosh.ttf
videos/
  <timestamp>_<slug>/   # working directories
  TO_UPLOAD/            # ready for delivery
```

## First-run setup

From the repo root:
```bash
python -m venv .venv
.venv\\Scripts\\python.exe -m pip install -r src/scripts/requirements.txt
```

Run the builder from the repo root:
```bash
.venv\\Scripts\\python.exe src/shorts_builder.py \\
  --youtube "<YOUTUBE_URL>" \\
  --title "<TITLE_TEXT>" \\
  --subtitle "<NARRATOR_SCRIPT_TEXT>"
```

Manual upload:
```bash
.venv\\Scripts\\python.exe src/scripts/youtube_upload.py "videos/TO_UPLOAD/<file>.mp4" --title "<TITLE>" --privacy private --description "<DESCRIPTION>" --tags "TAG1,TAG2"
```

## Privacy / artifact handling

- `videos/` is ignored in git
- Final rendered video assets stay local in `videos/TO_UPLOAD/`
- `assets/` is tracked in git
- Daily cleanup removes temp/build folders while preserving `videos/TO_UPLOAD`

## TSD / toolchain details

See `TSD.md` for toolchain, dependency versions, platform requirements, and compatibility notes.
