# youtube-shorts-news-report-generator

Generates vertical YouTube Shorts news/report videos from a single trailer/reference URL,
TTS narration, and burned-in captions.

Primary supported runtime: Windows with the project venv at `.venv`.

## Status

- Main entrypoint: `src/shorts_builder.py`
- Default branch: `master`
- Latest tested: gameplay/trailer URLs, YouTube trailer downloads
- Known limitation: burned-in subtitle visibility has not been verified with automated
  frame inspection. FFMpeg/subtitle pipeline works on many outputs, but this build
  should still be treated as in validation.

## What the one-shot build does

Invocation:
```bash
python src/shorts_builder.py \
  --youtube "<YOUTUBE_URL>" \
  --title "<TITLE_TEXT>" \
  --subtitle "<NARRATOR_SCRIPT_TEXT>"
```

Build steps:
1. Download YouTube source with `yt-dlp`
2. Generate TTS voiceover with Edge TTS
3. Build shortened/cut edit from the source video
4. Generate ASS captions aligned to the TTS
5. Burn captions into the final vertical MP4
6. Verify output file size + duration

Final output:
- `videos/TO_UPLOAD/<safe-title>.mp4`
- Filename is sanitized automatically; unsafe characters become `-`
- Title text remains intact in build logs / metadata

## Constraints enforced by the builder

- `--subtitle` text must be 100-200 words
- Output filename is sanitized for filesystem safety
- `assets/` content is loaded from repo-relative paths so caption font lookup is consistent

## Content rules

- Title must not include the first subtitle sentence or any phrase like `and here is` / `and here's what you need to know`
- Subtitle first sentence must end with: `and here's what you need to know.`
- Subtitle closing engagement sentence must start with: `but what do you think?`
- Subtitle closing engagement sentence must end with an open-ended question ending with `?`

## Repo layout

Top-level:
```text
src/
  scripts/
    make_vtt.py
    make_vtt_phrases.py
    make_vtt_small.py
    vtt_to_ass.py
    build_final.py
    render_now.py
    main.py
    requirements.txt
  shorts_builder.py
assets/
  fonts/
    whoosh/
      Whoosh.otf
      Whoosh.ttf
videos/
  <project>/         # working directories
  TO_UPLOAD/         # completed video(s)
```

## First-run setup

From the repo root:

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r src/scripts/requirements.txt
```

Run the builder from the repo root:

```bash
.venv\Scripts\python.exe src/shorts_builder.py \
  --youtube "<YOUTUBE_URL>" \
  --title "<TITLE_TEXT>" \
  --subtitle "<NARRATOR_SCRIPT_TEXT>"
```

## Privacy / artifact handling

- `videos/` is ignored in git
- Final rendered video assets stay local in `videos/TO_UPLOAD/`
- `assets/` is tracked in git

## TSD changes

See `TSD.md` for toolchain and compatibility notes.
