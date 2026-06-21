# Windows ffmpeg ASS/VTT subtitle path quirks

## Symptoms

- `[Parsed_subtitles_0] Unable to parse "original_size" option value ... as image size`
- Subtitle filter parses but shows no text
- ffmpeg fails to open subtitle file with obvious path

## Causes

1. `file:///` URL encoding on Windows (`%3A`, `%5C`) breaks ffmpeg ASS parser
2. Forward-slash only paths with unescaped `:` fail
3. Missing `WEBVTT` header or blank lines between cues causes parse to return empty output silently

## Fixes

- Use unencoded Windows path with escaped colon: `C\:/Users/qthas/...` or `C\\:/Users/qthas/...`
- Ensure valid VTT header and blank-line spacing between cue blocks
- For ASS style strings in `force_style=...`, escape backslashes and colons appropriately in Windows strings