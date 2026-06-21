# Windows ffmpeg 8.1.1 subtitle burn quirk (2026-06-06)

Host: `qthas@TheUdinForce MINGW64 ~` ffmpeg 8.1.1 full build via MSYS2.

## Symptom

Builder completes with status success and writes `final.mp4`, but a later `-show_streams -select_streams s` probe shows no subtitle stream. ffmpeg log shows this exact error string:

```
[AVFilterGraph @ ...] No option name near 'C:/Users/qthas/Programming/Belajar/YouTube/MashButtonGaming/...'
[AVFilterGraph @ ...] Error parsing a filter description around: [v]
Error : Invalid argument
```

The offending filter value:
```
subtitles='videos/2026-06-06-19-44-21_until-dawn-2-revealed-at-state-of-play-2026/captions/captions.ass':fontsdir='C:/Users/qthas/.../assets/fonts/whoosh'
```

## Root cause

Absolute Windows paths in `subtitles=...`/`fontsdir=...` break filter parsing on this host, even when the same ffmpeg build accepts those paths as `-i` inputs. The parser splits on `:` and misinterprets `C:`, producing the `No option name near '...'` error.

It also fails when using repo-relative paths but running ffmpeg with `cwd=<work dir>` rather than `cwd=<repo root>`: the relative path is then resolved from the work dir, so `videos/<slug>/captions/captions.ass` does not exist relative to `work`.

## Fix

Use repo-relative POSIX paths with `cwd=REPO`:

```python
ass_rel = ass.relative_to(REPO).as_posix()
font_rel = (font_dir or DEFAULT_FONT_DIR).relative_to(REPO).as_posix()
vf = (
    "[0:v]scale=720:1280:force_original_aspect_ratio=increase,"
    f"crop=720:1280,ass={ass_rel}:fontsdir={font_rel}[v]"
)
cmd = [
    "ffmpeg", "-y",
    "-i", str(reordered),
    "-i", str(audio),
    "-filter_complex", vf,
    "-map", "[v]", "-map", "1:a",
    "-c:v", "libx264", "-c:a", "aac", "-shortest", "-pix_fmt", "yuv420p",
    str(out),
]
res = run(cmd, cwd=REPO)
```

Key constraints:
- `cwd` must be `REPO`, not `work`
- use `.as_posix()` for both paths
- use `ass=...:fontsdir=...`, not `-i <ass>` + `subtitles=...` (this host also misparsed absolute paths inside the latter)

## Verification

After render, probe a frame at a known active cue timestamp (e.g., `00:00:06.50`). The MP4 subtitle stream will still be absent because subtitles are burned into frames; check visible text, not `-show_streams -select_streams s`.
