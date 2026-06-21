# AI Channel Shorts Folder Notes

Source of truth from the existing `2026-06-04-black-ops-7` pipeline.

## File layout

- `TO UPLOAD/<slug>.mp4` is the final deliverable.
- `shorts/<slug>/render/final.mp4` is the rendered source.
- `shorts/<slug>/captions/captions.vtt` is the caption file.
- `shorts/<slug>/audio/voiceover.mp3` is the voiceover.
- `shorts/<slug>/output_tmp/` holds trailer source, concat versions, and generated clips.

## Captions

- Existing captions are UPPERCASE.
- Existing `captions.vtt` samples omit the `WEBVTT` header, which makes them malformed even though ffmpeg can still burn them in.
- If `captions.vtt` is missing `WEBVTT`, prepend `WEBVTT` and a blank line to normalize before render.
- Caption style in render: Impact font, size 28, white primary, black outline, bold, centered horizontally and vertically.

## Script style

- Sample scripts use 4 uppercase paragraph lines packed into short punchy lines.
- Scripts are saved under `shorts/<slug>/script/script.txt` and also mirrored in root scripts/ for reuse.

## Render rule

- Final must fit 720x1280 using cover crop so no black bars appear.
- Voiceover should cover the full runtime; trim the scaled video to audio duration with `trim=duration=<audio_dur>`.
