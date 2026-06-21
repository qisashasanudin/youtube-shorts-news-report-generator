Session rebuild observations for the unified `scripts/ai_channel_scripts/create.py` workflow.

## Rebuild results (new method: single-line script + faster-whisper 1-2 word captions)
- 2026-06-04-black-ops-7.mp4: succeeded
- 2026-06-05-god-of-war-laufey.mp4: succeeded
- 2026-06-04-until-dawn-2.mp4: first run interrupted, second run succeeded
- 2026-06-05-marvels-wolverine.mp4: already rebuilt in earlier change

## Assumption updates to encode
- Background jobs can receive SIGTERM (-15) and exit before completion. Treat that as transient and re-run with same seed.
- Not all existing TO UPLOAD items have rebuildable project folders. Inspect `shorts/<slug>/` first.
- Punctuation in `script/script.txt` materially affects TTS pacing and STT cue quality.