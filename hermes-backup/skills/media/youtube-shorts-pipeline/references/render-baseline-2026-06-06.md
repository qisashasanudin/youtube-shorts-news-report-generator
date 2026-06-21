# AI Channel render baseline 2026-06-06

- Burned ASS subtitles do not produce a subtitle stream in `ffprobe`; expected streams are `h264` + `aac` only.
- Final audio and output durations matched at `26.04` seconds for Battlefield 6 rebuild, confirming tail gap is removed by hard-trimming to voiceover duration.
- Burbank Big Condensed Bold installed from release asset and registered as `Burbank Big Cd Bd`.
- Font config: use the registered Windows family name in ASS style; keep template placeholder and `.format()` keyword aligned.
- Trailer resolution preference encoded in download selection: prefer `bestvideo[height>=1080][ext=mp4]+bestaudio[ext=m4a]`, then `best[height>=1080][ext=mp4]`, then `best[ext=mp4]`.
- Encoder baseline updated to `medium` preset with `crf 18` after prior `veryfast`/`20`.
- Hashtags are stripped from TTS input so narration does not speak hashtags, while keeping them in title/metadata.
- Title/filename rule: upload file name must match `metadata/title.txt` exactly with no date prefix.
