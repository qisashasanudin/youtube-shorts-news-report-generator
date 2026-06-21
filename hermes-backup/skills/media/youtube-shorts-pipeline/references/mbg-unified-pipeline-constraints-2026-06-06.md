# MashButtonGaming Unified Pipeline Constraints (2026-06-06)

## One-codebase rule
Use `scripts/pipeline/run.py --video <project-slug>` for every video. Do not introduce per-video build scripts that diverge from this path.

## Script/title override rule
If `script/script.txt` and `script/title.txt` already exist, treat them as the source of truth. The unified pipeline must not silently regenerate placeholder text when files exist.

## Voiceover length guard
Do not render final output shorter than ~25-30 seconds. If narration/audio is too short, extend the narration script first. Do not rely on `-shortest` when the audio tail is meaningful; prefer hard-trim from concatenated shuffled edit to voiceover duration and ensure total runtime meets minimum duration before render.

## Subtitle font consistency rule
All projects must use `assets/fonts/whoosh/Whoosh.otf` with the same style:
- Uppercase bold text
- Raised/centered safe-area position
- No silent fallback to Arial/Burbank; surface the missing font error if the local copy is absent.

## Unified pipeline path contract
- Title source: `videos/<slug>/script/title.txt`
- Script: `videos/<slug>/script/script.txt`
- Asset font: `assets/fonts/whoosh/Whoosh.otf`
- Render: `videos/<slug>/render/final.mp4`
- Upload copy: `videos/TO_UPLOAD/<title>.mp4`
- Footage: `videos/<slug>/clips/trailer_full.mp4`
- Edit: `videos/<slug>/clips/reordered.mp4`

## Title fallback behavior
When `title.txt` is missing, generate or preserve the user-facing title, but never overwrite an existing `title.txt` without explicit instruction.
