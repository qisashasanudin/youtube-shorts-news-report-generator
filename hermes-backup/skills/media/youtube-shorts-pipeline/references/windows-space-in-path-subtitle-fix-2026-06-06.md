# Windows Space-in-Path Subtitle Burn Failure (2026-06-06)

## Symptom
ffmpeg `ass=` / `subtitles=` filters fail when the project path contains spaces, even if the ASS/VTT file is valid.

Example failure:
- `[AVFilterGraph @ ...] No option name near '\\Users\\qthas\\Videos\\Youtube Projects\\...'`
- `Error parsing filterchain ... Invalid argument`

Root cause: the filter parser splits the Windows path on spaces before ffmpeg can resolve it.

## Fixes
1. Prefer: render from a project directory under a space-free Windows path, e.g.:
   `C:\Users\<user>\Programming\Belajar\YouTube\MashButtonGaming`
2. Alternatively: switch to a Python subprocess renderer with a proper argument list (avoids shell splitting).
3. If paths still break, move the entire project out of any path containing spaces.

## Guidance for future sessions
- Always inspect `BASE` / project paths for spaces before ffmpeg subtitle burns.
- When adding a new video, create it under the current space-free workspace.
- Document the chosen workspace in the skill, not just in memory.
