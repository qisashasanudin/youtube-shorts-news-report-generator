Subtitle sync failure in Wardogs rebuild was traced to dashes in the `--subtitle` text.  
- Input: `tmp/wardogs-subtitle-v3.txt` contains hyphenated compounds.  
- Failure mode: these merged tokens after split/tokenization created mismatched script vs captions and drove ASS cues off-sync.  
- Triggered change: `src/shorts_builder.py` now sanitizes `-` -> ` ` before word checks/TTS/STT, so alignment can’t drift from hyphenation.  
- Rebuild command after patch: same builder invocation (`src/shorts_builder.py --youtube ... --title ... --subtitle "$(cat tmp/wardogs-subtitle-v3.txt)"`) is sufficient; do not rewrite the subtitle text again unless policy requires new wording.  
- Verify point: inspect ASS around 35-45s after rebuild; `2026’S` / `SHOOTERS.` region should complete before 00:00:40.