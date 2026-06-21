Notes from the 2026-06-06 subtitle burn investigation.

- Rendering with `ass=captions/captions.ass:fontsdir=assets/fonts/whoosh` from the repo root produced successful ffmpeg runs with libass loading `Whoosh.otf` and reporting events added.
- Frame inspection via OCR did not detect subtitle text in the rendered MP4 even though ffmpeg reported success.
- Confirmed styles in use: Alignment 5, MarginV 70, Fontsize 64, Bold -1, PrimaryColour &H00FFFFFF, OutlineColour &H00000000, Outline 3, Shadow 0.5.
- Confirmed pitfall: Windows filter args split on `:`, so absolute Windows paths with drive letters break `ass=`/`subtitles=`. Prefer repo-relative paths with `cwd=REPO`.
