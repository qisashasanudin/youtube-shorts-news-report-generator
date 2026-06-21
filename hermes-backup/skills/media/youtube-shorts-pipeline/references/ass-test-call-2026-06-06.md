# ASS subtitle test instructions

Purpose
- Check whether the Windows `ass=` filter path is usable.
- Do a short render with `-t 5` and inspect a frame at a known active cue timestamp.
- Do not claim success just because an MP4 was written.

Quick command (copy-paste)
ffmpeg -y -ss 0 -t 5 -i "<video>" -i "<audio>" \
  -filter_complex "[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,subtitles=<subtitle_file>[v]" \
  -map "[v]" -map 1:a -c:v libx264 -c:a aac -shortest <output>

Success criteria
- Frame at an active cue shows readable caption text.
- Non-visible text is treated as failure regardless of exit code.

