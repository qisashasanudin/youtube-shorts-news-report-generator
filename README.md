# MashButtonGaming YouTube Shorts News Generator

One-shot builder that converts a YouTube trailer URL, a title, and a short narration script into a vertical Shorts-ready MP4 with burned-in captions.

## What this repo contains

- `src/shorts_builder.py` — single entrypoint launcher for the current builder.
- `src/main.py` — orchestrates download, voiceover, editing, subtitle generation, rendering, and final verification.
- `src/config.py` — repo root and asset path resolution, plus ffmpeg/ffprobe discovery.
- `src/utils.py` — shared subprocess helpers, duration probing, slugification, and timestamp functions.
- `src/download.py` — trailer download logic using `yt_dlp`.
- `src/voice.py` — TTS/voiceover generation via local `piper`, `edge-tts` CLI, or `edge_tts` Python fallback.
- `src/edit.py` — trailer clip extraction, optional shuffle, selection, and concat assembly.
- `src/subtitles.py` — ASS caption generation with per-word timing.
- `src/render.py` — subtitle burn and final 720×1280 MP4 render.
- `src/editorial_state.py` — optional CLI helper for duplicate checks and daily upload counting.
- `requirements.txt` — Python dependency list.
- `assets/fonts/whoosh/` — font assets required for ASS subtitle rendering.
- `videos/TO_UPLOAD/` — destination for final output files.
- `hermes-backup/` — backup documentation and legacy skill files; not required to run the builder.

## Architecture

This project no longer uses a shell wrapper or a `src/scripts/` build helper. The entire active pipeline is now rooted in `src/` with one launcher.

```
┌─────────────────────────────────────────────────────────────┐
│  python3 src/shorts_builder.py                               │
│    --youtube "https://youtu.be/..."                         │
│    --title "BOMBASTIC CLICKBAIT TITLE"                      │
│    --subtitle "50-150 word narration script text"           │
│    [--no-shuffle]                                            │
│  → videos/TO_UPLOAD/<slugged-title>.mp4                      │
└─────────────────────────────────────────────────────────────┘
```

## How to run

1. Create and activate a Python virtual environment from the repo root:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
3. Run the builder:
   ```bash
   python3 src/shorts_builder.py --youtube "<url>" --title "<TITLE>" --subtitle "<50-150 word narration>"
   ```
4. Optional: disable random trailer shuffling:
   ```bash
   python3 src/shorts_builder.py --youtube "<url>" --title "<TITLE>" --subtitle "<text>" --no-shuffle
   ```

## Runtime behavior

- Downloads a YouTube trailer via `yt_dlp`.
- Generates narration audio with either `piper`, `edge-tts` CLI, or `edge_tts` Python.
- Splits the source trailer into 5-second clip segments.
- Optionally shuffles segments before selecting the final edit.
- Builds ASS captions and burns them into a vertical 720×1280 MP4.
- Writes the final asset to `videos/TO_UPLOAD/`.

## Output paths

- Intermediate working folder: `videos/<YYYY-MM-DD>-<SLUGIFIED_TITLE>/`
- Final output: `videos/TO_UPLOAD/<SLUGIFIED_TITLE>.mp4`
- The builder uses clean title slugification to name the final MP4.

## Requirements and environment

- Python 3.11+ is recommended. Python 3.9 is deprecated by upstream dependencies.
- `ffmpeg` and `ffprobe` must be installed and discoverable on PATH, or available via Homebrew locations on macOS.
- `assets/fonts/whoosh/` must exist and contain font files for ASS rendering.
- `requirements.txt` is the single dependency source of truth for Python packages.

## Subtitle and script rules

- `--subtitle` must contain between 50 and 150 words.
- The builder generates one caption line per word in uppercase.
- The word timing is derived from `faster-whisper` when available, otherwise fallback timing is used.

## Notes

- `src/shorts_builder.py` is intentionally small; it imports and runs the implementation from `src/main.py`.
- No shell wrapper is required or expected.
- `hermes-backup/` contains archival skill documentation, not the active builder code path.
- Uploading final MP4s to TikTok or YouTube is outside this repository’s current runtime scope.
