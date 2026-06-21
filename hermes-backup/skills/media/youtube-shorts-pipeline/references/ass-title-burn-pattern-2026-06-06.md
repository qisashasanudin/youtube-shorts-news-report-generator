# ASS title-burn pattern for Windows ffmpeg/libass (2026-06-06)

This host's Windows ffmpeg/libass path has a known limitation: inline ASS style tokens such as `&H00FFFFFF` can confuse ffmpeg's filtergraph parser, and absolute Windows paths sometimes produce broken subtitle rendering.

Verification on this host:
- `ffmpeg -version` used: Gyan FFmpeg 8.1.1
- OS: Windows 10 / MINGW64/MSYS2 shell

Safer ASS burn pattern:
1. Copy `captions.ass` into the same directory as the input video.
2. Burn it with the simple `ass=` filter and no `force_style=` overrides: `-vf "ass=captions.ass"` or `-vf "ass=relative/captions.ass"`.
3. If you need a duration-limited preview render, do it separately: `-ss <start> -t <seconds> -i input.mp4 ... ass=... output.mp4`.
4. If you modify style values, change them inside the ASS header first (`[V4+ Styles]`) and then rerun a preview frame.
5. When you switch between `Alignment=2` and `Alignment=5`, verify visually after each change because visibility failure looks the same as an empty stream.