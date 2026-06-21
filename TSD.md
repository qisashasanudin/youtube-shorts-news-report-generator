# TSD — Toolchain, Software, and Compatibility for youtube-shorts-news-report-generator

## Purpose

This document defines the exact runtime dependencies, compatibility requirements, and operational conventions for the current Shorts builder implementation.

## Active builder entrypoint

- `python3 src/shorts_builder.py --youtube "<url>" --title "<TITLE>" --subtitle "<text>"`
- `src/shorts_builder.py` delegates to `src/main.py` and the modular source files under `src/`.

## Repository structure

- `src/shorts_builder.py` — launcher entrypoint.
- `src/main.py` — build orchestration.
- `src/config.py` — repo path resolution, ffmpeg/ffprobe discovery, font path constants.
- `src/utils.py` — subprocess helper, duration probe, slugifier, and timestamp functions.
- `src/download.py` — YouTube trailer download logic.
- `src/voice.py` — TTS audio generation and voiceover duration measurement.
- `src/edit.py` — clip extraction, shuffle logic, concat assembly.
- `src/subtitles.py` — ASS caption generation with optional Whisper timing.
- `src/render.py` — final subtitle burn and render.
- `src/editorial_state.py` — optional duplicate/check/count CLI helper.
- `requirements.txt` — Python dependency manifest.
- `assets/fonts/whoosh/` — font assets required for ASS rendering.
- `videos/TO_UPLOAD/` — final MP4 output.

## Platform and runtime

- Recommended Python: 3.11 or higher.
- Verified: Python 3.11, 3.13.
- Avoid Python 3.9 for new installs; upstream packages warn against it.
- The builder runs from the repo root.
- Use a virtual environment for dependencies.

## Python environment setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## Python dependencies

Current dependency list from `requirements.txt`:

- edge-tts >= 0.4.0
- faster-whisper >= 1.0.0
- whisperx >= 1.3.0
- yt-dlp >= 2025.0.0
- requests >= 2.28.0
- feedparser >= 6.0.0
- python-dotenv >= 1.0.0

## External tool requirements

- `ffmpeg` — must support `libass`, `libfreetype`, `libx264`, and `aac`.
- `ffprobe` — used for duration probing.
- `edge-tts` CLI is optional but preferred for TTS if installed.
- Local `piper` executable support exists as a fallback if `piper` is installed and the `apps/piper/piper.exe` path is available.

## Important runtime details

- `config.py` searches for `ffmpeg`/`ffprobe` on PATH and common macOS Homebrew locations.
- Font rendering requires `assets/fonts/whoosh/`; missing fonts abort startup.
- Intermediate files are written under `videos/<timestamp>-<slug>/`.
- Final output is written to `videos/TO_UPLOAD/`.
- `src/editorial_state.py` is not required for main builder execution.

## Command-line behavior

- `--youtube` — required trailer URL.
- `--title` — required exact title / filename stem.
- `--subtitle` — required narration text, 50-150 words.
- `--shuffle` — default enabled.
- `--no-shuffle` — disables random trailer segment reordering.

## Validation checklist

- Confirm `python3` is installed and available.
- Confirm `ffmpeg` and `ffprobe` are available on PATH or via macOS Homebrew paths.
- Confirm `assets/fonts/whoosh/` exists with font files.
- Create and activate `.venv`.
- Install dependencies from `requirements.txt`.
- Run:
  ```bash
  python3 src/shorts_builder.py --youtube "https://youtu.be/..." --title "TEST TITLE" --subtitle "Fifty words of narration ..."
  ```
- Verify final MP4 is written to `videos/TO_UPLOAD/` and the build completes without font/tool errors.

## Notes on repo artifacts

- `hermes-backup/` contains documentation, skill backups, and legacy references; it is not part of the active builder runtime.
- There is no active `run_short_builder.sh` wrapper in this repo.
- There is no active `src/scripts/` build helper in this repo.
- Upload automation is outside the current repo scope.
