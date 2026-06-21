# Subtitle-only Regeneration

Use this when the final render is mostly fine but captions need changing, especially when moving to word-level 1-2 word cues.

## Rule

Do not re-run TTS unless you must. Reusing `audio/voiceover.mp3` avoids changing timing.

## Workflow

1. Generate/update `shorts/<slug>/script/script.txt` as a single-line narration source.
2. If the audio already exists, skip TTS.
3. Generate `captions/captions.vtt` with faster-whisper word-level cues:
   - Use smaller/fast model, device hint depending on hardware; example from a successful run used CPU with `int8`.
   - Prefer VTT shape `0:00:00,100 --> 0:00:22,987`, uppercase.
   - Use `scripts/ai_channel_scripts/subtitles.py` helpers to parse VTT into ASS safely.
4. Render with:
   - explicit ASS burn via `ass=` filter
   - Impact font, size 48, white fill, black outline, Alignment 5
   - no bars / 720x1280 output
5. Mux with the reused narration audio and copy to `TO UPLOAD/<slug>.mp4`.

## Pitfalls

- Using `scripts/create_short.py` for subtitle-only rerenders can trigger re-download/reclip flows and bugs; prefer the stable inner builder package or a subtitle-only path if you want to avoid full rebuilds.
- Empty/no-cue VTT will create silent subtitles; always verify the captions file before render.
- When you do replace caches, run rebuilds instead of trying to patch from a broken file.
