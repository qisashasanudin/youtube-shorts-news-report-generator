---
name: ai-channel-youtube-shorts
description: Class-level skill for generating AI gaming channel YouTube Shorts with TTS, trailer assembly, subtitle burning, and final upload staging.
---

# AI Channel YouTube Shorts Pipeline

Class-level skill for generating YouTube Shorts videos for the AI gaming channel. Covers the full `create.py` workflow: TTS, trailer download, clip assembly, subtitle burn, and final upload staging.

## Trigger Conditions

Load this skill when:
- Building or debugging an AI Channel short
- Subtitle positioning or visibility is broken
- `create.py` fails at render, trailer download, or clip assembly
- The final MP4 has no visible subtitles
- You need to inspect or fix ASS subtitle rendering paths

- Edge-TTS (`edge-tts.exe` on Windows) is the default preferred TTS for this workflow because it provides the best voice quality for these Shorts. Do not install or switch to another local TTS engine silently; if the user requests a different engine, implement that explicitly, otherwise keep Edge-TTS.
- If the user later asks about local TTS, note that `piper-tts` is installable in WSL but has been observed as robotic/less natural for this use case compared to Edge-TTS.

### Subtitle Burn (Windows)

The subtitle layer must be burned with a **local-font-dependent** command using absolute paths. Verified working ffmpeg command shape:

```bash
ffmpeg -y \
  -i "<project>/output_tmp/scaled.mp4" \
  -i "<project>/audio/voiceover.mp3" \
  -filter_complex "[0:v]ass='<abs-posix-ass-path>':fontsdir='<abs-posix-fonts-dir>',pad=720:1280:(720-iw)/2:0:color=black[outv]" \
  -map "[outv]" \
  -map 1:a \
  -c:v libx264 -preset veryfast -crf 20 \
  -c:a aac -b:a 192k \
  -shortest \
  -t <audio_duration> \
  "<project>/render/<slug>.mp4"
```

**Critical quoting rules:**
- Convert backslashes to forward slashes: `replace("\\", "/")`
- Do NOT escape colons inside the filter string (break ffmpeg option parsing)
- Escape spaces with `\ ` inside the filter string
- Verified working ASS file: `<project>/render/captions.ass`
- Verified working fontdir: `<project>/render/`

### Font Family Name Issue

The project font file `burbank_big_condensed.otf` loads successfully but maps to `Arial-BoldMT` under libass/DirectWrite+directwrite:

```
fontselect: (Burbank Big Condensed, 700, 0) -> Arial-BoldMT, 0, Arial-BoldMT
```

This means the requested font style resolves to Arial because the OTF's internal style name doesn't match the requested name. Subtitle burn succeeds mechanically, but Burbank text is invisible because libass substitutes a fallback font (Arial) which then has no visible rendering activity.

**Lesson:** When subtitles appear invisible in ffmpeg/libass, check the `fontselect:` debug line. A direct font-family-to-Arial mapping means you're hitting a fallback substitution.

### Script Structure Rule

Each short narration must follow the proven retention structure:

- sensational / ambiguous hook
- the exact phrase "and here's what you need to know."
- the main information
- a closing "But what do you think?" line plus a fresh open-ended engagement question

Use casual conversational tone with these four elements in this order.

### Subtitle Cue Rule

Prefer **one word per cue**, perfectly synced to TTS narration. Generate captions from the final voiceover with faster-whisper STT so timing is derived from the actual audio, not hardcoded. Do not embed subtitle text or timing literals into project files.

### Subtitle Position Rule

Do not place burned-in subtitles at the very bottom of the video frame. Increase the subtitle position (lower the vertical drop) so it sits higher on screen and does not collide with the YouTube channel name / title / description UI. Verify visually on a rendered frame before treating the video as done.

### Subtitle Weight Rule

Use bold subtitle weight. When rendering ASS, set bold on and confirm via vision check.

### Clip Assembly Rule

Always split the trailer into segments, then randomly reorder enough clips to cover the full narration duration before rendering. Do not use the source trailer as the final video sequence without this shuffle step.

### Minimum Duration Rule

All final videos must be at least 30 seconds. Enforce during clip selection/concat:
- If generated audio is < 30s, extend the script text before rebuilding
- Each short must be exactly one game/topic; script, title, and trailer must all match that single game

### Filename Rule

Final MP4 filename must match `metadata/title.txt` exactly, with no date prefix. Hashtags appear in the filename. Truncate at 180 chars.

## Pitfalls

- `captions.ass` is **generated output**, not a stable config. Editing it in-place is a no-op for future renders because `create.py`/`subtitles.py` regenerate it. Patch `scripts/ai_channel_scripts/subtitles.py` instead so the chosen font and margins are preserved across reruns.
- The installed font family name for the Burbank OTF is `Burbank Big Cd Bd`. If you render with a different requested name, libass can silently substitute Arial-BoldMT, making subtitles invisible or wrong.
- `Alignment=5` (middle-center) ignores `MarginV`; use `Alignment=2` (bottom-center) instead
- **Prefer `render.py` over `create.py` for subtitle burn.** `render.py` is the known-good 3-step path: video-only encode, ASS burn with `ass='...'` (no `fontsdir=`, no `force_style`), then audio mux. `create.py`'s `step_render()` has an inline `filter_complex` `ass=...:fontsdir=...` form that intermittently fails with `Invalid argument` on Windows, and repeated rewrites of its filter string do not fix the underlying issue. If `create.py` fails at render, fall back to the `render.py` pattern instead of patching `create.py` again.
- **Do not chase the subtitle bug by repeatedly rewriting `captions.ass` or filter strings.** When the user reports the render still looks wrong after multiple adjustment attempts, stop, inspect `render.py`/`WORKFLOW.md`, and switch to the working legacy pattern rather than editing the same ASS fields again.
- `build_ass()` per-cue margin fields override style-level margins; emit empty per-cue margin fields with 8-field Dialogue lines
- Trailer download may require `--cookies-from-browser` if the source is age-restricted
- Manual mpv/mplayer reconfigure checks are **not** valid verification — see mpv verification rules below
- The verified subtitle burn filter shape is `ass='<abs-posix-ass-path>':fontsdir='<abs-posix-fonts-dir>'`. Do **not** re-escape the `:` inside `<abs-posix-ass-path>`, and do **not** pass Windows-style escapes into the filter string.
- `create.py` has an intermittent subtitle-burn issue where the final `ass=`/`fontsdir=` filter still fails even after the path quoting changes above. Verified fallback: render the subtitle burn with an isolated manual ffmpeg call outside of `create.py`, then verify the resulting MP4.

## Verification Steps (MANDATORY)

After every subtitle burn, verify **all three** of these before claiming success:

This verification sequence requires terminal/filesystem access. **Never report a successful render if tool calls confirming MP4 and subtitle evidence were denied.** If verification calls are blocked by tool access, stop and request foreground verification.

1. ```bash
   ffprobe -v error -show_streams -of default=noprint_wrappers=1 "<final.mp4>"
   ```
   Check stream info for expected video/audio presence.

2. ```bash
   ffmpeg -ss 00:00:00 -i "<final.mp4>" -frames:v 1 -update 1 "<first-frame.jpg>"
   ```
   Use `-update 1` so the single frame writes to the named file.

3. Inspect the extracted frame with vision_analyze. Confirm subtitle text is visible. Surface exact placement in general terms only; do not tie this verification to a specific absolute Windows project path.

**Do NOT** use mpv, mplayer, or any other player's reconfigure output as verification. Any player-specific output is considered noise, not evidence.
