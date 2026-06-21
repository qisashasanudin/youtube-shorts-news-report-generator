---
name: ai-channel-pipeline
description: >
  End-to-end generation of AI gaming news YouTube Shorts for the user's "AI Channel" project.
  Covers single-line uppercase narration script generation, Edge-TTS voiceover, faster-whisper
  STT-based caption alignment, ASS subtitle styling, clip assembly, and deliverable placement
  in TO UPLOAD/. Use when the user asks to build, recreate, or fix shorts, update subtitles,
  adjust caption timing/style, or work with the existing project structure under
  C:\Users\qthas\Videos\Youtube Projects\AI Channel.
---

# AI Channel Pipeline

## Project Structure

- `shorts/<YYYY-MM-DD>-<topic>-<slug>/script/script.txt` — single-line uppercase narration script
- `shorts/<...>/audio/voiceover.mp3` — Edge-TTS output
- `shorts/<...>/captions/captions.vtt` — faster-whisper STT output from narration audio
- `shorts/<...>/output_tmp/` — downloaded clips, concat, scale intermediates
- `shorts/<...>/render/captions.ass` — rendered ASS subtitle file
- `shorts/<...>/render/final.mp4` — final vertical 720x1280 render
- `TO UPLOAD/<slug>.mp4` — deliverable copied from render/

Check these paths from the project root as relative paths; only resolve to absolute when an external tool actually requires it.

## ASS Style (current default)

- Font: `Burbank Big Cd Bd`
- Size: `72`
- Colors: white fill with black outline and black back
- Outline thickness: `3`
- Alignment: middle-center (ASS alignment 5)
- Margins: `MarginL=0`, `MarginR=0`, `MarginV=10`
- Effect: captions are centered horizontally and placed slightly above the true vertical center, closer to the center of the screen rather than the bottom edge.

Use `scripts/ai_channel_scripts/subtitles.py` as the source of truth for these values. Any existing `captions.ass` file should be regenerated from there.

The installed OTF for Burbank is at `C:\Users\qthas\Videos\Youtube Projects\AI Channel\scripts\fonts\burbank_big_condensed.otf`. In this project the working family name for ASS headers and per-cue style overrides is `Burbank Big Cd Bd`.

## ASS Pitfalls
## ASS Pitfalls

- **Font family must match exactly (`fontTools`-verified):** the project OTF is `C:\\Users\\qthas\\Videos\\Youtube Projects\\AI Channel\\scripts\\fonts\\burbank_big_condensed.otf`. Use `from fontTools.ttLib import TTFont; font['name'].getDebugName(4)` to read the actual internal family name and use that exact string in ASS `Fontname` headers and per-cue overrides. In past failures, using spaced aliases like `Burbank Big Condensed Bold` caused silent fallback to Arial. Do not guess-approximate the font name.
- **Int size:** ASS style encodings must stay `1`. Do not accidentally morph the header into a comment line starting with `|Style:`. A leading `|` makes the line invalid and can prevent styles from loading.
- **Alignment vs MarginV:** alignment `5` is middle-center and in most renderers ignores `MarginV`. Keep alignment `2` (bottom-center) when you want vertical offset from the bottom.
- **Per-cue margins override styles:** if Dialogue lines include explicit per-cue MarginL/MarginR/MarginV values, they override the style-level defaults. If the build function previously emitted `Default,,,,,`, the empty placeholders can still suppress style-level `MarginV` because they are still explicit fields. The safe pattern is either omit those fields or write the actual intent case-by-case.
- **Font resolvability:** ffmpeg/libass do not automatically see fonts inside the repo. On this Windows box, either install the OTF under `C:\\Windows\\Fonts` or burn in a space-free temp dir with `fontsdir='.'`. Otherwise you will get missing-font behavior and no visible text with no obvious error.
- **Timecode format:** Dialogue timecodes must be `H:MM:SS.cc` with exactly two decimal digits.
- **Per-cue format correctness:** The `build_ass` function must write Dialogue lines that match the Events format exactly: `Dialogue: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text`. Extra commas or missing fields corrupt subtitle parsing even when the file otherwise looks valid. If an extra placeholder is inserted before Name, the word text can shift into the Effect column and render invisibly with no explicit error.
- **VTT timestamp format:** when writing `captions.vtt` from faster-whisper `word_timestamps=True`, convert each timestamp from seconds to `H:MM:SS.mmm`. Raw values like `0.000 --> 4.240` will raise `ValueError: invalid VTT time` in `parse_vtt_cues`.
- **Word-level to phrase-level grouping:** single-word cues produce fragmented, unreadable captions. After generating word-level VTT, merge adjacent words into readable phrases using a gap threshold (e.g. >0.28s) and/or max phrase length (e.g. 90 chars / 5 words).
- **Windows/MSYS ffmpeg ASS syntax:** prefer `ass='captions.ass':fontsdir='C:/Windows/Fonts'` from MSYS2 bash; commas in MSYS args can split filter options unexpectedly.
- **Windows spaces-in-path constraint:** when `fontsdir` or the ASS path contains spaces, prefer copying into a space-free working dir and setting `fontsdir` to that temp path. In `create.py`, derive a `safe_slug` for `/tmp/<safe_slug>` before burning, then copy the final MP4 back to the project paths afterward. Spaces in `fontsdir` will break ffmpeg/libass even if the file exists.

## Renderer

Prefer regenerating final assets with `scripts/ai_channel_scripts/render.py`, which emits `captions.ass` from `captions.vtt` and writes the final MP4 to `TO UPLOAD/<slug>.mp4`. Legacy per-short build scripts exist for older shorts; treat them as repair paths only when `captions.vtt` is missing.

## Entry Point

Run from the project root:
```bash
python scripts/ai_channel_scripts/create.py <slug> "query" "script text" --seed <int>
```

**No `--project` flag exists.** `create.py` expects positional arguments: `<slug>`, `<query>`, `<script>`. Passing a non-existent flag stops with argparse usage text, not a friendly error.

SLUG pattern: `YYYY-MM-DD-<topic>-<slug>` matching the `shorts/` folder name.

Direct trailer URL shortcut:
```bash
python scripts/ai_channel_scripts/create.py <slug> "query" "script text" --trailer-url "https://www.youtube.com/watch?v=..." --voice "en-US-GuyNeural"
```
Use `--trailer-url` to skip the yt-dlp search when you already have the exact source.

## Trailer Download

Preferred path is the in-process `yt_dlp.YoutubeDL` Python API with browser headers and client fallbacks, matching the reference hoax detector project. `create.py` now cycles:
1. `android` client + Android user-agent
2. `web` client + Windows Chrome user-agent
3. generic `best` fallback + Windows Chrome user-agent

Each attempt sets `http_headers`, `retries`, and small `sleep_interval`/`max_sleep_interval` values. Use this flow instead of increasing CLI retry wrappers around `yt-dlp.exe`.

If download still fails, switch to a direct trailer source URL (`--trailer-url`) or another platform extractable by yt-dlp rather than retrying the same shell invocation unchanged.

## Script Format

- UPPERCASE throughout
- Single long line, no line breaks (entire narration is one `script.txt` line)
- Punctuated and formatted for **30-60s runtime**
- Conversational gaming news tone: direct address to viewer, present/future tense hooks
- **Mandatory open-ended closing line**: end every script with an engagement-driving question that asks the viewer to choose or share an opinion. This increases comments and watch signals. Examples: "But what do you think?" / "Will it be worth the wait?" / "Are you still playing, or have you moved on?"

- **Always pinned at 1.2x:** narration speed is fixed at `edge_tts --rate=+20%`. If audio is too short/long, adjust script length only; do not change --rate.

The generator now enforces 30–60 seconds for the final voiceover. If the generated audio falls outside this window, the build stops and reports the actual duration so the script can be adjusted before rerunning.

## Topic Selection and Trailer Sourcing

Prefer **latest news first**, then decide the framing/angle for that item rather than defaulting to negative sentiment. Use this priority order:

1. Latest official franchise/studio news for the game
2. Latest headline updates (patches, roadmap, seasons, modes)
3. Gameplay trailers or official footage for that specific update
4. Sentiment angle (positive/negative/neutral) chosen to fit the actual news

**Current working rule:** Always go with the rule as it is now—latest-news priority, keep same-game reuse safe by requiring distinct sub-topics, apply existing quality guards, and reference the Known Shorts list to avoid repeats.

**Duplicate-topic rule:** Reusing the same game is allowed, but each short must cover a distinct sub-topic. Examples of distinct sub-topics for one game: studio layoffs, patch notes, developer Q&A, trailer reveal, roadmap update, season launch, item/meta rework. If a new short would repeat a sub-topic already used, pick another news angle for that game instead.

Restated for clarity: same franchise is fine across multiple shorts. What must stay different is the specific news thread each short is about.

### Source Quality Rules for Footage and Info (effective latest rules)

Failure mode to avoid: downgrading the source just to keep the same story moving. If the cleanest path is to switch stories after a 30–60s script pass, that is acceptable; do not accept a worse visual source.

These are the hard rules, not preferences:

- **Footage:** use gameplay trailer videos from the **developer’s official YouTube channel** only.
- **Developer-focused news exception:** if the news is about a game studio rather than a specific game, use gameplay trailer footage from that studio's latest released game.
- **Verified gaming outlets:**IONAL-ONLY channels or brands widely accepted as authoritative in gaming coverage are acceptable secondary sources: IGN, GameSpot, Polygon, The Verge, PC Gamer, Kotaku, GamesIndustry.biz.
- **Leaker/data-miner info:** incorporated into narration when appropriate. Well-known leakers and data miners on Twitter/X are valid info sources for the script. Treat their claims as interesting/unverified context, not as primary source of truth unless corroborated officially. Do not frame unverified claims as confirmed facts.
- **Drop story when needed:** if the best unverified footage needs to be used to cover a topic, **do not** accept a random/unvetted creator clip. Either switch the topic or accept a relevant verified-trailer substitute for the same game.
- **Anti-pattern:** "I'll just use this random gaming-news channel video because it mentions X." Avoid completely unless the channel is an established confirmed outlet.

## Title and Filename Format

Use the reference pattern verbatim so titles are upload-ready and filesystem-safe:

```
ASSASSIN'S CREED BLACK FLAG RESYNCED SETS SAIL JULY 9! #assassinscreed #blackflag #ubisoft #gaming #remake
```

Filename rules:
- Derived from `metadata/title.txt` verbatim, so hashtags like `#gaming`, `#battlefield6`, `#bf6` are preserved when practical.
- Keep spaces in the filename. Replace only Windows-invalid characters: `<>:"/\\|?*` and control chars.
- Truncate at the end only when the fully derived slug would otherwise exceed safe Windows MAX_PATH headroom. Target the longest readable title that still fits under the limit.

## Voice Selection

The default narrator should be **`en-US-GuyNeural`** per user preference. If that voice is unavailable on a given machine, use `--voice` to override with an installed voice.

Known-working fallbacks on this Windows box: `en-AU-NatashaNeural`, `en-AU-WilliamMultilingualNeural`. `en-AU-TimNeural` is not installed here and should not be used as the default.

Available Edge TTS voices:
```bash
python -m edge_tts --list-voices
```

## Caption Proofreading

Captions are generated from faster-whisper STT word timestamps, then corrected against the original script before burning into the video.

- The script text is uppercased and split into expected words.
- A `SequenceMatcher` maps STT-recognized words back to script words.

**Python 3.11/3.13 matching-blocks tuple form:**
```python
for i1, j1, length in sm.get_matching_blocks():
    if length:
        for offset in range(length):
            recognized_to_script[i1 + offset] = j1 + offset
```

Unpacking five values from `get_matching_blocks()` will fail with `ValueError: not enough values to unpack (expected 5, got 3)`.

- Where a recognized caption word maps to a script word, the caption text is replaced with the exact script wording.
- STT timing is preserved; only the caption text is corrected.
- This prevents Whisper typos/mishearings from appearing in the final burned subtitles.

## Known Failure Patterns

- see `references/python-difflib-getmatchingblocks-2026-06-06.md`
- see `references/youtube-dl-py-api-2026-06-06.md`

## Session Notes

- see `references/2026-06-06-source-and-narration-rules.md` for enforced source rules, narration duration behavior, shell-quoting workaround, and Docker guidance.
- see `references/ai-channel-subtitle-position-and-duration-adjustment-2026-06-06.md` for subtitle position change and narrator speed constraint.
- see `references/subtitle-burn-first-frame-verification-2026-06-06.md` for the verified subtitle burn command pattern and first-frame verification routine.
- see `references/subtitle-visibility-debug-2026-06-06.md` for prior subtitle-visibility debugging findings.

## Background Process Behavior

- Prefer official gameplay trailers and official publisher/developer footage.
- Prefer trailer content that directly matches the selected news hook when possible.
- **Source rule:** the visual/trailer source must come from an official or clearly verified outlet/company channel. Do not use random or unverified YouTuber/streamer clips as the primary source. If no suitable official/verified source exists, choose a different story rather than downgrading the source quality.
- If no official trailer is immediately available, search for the next most recent official channel upload before falling back to generic gameplay clips.

## Deliverable Verification

After recreating a short, verify these artifacts exist:

1. `import-fit` local render: `shorts/<slug>/render/final.mp4`
2. Upload deliverable: `TO UPLOAD/<video_title>.mp4`
3. `shorts/<slug>/render/captions.ass` with the expected burn-in style
4. Metadata files present for upload handoff

**Do not treat absence of background logs as proof of success**—filesystem evidence is the source of truth.

**Background-review caveat:** `read_file`/`terminal` can be unavailable in background review. Absence of an error message here is not proof the render path succeeded. Insist on foreground verification, or request a foreground tool pass when strict deliverables must be confirmed.

## Subtitle Debugging/Verification (updated 2026-06-06)

- After any subtitle rebuild, extract a subtitle-active frame and check for visible text before treating the run as success.
- `captions.ass` generation success does not equal subtitles visible in the final MP4. Both must be confirmed with real tool output before completing the task.
- If `render_compare.py`-style comparisons are used, ensure the runner itself has no quoting bugs that mask failures. Space-free working directories are acceptable for comparison work until the main pipeline quoting is stable.

### Empty-Ass Guardrail (must-check before declaring success)

An ASS file can parse successfully, be accepted by ffmpeg/libass, and produce a valid MP4 — but render **zero subtitles** if the Dialogue section is empty. This is a silent no-op: exit code 0, no ffmpeg errors, and no visible text.

Concrete check before and after burn:
- Before burning, parse or count `Dialogue:` lines in the exact ASS file being passed to the filter. A zero count means the burn will succeed but produce no subtitles.
- After burning, verify by vision as usual; do not trust the absence of ffmpeg errors as proof of subtitle presence.

## Subtitle Burn Method (current verified state)

- The reliable path on this Windows/MSYS ffmpeg setup is ASS burn in a space-free working dir:
  - copy `captions.ass` and `burbank_big_condensed.otf` into a temp space-free dir
  - run `ass='captions.ass':fontsdir='.'` with verified style already inside the ASS style line
- Explicit `force_style` on `ass=` is unusable on this ffmpeg build: the build returns `Error applying option 'force_style' to filter 'ass': Option not found`. Use ASS-template styling instead.
- `subtitles=` SRT burn with `force_style=` remains an acceptable fallback when ASS font resolution is problematic.

## Subtitle Failure Rules and Burn Patterns (current verified state)

If you see `Unable to parse "original_size" option value`, treat it as a quoting/path-parsing bug in the `ass=` filter on this Windows/MSYS ffmpeg build. Common causes: embedded colon/backslash translation from MSYS path expansion, and space-containing paths through the ASS filter. The shortest fix is the simple no-filtersdir burn path: copy `captions.ass` and the Burbank OTF into a space-free temp dir, then burn with `ass='captions.ass':fontsdir='.'` in a normal ffmpeg invocation. A fallback path remains SRT + `force_style` when ASS font resolution is unstable.

In general, prefer the simplest burn that works on this machine:
1. Single-pass ffmpeg burn with `ass='captions.ass'` plus an explicit local `fontsdir` in a space-free working dir.
2. Only return to more complex filter chains if the simple path fails.
3. When quoting from msys/bash is involved, test the exact command via `subprocess.run([...])` with literal path strings instead of hand-built shell snippets.

## Verified Working Subtitle Style

- Font: `BurbankBigCondensed-Bold` (internal nameID 6 / nameID 4 from the OTF; this is the string libass resolves correctly on this Windows build)
- Do NOT use `Burbank Big Condensed Bold` with spaces in the ASS style: libass will silently fall back to `Arial-BoldMT`.
- Size: `72` in the ASS template/header
- Colors via ASS style: `PrimaryColour=&HFFFFFF`, `SecondaryColour=&HFFFFFF`, `OutlineColour=&H000000`, `BackColour=&H000000`
- Outline: `3`
- Shadow: `1`
- Alignment: `5` (middle-center)
- MarginV: `10`
- The effective visual style comes from the generated `captions.ass` template. If an inline `force_style` override is present in a command, keep it consistent with the template values above.

## Subtitle Verification Rule (user preference; supported in references)

- Do not ask the user to manually inspect the finished video as the only verification.
- After running `create.py`, extract the first frame with ffmpeg and inspect subtitle visibility from the frame evidence before declaring success.
- First-frame inspection is the user-preferred verification path for subtitle visibility, not presenting the video for manual watching.
- Verification notes are kept under `references/subtitle-visibility-debug-2026-06-06.md`.
- Status checks for current shorts should use project-root relative paths instead of hard-coded absolute Windows clips paths, so the skill works across machines and background-review contexts.

## Script Execution And Behavior

- `step_render()` writes both `captions.srt` and `captions.ass` from `captions.vtt`, then burns subtitles into the final MP4 before copying to `TO UPLOAD`.
- Expected render output naming: `shorts/<slug>/render/<slug>.mp4`.
- Expected upload copy naming: `TO UPLOAD/<slug>.mp4`.
- Use ASCII-only `safe_slug` directory names when creating temporary workspaces for builds or comparisons; keep title strings separate from filesystem work paths.

## Windows Render/Upload Pitfalls

1. **Stale renders:** `process list` showing `exited` does not confirm success.
2. **Builds killed by SIGTERM (-15):** rerun and verify after interruption.
3. **Windows render lock on upload copy:** close anything holding the file before copying.
4. **`--project` flag:** `create.py` takes positional args only.
5. **MSYS startup noise:** harmless; ignore.
6. **Windows ffmpeg ASS quoting:** with MSYS2 bash and this ffmpeg build, prefer explicit named subtitle filter options:
   - `subtitles=filename=...`
   - Treat errors like `No option name near '...'` as quoting/parsing problems, not subtitle content problems.
7. **Space-free comparison/render workspace:** paths with spaces in `fontsdir` or `ass=` still fail in pipeline comparison scripts even when the main pipeline works. Use `/tmp/ai_channel_compare` or another space-free path for compare renders.
8. **Font family must match exactly:** the installed OTF name is `Burbank Big Cd Bd`, not `Burbank Big Condensed` alone or `Burbank Big Condensed-Bold` alias. libass/FFmpeg will silently fall back to Arial otherwise.
9. **ASS style vs per-cue margins:** if `build_ass()` emits empty per-cue margin placeholders, they override the style defaults. Either omit those fields or set values explicitly.
10. **Final render string shape:** use `ass='<filename>'` plus `fontsdir='...'`. For spaces, a working pattern is `ass='captions.ass':fontsdir='/tmp/<safe-slug>'` after copying the ASS/font into that safe slug dir. A raw space-containing title string in `fontsdir` will break FFmpeg's `AVFilterGraph` parser even if the file exists.
11. **`create.py` subtitle burn current verified path:** build ASS in the project `render/` dir with the desired style baked in, then copy `captions.ass` + font into a space-free temp dir and burn there, then copy the final MP4 back to the project `render/` and `TO UPLOAD/` paths.
12. **Inline `force_style` override bug:** when `create.py` constructs its own `force_style` values for subtitle burn, the command overrides template fonts/alignment/margins regardless of what the template file contains. If you rely on template-first styling, either remove that inline override or make it match the template exactly. Otherwise updates to template files will appear to be ignored.
13. **Avoid repeating the plan after diagnosis:** once the root cause is known and a corrective command is ready, run it directly. Do not continue sending investigation summaries or plan restatements in place of acting.
14. **One corrective action, not many:** after a confirmed cause, execute exactly the needed change. Extra redundant execution just adds noise and tool calls. Stop probing, stop comparing alternatives that are already known, and apply the fix.