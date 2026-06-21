# shorts_builder.py runtime fixes (Rayman regression, 2026-06-06)

Break/fix sequence discovered while bringing the Rayman Legends Retold deliverable to gold-standard parity with Stuntman Hollywood and Silent Hill Townfall:

1. Corrupted render function signature
- Symptom: after patching `render_final`, the script failed to parse or crashed because the inner helper signature was malformed.
- Fix: keep `_render_burn_subs(work, out)` as a thin wrapper, and keep `render_final(...)` at module scope with the exact same parameter list. Do not nest function definitions.

2. Render path contract
- Symptom: the final MP4 was written correctly, but `main()` still failed because it expected `work/render/final.mp4`.
- Fix: render directly to `videos/TO_UPLOAD/<TITLE>.mp4` from `_render_burn_subs`, then verify that exact path. Remove the "render to temp then copy" step entirely.

3. Final filename derivation
- Symptom: an extra `videos/TO_UPLOAD/final.mp4` artifact was created, while the title-named file was not being regenerated because the old copy path used a different destination name.
- Fix: `final_out = TO_UPLOAD / f"{args.title}.mp4"`. The deliverable filename must match `--title` verbatim.

4. Duration cap regression
- Symptom: segmented edit was still capped at 30 seconds even though the script/voiceover was ~55s.
- Fix: remove `target = 30.0 if duration >= 30.0 else duration`; use `target = duration` so clip count adapts to full TTS length.

Proven command shape for subtitle burn:
- Run ffmpeg from the project root using relative paths.
- filter: `[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,subtitles=captions/captions.ass:fontsdir=assets/fonts/whoosh:force_style='FontName=Whoosh,FontSize=64,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=0,Alignment=2,MarginV=100'[v]`
- map `[v]` and `1:a`, encode `libx264` + `aac`, keep `-shortest`.

Verified outcome:
- Output: `videos/TO_UPLOAD/RAYMAN... .mp4`
- Duration: 55.128s
- Resolution: 720x1280
- Single-pass subtitle burn succeeded on this Windows ffmpeg build.
