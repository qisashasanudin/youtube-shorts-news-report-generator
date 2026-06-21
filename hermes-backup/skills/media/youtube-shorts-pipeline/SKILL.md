---
name: youtube-shorts-pipeline
description: "Produce AI Channel-style YouTube Shorts locally: script, trailer download, clip assembly, TTS, captions, ffmpeg render, and TO UPLOAD output."
platforms: [windows]
---

# YouTube Shorts Build Pipeline

USE THIS when the user wants to generate a new Short from a script/topic within a generic short-video project. For this user's specific **AI Channel** project under `C:\\Users\\qthas\\Videos\\Youtube Projects\\AI Channel`, use the more specific `ai-channel-pipeline` skill instead.

## Conventions

- Per-short folder: `shorts/<YYYY-MM-DD-slug>/`
- Required subdirs: `script`, `audio`, `captions`, `render`, `assets`, `metadata`, `output_tmp/clips`
- Final files:
  - Output: `videos/TO_UPLOAD/<TITLE>.mp4`
    - `videos/<slug>/render/final.mp4`
  - `shorts/<slug>/captions/captions.vtt`
  - `shorts/<slug>/audio/voiceover.mp3`
- This skill is shared across two projects under the same root project tree: the **AI Channel** flow and the **MashButtonGaming** flow.
- MashButtonGaming videos live at `videos/<project-id>/...`; the AI Channel videos live at `shorts/<YYYY-MM-DD-slug>/...`.
- Shared rules (script target, upload filename rule, silence-when-stuck fallback, ASS burn safety) apply to both flows unless a project-specific exception is documented here.
- Intermediates:
  - `shorts/<slug>/output_tmp/trailer_src.mp4`
  - `shorts/<slug>/output_tmp/clips/clip_*.mp4`
  - `clips.txt`, `concat.mp4`, `scaled.mp4`

## Content rules

- Only use news from the last 3 days. Reject stale topics automatically to avoid irrelevant uploads.
- Prioritize the latest official news, reputable industry articles, and verified leak/leaker signals regardless of sentiment. Do not default to negative news and do not assume a topic is about a new announcement.
- Validate the story first: if the latest relevant signal is a shutdown, delay, legal issue, layoff, or business change, that is the valid topic. Do not rewrite the narrative back into a generic reveal, launch, or update angle.
- The same game may be reused across multiple videos, but each video must cover a unique sub-topic. Examples: different updates, patches, reveals, events, interviews, or announcements about the same game.

## Unique subtopic uniqueness rule

When repeating a game across shorts, de-duplicate before rendering:

- Inspect the project's recent shorts/output history.
- If an existing sub-topic already matches the candidate topic, generate a different subtopic for the same game instead.
- Same-game reuse is allowed only when the sub-topic will be meaningfully different from prior shorts.
- The narration script is one long continuous line with no internal breaks.
- On-screen captions are extracted from the generated voiceover through STT (speech-to-text) after TTS, not derived from the script file.
- Captions are UPPERCASE and styled with heavy outline when burned into the short.
- Each video script must end with an open-ended question to drive engagement.
- Vertical Shorts must be 720x1280 with cover crop and no bars.

## Subtitle word-count policy (MashButtonGaming override)

`src/shorts_builder.py` requires the `--subtitle` argument to be **50–150 words**. This is the TTS duration guard: shorter text produces a voiceover too short for YouTube Shorts minimum length. The runtime guard is enforced in `_check_subtitle_words()` and runs before any download/TTS work. The CLI flag was renamed from `--caption` to `--subtitle` to make its purpose unambiguous: it is the TTS/subtitle text, not just a display caption.

- When the user sets a narrative target like 50–150 words, treat that target as the hard spec for the narration script and keep it over a minimum-duration gate.
- If the same narration path drives the build past a service duration limit, do not silently slice the script below target. Instead, fall back to the project's silent/source-driven flow and stop TTS-dependent steps rather than failing the script spec.
- "Silent" for this rule means **narration track absent**, not a black-screen or missing material. The source video remains visible; captions may still be burned from existing captions when available.
- **Minimum duration enforcement**: All final videos must be ≥ 30 seconds for YouTube Shorts compliance. If the generated audio + shuffled clips produce < 30s, add more trailer segments or adjust TTS rate before final render.
- Note: the CLI flag was renamed from `--caption` to `--subtitle` so its purpose is unambiguous.
- **Correction (2026-06-11):** Previous comments incorrectly stated 100-200 words. The builder enforces **50-150 words** via `len(subtitle.split())`. Our MW4 narration required trimming from ~127 → 96 words over 3 attempts. The 50-150 range is correct.

## Silence-when-stuck fallback

When narration cannot be produced, downloaded, or synced, do not stop partway through the pipeline. Switch to the silent build path so delivery still advances.

- MashButtonGaming fallback: build from the verified trailer clip + existing captions/assets without narration.
- **Scheduler bypass fallback**: when the Hermes cron scheduler gets stuck (e.g., `cronjob run` returns success but job state remains `scheduled` and `last_run_at` is unchanged), bypass it entirely by running the builder directly.
  - Command pattern: `python src/shorts_builder.py --youtube "<url>" --title "<TITLE>" --subtitle "<100-200 WORDS>"` from the project workdir
  - This executes the same end-to-end flow the scheduler would run, producing an identical final MP4 in `videos/TO_UPLOAD/`
  - After direct builder success, still perform the same verification and Telegram delivery checks as a scheduled run
  - Do not repeatedly trigger the stuck scheduler expecting it to advance; clear observed lockfiles first, then fall back to direct invocation if state still does not change
- AI Channel fallback: build from the topic/title and existing `storyboard_*.json` media files in `system_sources/...` or `references/...` instead of narration.
- If a user-facing skill such as `silentshorts` exists in the active skills list, prefer that class-level path for this host.
- Trailer priority for gaming: official trailer > official gameplay > official reveal trailer. Do NOT use streamer clips, unlicensed reaction footage, or fan edits.

## Canonical runtime

- Primary runtime: WSL Ubuntu 24.04
- Preferred venv: WSL `/root/mashbutton-venv`
  - create: `python3 -m venv ~/mashbutton-venv`
  - activate: `source ~/mashbutton-venv/bin/activate`
  - pip install from `src/scripts/requirements.txt` inside this venv
- Windows native Python remains supported when WSL is unavailable, but WSL + venv is the supported standard
- Repo path in WSL mirrors the Windows path: `/mnt/c/Users/qthas/Programming/Belajar/YouTube/youtube-shorts-news-report-generator`

## Project path rule

Use the renamed project path everywhere this skill is applied:

- Windows: `C:\Users\qthas\Programming\Belajar\YouTube\youtube-shorts-news-report-generator`
- WSL: `/mnt/c/Users/qthas/Programming/Belajar\YouTube\youtube-shorts-news-report-generator`

Do not reference the old `MashButtonGaming` folder name in new guidance.

## Existing YouTube upload module (built, ready to use)

The project includes a working YouTube upload helper at `src/scripts/youtube_upload.py`:

```bash
# First run: opens browser → user clicks Allow → saves token.json
.venv\Scripts\python.exe src/scripts/youtube_upload.py video.mp4 --title "Title #tag1 #tag2" --privacy public

# Subsequent runs: uses cached token.json (auto-refreshes)
.venv\Scripts\python.exe src/scripts/youtube_upload.py video2.mp4 --title "Another One"
```

**Auth flow**: OAuth 2.0 with `client_secrets.json` (from Google Cloud Console) + persisted `token.json`.
**Scopes**: `youtube.upload`, `yt-analytics.readonly`, `youtube.readonly`.
**Upload**: Uses `googleapiclient.discovery.build("youtube", "v3")` + `MediaFileUpload(resumable=True)`.
**CLI args**: `video_path`, `--title`, `--privacy` (private|public|unlisted), `--description`, `--tags`.

**Prerequisites**:

1. Create Google Cloud project → enable YouTube Data API v3 → OAuth consent screen → Desktop app credentials
2. Save credentials as `client_secrets.json` in project root
3. Run once to authorize; `token.json` is created and reused

See `youtube-api-setup` skill for OAuth troubleshooting patterns.

## TikTok upload module (not yet built)

TikTok Content Posting API requires a separate module. Key differences from YouTube:

| Aspect          | YouTube                     | TikTok                                             |
| --------------- | --------------------------- | -------------------------------------------------- |
| Auth            | Google OAuth 2.0            | TikTok OAuth 2.0 (different endpoints)             |
| Upload          | Single `videos.insert` call | 2-step: create session → PUT chunks → publish      |
| Scopes          | `youtube.upload`            | `video.upload`, `video.publish`, `user.info.basic` |
| Token expiry    | No expiry (refresh token)   | Access: 2h, Refresh: 1 year                        |
| Rate limits     | Generous                    | ~100 req/day (sandbox), higher in prod             |
| Review required | No (standard OAuth)         | Yes (App Review + demo video)                      |

**To build `src/scripts/tiktok_upload.py`** (after TikTok app approval):

1. OAuth flow → saves `tiktok_token.json` (client_key, client_secret, refresh_token)
2. `POST /v2/video/upload/` → get `upload_url` + `video_id`
3. `PUT` video chunks to `upload_url` with `Content-Range` headers
4. `POST /v2/video/publish/` with `video_id` + post_info (title, privacy, etc.)
5. CLI wrapper: `python src/scripts/tiktok_upload.py video.mp4 --title "Caption #gaming"`

**Blockers today**: TikTok app "mashbuttongaming-uploader" needs Products (Content Posting API), Scopes (video.upload, video.publish, user.info.basic), demo video in Sandbox, and App Review approval before production tokens work.

## WSL venv command pattern

Template:

```bash
cd /mnt/c/Users/qthas/Programming/Belajar/YouTube/youtube-shorts-news-report-generator
python3 -m venv ~/mashbutton-venv
source ~/mashbutton-venv/bin/activate
pip install -r src/scripts/requirements.txt
python src/shorts_builder.py --youtube "<url>" --title "<TITLE>" --subtitle "<SCRIPT TEXT>"
```

## Windows path rule

Use Windows-native paths only:

- Repo: `C:\Users\qthas\Programming\Belajar\YouTube\youtube-shorts-news-report-generator`
- Do NOT use WSL `/mnt/c/...` paths when the build is running on Windows
- Do not reintroduce spaces in repo paths beyond the unavoidable `C:\Users\qthas\...`
- Ensure `videos/TO_UPLOAD` exists before render

## yt-dlp rule

`yt-dlp` is installed for the active Python/Pip in the active venv. Prefer in-process use from `src/shorts_builder.py`; only fall back to shell form when the venv Scripts directory is on PATH.

Source size cap:

- Reject trailer candidates larger than `500 MB` before download.
- If a selected source exceeds that cap, stop and reconsider the candidate/source instead of downloading.

## Asset/folder rules

- `videos/` is gitignored; keep all working outputs and render intermediates under it
- `assets/` is tracked in git and must remain present after clone; it holds subtitle fonts such as `assets/fonts/whoosh/`
- Do not place source files inside `videos/`; all pipeline source stays under `src/`

## YouTube download workaround

YouTube extraction can fail with `HTTP Error 416` / `getaddrinfo failed` / deprecation warnings when calling `yt-dlp` as a shell subprocess. The reliable workaround is to import `yt_dlp` in-process and use browser-impersonation headers + client fallbacks:

- Call `yt_dlp.YoutubeDL(...).download([url])` instead of shelling out
- Use multiple attempts with different `player_client` values: `android`, then `web`
- Provide matching `http_headers`: `User-Agent`, `Referer`, `Origin`
- Fall back to `best` if `bestvideo+bestaudio` fails
- Keep retries low (`retries=2`, `fragment_retries=2`) but real

Reference implementation pattern for `step_download_trailer()`:

```python
from yt_dlp import YoutubeDL

ANDROID_UA = 'Mozilla/5.0 (Linux; Android 14)...Chrome/124.0.0.0 Mobile Safari/537.36'
WEB_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...Chrome/124.0.0.0 Safari/537.36'


def _build_headers(url, user_agent):
    return {
        'User-Agent': user_agent,
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': url,
        'Origin': 'https://www.youtube.com',
    }


attempts = [
    {
        'format': 'bestvideo[ext=mp4][height>=1080]+bestaudio[ext=m4a]/best[ext=mp4][height>=1080]/best[ext=mp4]/best',
        'extractor_args': {'youtube': {'player_client': ['android']}},
        'user_agent': ANDROID_UA,
    },
    {
        'format': 'bestvideo[ext=mp4][height>=1080]+bestaudio[ext=m4a]/best[ext=mp4][height>=1080]/best[ext=mp4]/best',
        'extractor_args': {'youtube': {'player_client': ['web']}},
        'user_agent': WEB_UA,
    },
    {'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
     'user_agent': WEB_UA},
    {'format': 'best', 'user_agent': WEB_UA},
]

for attempt in attempts:
    ydl_opts = {
        'format': attempt['format'],
        'outtmpl': outtmpl,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'retries': 2,
        'fragment_retries': 2,
        'socket_timeout': 15,
        'timeout': 60,
        'merge_output_format': 'mp4',
        'http_headers': _build_headers(url, attempt['user_agent']),
    }
    if 'extractor_args' in attempt:
        ydl_opts['extractor_args'] = attempt['extractor_args']
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
```

This pattern is known-good from the user's `video-ai-hoax-detector-api` project. The 1080p+ constraint is mandatory unless the user explicitly wants lower-quality fallback.

## Trailer resolution preference

Prefer 1080p+ source when downloading trailers:

- First choice: `bestvideo[height>=1080][ext=mp4]+bestaudio[ext=m4a]`
- Fallback: `best[height>=1080][ext=mp4]`
- Last fallback: `best[ext=mp4]`

This avoids landing on a lower-resolution MP4 when a higher-quality alternative is available.

### Direct trailer URL option

`step_download_trailer(short, query, trailer_url=None)` accepts a direct video URL. Use it when the user provides a specific YouTube/YT trailer link. The same 1080p+ format selector applies.

## Title/filename source of truth

- The upload filename must match the title text closely, but must NOT include the phrase `and here's what you need to know` anywhere in the filename.
- Hashtags must appear in the final filename; use at least 5 hashtags (`#TAG1_#TAG2_...`) appended after the sanitized title prefix.
- The deliverable MP4 filename should be safe for platform transport: strip `#` symbols from the filename when delivering via Telegram; keep hashtags in the caption/description text instead.
- Do not derive the upload filename from the short folder name or any date prefix.

## Render settings

Preferred encode defaults for YouTube Shorts:

- `-c:v libx264 -preset medium -crf 18`
- `-c:a aac -b:a 192k`

`veryfast`/`crf 20` is a fallback only if render speed matters more than quality.

## Build sequence

1. Script: write narration to `script.txt`; auto-create/fill `metadata/title.txt` if missing.
2. TTS: generate `audio/voiceover.mp3` from hashtag-stripped narration.
3. STT: create `captions/captions.vtt` from the generated voiceover.
4. Trailer: download or reuse `trailer_src.mp4`.
5. Clips: extract enough clips to cover narration duration (adaptive count; reuse existing `clip_*` if present and sufficient).
6. Concat + scale to 720x1280.
7. Burn captions and hard-trim to voiceover duration, then copy to `TO UPLOAD/<title>.mp4`.
8. Preserve a `.baseline.mp4` fallback before overwriting final if rollback is needed.

## Subtitles / ASS config

- ASS base style is the single source of truth for font family, size, outline, bold, alignment, and margins. Keep event lines as plain uppercase text; do not duplicate style settings inline in `force_style` in a way that conflicts with the ASS style.
- ASS Dialogue line format for one-word cues: use exactly nine fields before the text (`Dialogue: 0,start,end,Style,,Effect,,Text`), leaving name/margin/effect commas empty. Missing commas cause libass to drop the whole cue.
- ASS header must contain exactly one `[V4+ Styles]` section. Duplicate headers break parsing on some players/ffmpeg builds.
- On this Windows host, libass/ffmpeg may silently fall back to a system font even when the local font file exists. Force resolution with an absolute `fontsdir` pointing at the exact font folder and `FontName=<ExactFamilyName>` in `force_style`.
- Extract the exact font family name from the font file metadata (not guessed) before setting `FontName` or `Style: Default,Fontname,...`.
- Current working Whoosh config: 100pt, white fill, black 3px outline, `Alignment=5` (center-upper), `MarginV=240`. Treat these as the starting baseline; change only after visual confirmation.

## Render path correctness

- `src/shorts_builder.py` must pass the real `reordered`, `audio`, `ass`, and `font_dir` into the ffmpeg render call. Do not redirect render CWD from `work`; absolute input paths plus repo-root CWD are more reliable on Windows.
- Build the subtitle `ass=` filter path directly from the Path object; do not reconstruct it from `REPO.relative_to(...)` because intermediate `videos/<slug>/` paths already resolve from repo root without rewrites.
- Build the full filter expression in Python and pass it as one `-filter_complex` argument list entry. Avoid nested quoting of the filter string itself.
- Use absolute Windows-native paths in `subtitles=...` and `fontsdir=...`. Avoid relative paths that depend on the working directory being exactly the project root.
- Final MP4 must be written directly to `videos/TO_UPLOAD/<TITLE>.mp4` using `args.title` verbatim. Do not derive the deliverable filename from the project folder or an intermediate name.
- If a background render is killed before completion, restart it with the same exact title and inputs. Partial output is not valid.

## Frame verification requirement

- Always verify subtitle visibility with a frame at a **known active cue timestamp**.
- The probe timestamp should be driven from the generated ASS/VTT cue list, choosing the middle of an early visible cue (for example, `00:00:06.50`–`00:00:08.50` for a first cue that starts around 6–9 seconds).
- Always verify subtitle presence with an actual frame inspection after render, not only file duration/size or `ffprobe` stream listings.

## Hashtag handling

Strip hashtags from the TTS input before generation so the voiceover does not read them aloud. Keep hashtags in `script.txt`, `metadata/title.txt`, and the final upload filename/metadata/description.

## Unified builder scripts

- `src/shorts_builder.py` is the current one-shot builder for MashButtonGaming. Run it as: `.venv\Scripts\python.exe src/shorts_builder.py --youtube "<url>" --title "<TITLE>" --subtitle "<SCRIPT TEXT>"`. TTS duration is driven directly by `--subtitle` length.
- `--subtitle` accepts either raw subtitle text or a path to a text file. The builder reads the file content when the provided path exists, so callers can pass `--subtitle tmp/rtx-spark-subtitle.txt` directly.
- `--subtitle` must be 50-150 words. The builder enforces this at runtime in `_check_subtitle_words()` and aborts before download/TTS if outside the range.
- **Narration input format**: The `--subtitle` argument expects normal sentence-case paragraphs with conversational phrasing — NOT the rendered ASS output format (which is one-word-per-line ALL CAPS). The builder internally converts to ASS. Do not pass pre-formatted ASS text.
- **Hashtag handling in upload**: The `youtube_upload.py` script extracts hashtags from the `--title` stem and moves them to the video description. The YouTube title will be the clean text without hashtags. This is intentional — do not remove hashtags from the title stem to preserve the filename convention.
- Legacy scripts have been cleaned from `videos/`, `src/scripts/`, and the repo root. Do not reference `apps/shorts_builder.py`, `scripts/render_now.py`, `scripts/videos/`, or `src/scripts/*.py`.
- Source code isolation rule: keep all source code under `src/`. No Python or shell scripts should live in `videos/`, the repo root, or other asset folders.
- **Global builder-only rule**: always build through `src/shorts_builder.py` with dynamic CLI args (`--youtube`, `--title`, `--subtitle`). Do not create per-video wrapper scripts in `src/scripts/` or the repo root for one-off builds. This keeps tooling unified and easier to debug across sessions.

## Proposal-first workflow and delivery contract

For this project, new Shorts are NOT built automatically. The scheduler must stop after proposing a candidate story on Telegram and must wait for the user's explicit approval before any build, render, or upload step.

**NEW: Draft-first workflow (2026-06-15)** — Before any build, always send the **narration draft** to the user for review. The user will often request revisions (fact corrections, tone adjustments, punctuation fixes). Do NOT run `shorts_builder.py` until the user explicitly approves the draft.

Telegram delivery status must be reported truthfully:

- A successfully built MP4 in `videos/TO_UPLOAD/` is a local build artifact, not a delivered video.
- `send_message` with `MEDIA:` that returns a timeout warning means the adapter stalled during upload; do not treat it as delivery success and do not blind-retry the same call.

Filename sanitization for platform delivery:

- Sending to Telegram is safest with filenames that do not contain `#`; strip hashtags from the deliverable filename while keeping hashtags in the title/description/caption metadata.
- Hashtags still belong in the final title text and metadata; only the filesystem filename is stripped for transport compatibility.

Upload-only after explicit approval:

- YouTube, TikTok, or any other upload must never proceed without a clear approval message from the user.
- Preferred commands/expressions that count as approval: `ok`, `upload`, `approve`, `send`, or similar affirmative statement.
- When in doubt, ask once and stop.

## Manual Telegram-to-YouTube/TikTok upload flow (approval-gated)

When the user approves an upload after Telegram delivery:

- Stop and report if upload/auth stalls or freezes; avoid blind retries.
- Required user actions for a first-time platform path: provide any needed OAuth/app credentials safely and explicitly approve the upload step.
- TikTok: manual-first only. Do not auto-upload to TikTok and do not add TikTok automation to the scheduler.
- The builder runs on Windows native `.venv` (Python 3.11+/3.13). WSL references have been removed from source and docs; Windows is now the canonical runtime.
- When a patch corrupts `src/shorts_builder.py`, recover with `git checkout -- src/shorts_builder.py` before editing again. Blind full-file rewrites via patch tools tend to inject bad escapes.
- Local temp state must not live under `tmp/` or any top-level temp root. Keep all intermediates under the project video folder.
- Keep the legacy `src/scripts/pipeline/run.py` path for AI Channel repos when present; prefer `src/scripts/shorts_builder.py` for MashButtonGaming.
  - Output: `videos/TO_UPLOAD/<TITLE>.mp4` plus generated intermediates inside `videos/<slug>/`.
  - The script uses a segment + concat + scale + audio mux + verify flow and references the proven Stuntman Hollywood / Silent Hill render layout as the gold standard.
  - The render step must write directly to `videos/TO_UPLOAD/<TITLE>.mp4` using the same relative from-project-root ffmpeg command shape, then verify that exact path. Do not render to a temporary `render/final.mp4` and copy afterward.
  - The final MP4 filename must match `--title` verbatim. Do not derive the deliverable filename from the project folder or an intermediate name.
  - Subtitle styling must be controlled from the ASS style line, not from inline per-cue overrides or conflicting `force_style` params. Use the base `Style:` line for font size, outline, bold, alignment, and margins; keep event lines as plain uppercase text.
  - Adaptive clip selection should match the full TTS duration. Do not hardcode a 30-second cap unless the user explicitly asks for a maximum duration.
- One-shot builder maintenance rule: any fix to trailer download, TTS, caption generation, or ffmpeg subtitle burn must be applied in `src/scripts/shorts_builder.py` itself. Treat wrappers and caller instructions as the caller's responsibility; fixes must live in source so repeated runs stay consistent.
  - Builder guardrails to encode in `shorts_builder.py`: reject subtitle word counts outside 100-200 words before TTS; fail immediately if the configured subtitle font directory is missing; do not silently fall back to a non-project font.
  - YouTube URL validation must happen before any script/caption/asset work. Reject invalid or incomplete links up front so a build never advances on a bad trailer reference.
  - Trailer duration guard: prefer trailers shorter than 5 minutes. If the chosen official trailer exceeds that limit, skip it and select a shorter candidate before downloading.
  - Reuse guard: if `clips/trailer_full.mp4` already exists and is non-empty, skip redownloading and proceed directly to TTS/editing.

- Optional `--trailer-url` bypasses search-based trailer discovery when a direct link is available.
- The builder auto-fills `metadata/title.txt` if missing, adapts clip count after TTS duration is known, reuses existing trailer/clip intermediates when valid, and preserves a `.baseline.mp4` fallback before overwriting `final.mp4`.
- Output: `TO UPLOAD/<title_from_metadata>.mp4`.

### Efficiency notes

- Re-run only the stages you need: if only subtitles changed, regenerate `captions.vtt` and rerun the final render. If only quality/tail trim changed, regenerate from `scaled.mp4`.
- Reuse `shorts/<slug>/output_tmp/trailer_src.mp4` and `clip_*.mp4` when they already exist and are valid. Re-extraction is not required for metadata/TTS-only changes.
- Adaptive clip count prevents extracting dozens of unused clips for short narration; this saves disk churn and redu课 redundant concat/scale work.

## Pitfalls

- ffmpeg subtitle paths in Windows must escape `\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\`, `:`, and `'` inside `subtitles=...:force_style=...`.
- Build scripts hardcoded to WSL paths break on Windows runtime even when WSL paths resolve in some contexts.
- Non-age-restricted trailer selection: prefer official gameplay/trailer records; when a target video is age-restricted or login-walled, switch to another official source instead of halting.
- `src/shorts_builder.py` ignores `--caption`; use `--subtitle` and submit 100-200 words to ensure TTS generates voiceover long enough for a valid YouTube Short. Short `--subtitle` text produces a 4s voiceover; the new runtime guard rejects `--subtitle` outside 100-200 words.
- `--subtitle` is the narration script for TTS, not only display captions. Treat it as the script text and length matters for voiceover duration.
- When reverting segmented-edit logic in `shorts_builder.py`, remove all stale references to renamed variables such as `raw_parts`; otherwise segment counting and duration checks raise `NameError` after the refactor.
- When subtitle only needs refreshing, prefer subtitle-only rerender paths rather than full pipeline rebuild to save download/encode time.
- Ollama install/launch is environment-specific; capture setup commands, not failure assertions, if guidance is needed.
- Script punctuation is not optional. A single-line narration script must preserve commas, periods, question marks, exclamation points, em dashes, and apostrophes. Missing or stripped punctuation causes flat, rushed TTS output and breaks faster-whisper word-level caption alignment. Before rebuild, verify `script.txt` ends with punctuation and has no accidental line breaks.
- Caption words proofread against original script before final render. Contracted/run-together ASR tokens and near-match spelling errors must be mapped back to the script wording. If the mapped word does not exactly match the script, replace it with the closest script word. Exact script text is preferred; close matching is only a fallback when exact mapping could not be established.
- Background rebuilds can be interrupted (exit -15). If a background job is killed before completion, restart it with the same seed rather than assuming partial output is valid.
- Not all files in `TO UPLOAD/` can be rebuilt with `create.py`. Older items may lack the required `shorts/<slug>/script`, `audio`, and `captions` structure. Confirm folder layout before assuming a rebuild is possible.
- Do not mix builds for different games/topics in the same session queue unless the user explicitly requests it. Switching topics mid-stream (`bf6` after `dmz`) wastes render time and creates confusion.
- Platform delivery timeouts are transport-layer issues, not file issues. `send_message` Telegram timeout means the adapter stalled during upload. The MP4 can still be locally valid and complete; do not retry the same failing `MEDIA:` send. Treat build success and platform delivery as separate phases.
- When a background process completes, always check the process result/exists before moving on. Do not assume completion without verification.
- Duration edge case (June 10, 2026): Final render hit 29.1s — **just under YouTube Shorts 30s minimum**. Fix: add one more 5s trailer segment in clip assembly or slightly slow TTS rate (`rate=\\\"-5%\\\"`) to push past 30s before final render.
- **Duration issue (June 15, 2026)**: 79-word narration at `+25%` TTS rate produces ~23s — **still under 30s minimum**. Options: increase narration to 95-150 words, or slow TTS rate in `shorts_builder.py` (`--rate +25%` → `+0%` or `-10%`).
- Subtitle word count clarification: The builder's `_check_subtitle_words()` enforces **50-150 words** (not 100-200 as some comments state). Count with `len(subtitle.split())` before submitting. Our MW4 narration required trimming from ~127 → 150 words over 3 attempts.

## Windows ASS/libass subtitle burn failure mode (2026-06-06)

On this Windows host, libass via ffmpeg can accept an ASS file yet still fail to render visible subtitles. Symptoms:

- `Parsed_ass_0` reports `Bad timestamp` repeatedly for every cue.
- Final MP4 is produced with no visible caption text.
- This occurs even when the ASS file contains valid quoted timestamps and simple dialogue lines.

Current workarounds:

- Build repo-relative POSIX paths for video, audio, ass, font, and output.
- Launch ffmpeg with `cwd=REPO` so those relative paths resolve correctly.
- Do not pass Windows absolute paths in `ass=` or `fontsdir=`. The ffmpeg/libass build on this host rejects them with `No option name near 'C:/Users/...'`.
- Rebuild after changing subtitle text/duration; do not rely on reused stale `reordered.mp4` or `captions.ass` from a previous shorter script.
- When content changes, rerun the full builder or at least the TTS/caption/render stages so segment count and cue timing stay synchronized.

### Windows subtitle filter path and quoting rule (2026-06-06)

When the builder work directory is under `videos/<slug>/`, build the subtitle filter path from repo-relative POSIX paths and run ffmpeg with `cwd=REPO`. Do not use absolute Windows paths inside `subtitles=...` or `fontsdir=...` on this host — the ffmpeg 8.1.1 Windows build misparses absolute paths and emits `No option name near 'C:/Users/...'`, causing subtitle burn to abort.

Working pattern (single-pass, repo-relative paths, `cwd=REPO`):

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

Known-bad patterns on this host:

- `subtitles='C:/Users/.../captions.ass':fontsdir='C:/Users/.../fonts'` → parser error `No option name near 'C:/Users/...'`
- `ass='videos/<slug>/captions.ass':fontsdir='assets/fonts/<slug>'` with `cwd=work` → also fails because the relative path is resolved from `work`, not from `REPO`

Frame verification rule:

- Inspect a frame at a timestamp where a cue is known to be active. Checking an arbitrary timestamp commonly produces a false "no captions" result.
- Always verify subtitle presence at an active cue timestamp after render, not only file duration/size.

# Project source code isolation (project root layout)

All project source code must live in the project root tree, not in asset or output folders.

Required tree:

- Project root: `C:\Users\qthas\Programming\Belajar\YouTube\MashButtonGaming`
- Source code: `src/`
- Assets/output: `videos/`, `assets/`

Rules:

- All `.py` and `.sh` source files belong under `src/` by default.
- Do not place source files under `videos/`, the repo root unless they are the canonical entrypoint, or any folder that also stores rendered assets.
- If script placement is ambiguous, prefer `src/scripts/` or another explicit `src/` subfolder.

Why:

- Asset/output folders such as `videos/` change with each project run.
- Stray source files in output folders cause path collisions, stale hardcoded paths, and accidental execution of outdated session scripts during rebuilds.
- Surfaces rules early via `find` to avoid working from bad cwd conventions.

## Subtitle placement guide

User preference: subtitles must be visible and readable on a 9:16 short.

- Visibility is the ONLY success criterion. If a build produces no visible captions, treat it as a failure regardless of whether ffmpeg exited successfully.
- Preferred starting baseline: **centered** (`Alignment=5`) if it renders visibly.
- If `Alignment=5` produces visible text, use it. If centered alignment is invisible with the current font/source, immediately fall back to **bottom-center** (`Alignment=2`) with increased `MarginV` to push text above the YouTube UI overlap area.
- Always verify subtitle visibility with a frame at an active cue timestamp before claiming the render is done.
- This project prefers center alignment, but readable bottom-center beats invisible centered text every time.

## Custom font rule

If the user supplies a font archive (e.g. `C:\\\\Users\\<user>\\Downloads\\<FontName>\\Font.zip`), treat it as the intended subtitle font for that render.

Requirements:

- Font zip contents must be extracted under the project at `assets/fonts/<font-slug>/`.
- In `captions.ass`, set `Fontname=<Fontname>` from the actual font file family metadata (do not guess).
- Set `fontsdir=<project>/assets/fonts/<font-slug>` so ffmpeg/libass can resolve the file in WSL.
- Keep the ASS style's per-cue `MarginL,MarginR,MarginV` empty so style-level margins apply.
- When the font is clearly a display or comic font, avoid bottom flush; raise `MarginV` if needed for safe-area visibility.

### Whoosh font setup example

```bash
unzip -o 'C:/Users/<user>/Downloads/Whoosh-Font.zip' -d "<project>/assets/fonts/whoosh"
```

Then include it in the WSL render:

```bash
ffmpeg -y -i clips/reordered.mp4 -i audio/voiceover.mp3 \
  -filter_complex '[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,subtitles=captions/captions.ass:fontsdir=assets/fonts/whoosh[v]' \
  -map '[v]' -map 1:a -c:v libx264 -c:a aac -shortest render/final.mp4
```

## Clip assembly rule

Use fixed-length trailer chunks with randomized start offsets, then assemble them in extracted order to match narration length exactly. Do not shuffle chunk order after extraction.

Requirements:

- Split the full verified trailer into **exact fixed-length chunks**; default chunk size for this user is **5 seconds** unless overridden.
- Do **not** extract segments sequentially from start=0. Pick a random start time across the full source duration for each chunk so the edit doesn't play through the trailer linearly.
- Keep chunks in the order they were extracted; do **not** shuffle the segment list before concatenation.
- Concat enough chunks to reach the narration duration, then trim to the voiceover length.
- Never loop the first few seconds of the source just because earlier logic hardcoded `-ss 0`.
- Verify `reordered.mp4` duration matches target before render.

### User preference note

When reordering or concating loaded chunks, do not reconstruct the entire trailer if only one chunk is missing or needs replacement. Use in-place replacement at the exact load position so fewer chunks are re-encoded and the change stays minimal.

## WSL render script invocation rule

Render scripts that use positional parameters or contain `'` characters must be invoked by absolute POSIX path through WSL.

Requirements:

- Write WSL scripts using forward slashes and paths under `/mnt/c/Users/<user>/...`.
- From Windows, invoke as: `wsl -d Ubuntu bash <absolute POSIX script path>`.
- If bash returns `script: No such file or directory`, verify the WSL-side path by running `wsl ... ls <path>` before editing.
- Do not rely on `bash -c "<cmd>"` for long ffmpeg commands unless the command is quoted without `'`.

## Caption format requirement

- Caption cues should be **1 word at a time** unless the user requests another cue grouping.
- Group faster-whisper word timestamps singly, then merge only when natural phrase boundaries occur.
- Edge-TTS speech is the only enabler for one-word visual cues; preserve punctuation in the narration script so TTS pacing matches the word timings exactly.
- If re-burning only (no full rebuild), the VTT must be valid:
  - Include `WEBVTT` header.
  - Have a blank line between cue blocks.
- Caption cues should remain UPPERCASE when burned into the short.

## Subtitle regression isolation: MVP vs legacy render

When subtitle burn is suspected broken, build a minimal competing subtitle render path and compare on the **same source assets** instead of rerunning the full pipeline.

Working pattern (WSL-safe):

```bash
ffmpeg -y -ss 0 -t <audio_dur> -i clips/trailer_source.mp4 -i audio/voiceover.mp3 \
  -filter_complex '[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,subtitles=captions/captions.vtt[v]' \
  -map '[v]' -map 1:a -c:v libx264 -c:a aac -shortest render/final.mp4
```

Judge success by a subtitle-active frame, not by whether an MP4 is produced.

## Subtitle word-count policy

The narration text passed to `src/shorts_builder.py --subtitle` must be under 150 words.
Keep the script concise — under 150 words — while still preserving the required opening/closing structure.

## Upload title and metadata hygiene

- Never include hashtags in the YouTube title. Move hashtags into the description and into the tags list instead. Enforce this in the upload helper before upload, and treat title + description as the uploader outputs, not the raw filename or proposal text.

## Editorial log updates after successful upload

After every successful YouTube upload:

- Add the story to `editorial_state.json` `used_stories`.
- Increment the corresponding date in `daily_uploads`.
- Do this immediately after confirming the upload returned a valid video response.

## Narration script format

Use one long narration line without internal line breaks, but keep punctuation meaningful:

- Store narration in `script.txt` as a single continuous paragraph with no manual line breaks.
- **Preserve punctuation: commas, periods, question marks, exclamation points, em dashes, and apostrophes must remain intact in the single line.** Punctuation drives TTS pacing and faster-whisper caption timing; stripped punctuation commonly produces flat, rushed, or machine-like narration and poor cue alignment. The user explicitly requires proper punctuation for TTS quality (confirmed 2026-06-15: "The tts needs it" — narration without punctuation produces bad output).
- Treat `script.txt` as the TTS input only, not as the on-screen subtitle source.
- Do not derive captions from the narration script directly.

## Random-start fixed-length clip selection

When splitting trailers into 5-second pieces, do not extract them linearly from `ss=0`. Use a random start per segment so the edit does not play through the source sequentially.

Requirements:

- Source trailer duration is read with `ffprobe`.
- For each segment: choose a random start between `0` and `video_duration - segment_duration`.
- If `video_duration < segment_duration`, allow reuse from earlier segments, but prefer spacing across the source. Do not just loop from `ss=0` repeatedly unless the user explicitly asks.
- Verify actual chunk start diversity and final edit duration before render.
- Rebuild from `build_edit.py` when changing chunks; reusing an old `reordered.mp4` can show stale ordering.

## Narration opening/closing structure

Use this exact subtitle structure for every generated Short:

- First sentence: hook/context followed by `and here's what you need to know.` That phrase must appear inside the first sentence, before any factual bullets.
- Closing engagement sentence: must start with `but what do you think?` and the same sentence must end with a question mark.

Correct:

- `Battlefield 6 Season 3 Blastpoint is almost here and here's what you need to know. ... but what do you think? Will Blastpoint bring Battlefield 6 back to the top of the shooter list?`

Incorrect:

- Separating the bridge into its own sentence.
- Closing with anything that does not start with `but what do you think?`.
- Closing without a trailing `?`.

The scheduler prompt and persistent memory are the source of truth for this copy rule. Do not hardcode subtitle opening/closing validation inside `src/shorts_builder.py`; enforce it at generation/scheduling time so it stays flexible without rebuilding the builder.

## Project portability/GitHub readiness

Target machine-independent operation with minimal Hermes dependency:

- Capture executable commands in `README.md` and `docs/PIPELINE.md`.
- Keep absolute host-specific paths to a minimum; project-relative paths are preferred.
- Document nonstandard installs, such as WSL Ubuntu render path and custom fonts under `assets/fonts/<slug>/`.
- Store exact yt-dlp invocation and fallback sequence so another device can render without Hermes context.
- Replace single-use session scripts with reusable `scripts/` helpers when a pattern repeats.

## Caption punctuation behavior

Generate captions from STT on the narration audio, but keep them readable at 1 word per cue:

- Edge-TTS can call out missing punctuation as missing; preserve commas, periods, `?`, `!`, `—`, and apostrophes in the narration script so the TTS does not sound flat.
- Caption cues should remain UPPERCASE when burned into the short.
- If STT punctuation looks wrong after regeneration, fix the narration script and regenerate the voiceover before captioning, or apply a small caption cleanup pass in `captions.vtt`.
- Keep a `captions/captions.srt` backup when you want human-readable subtitle text even if the render path uses VTT.

## Separate subtitle transcription

Generate on-screen subtitles separately from the narration audio:

- Run speech-to-text on the generated voiceover (`audio/voiceover.mp3`) to produce `captions/captions.vtt`.
- Preserve or improve word-level timing accuracy through actual audio transcription.
- Preferred burn path: ffmpeg `subtitles=` with that VTT, producing a final render in one pass.
- A helper like `shorts/<slug>/render/apply_subs.py` is useful for subtitle-only regeneration: it takes an existing `scaled.mp4` and burns captions without redownloading/reencoding the source trailer.

## Trailer selection rule

Choose footage in this order:

1. Official video about the topic itself, from the developer/publisher channel.
2. If no official topic video is available, use official gameplay footage from the studio's latest released game.
3. Do not use unrelated official game footage just because it is from the same studio.

Always verify the selected YouTube video is downloadable before building.

## TTS options

### Edge-TTS (preferred)

- **Edge-TTS**: default for new builds using `C:\Users\qthas\AppData\Roaming\Python\Python313\Scripts\edge-tts.exe`.
- Current default voice: **`en-US-BrianMultilingualNeural`** at **`+25%`** rate.
- Allow voice overrides from environment/config if the user requests a different voice, but do not hardcode other voice defaults.
- This host has had issues with some Piper models sounding robotic/repetitive for short-form narration. Keep Edge-TTS as the default TTS unless the user explicitly requests Piper.

### Piper TTS

- **Secondary local TTS for this host**: install Piper TTS under a dedicated WSL venv.
- Only generate voiceovers with Piper when explicitly requested by the user.
- Setup commands:
  ```bash
  wsl -d Ubuntu -e bash -lc "python3 -m venv /mnt/c/Users/qthas/.venvs/piper-tts && \
    /mnt/c/Users/qthas/.venvs/piper-tts/bin/pip install --no-cache-dir piper-tts && \
    mkdir -p /mnt/c/Users/qthas/.piper/voices && \
    cd /mnt/c/Users/qthas/.piper/voices && \
    curl -L -o en_US-lessac-medium.onnx https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx && \
    curl -L -o en_US-lessac-medium.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
  ```
- Piper invocation pattern:
  - **Prefer stdin redirection** when passing script text to Piper in WSL, because `-t "$text"` breaks on apostrophes and quotes in the script. Use: `cat script/script.txt | piper ... -f audio/voiceover.wav`
  - **Quoting fallback**: if you must pass inline text, wrap in single quotes and escape internal single quotes as `'\''`; otherwise use stdin.
- PIPER QUIRKS:
  - Piper often returns `exit 0` even on empty/null input, producing a tiny/empty `.wav`. Always check `ffprobe` duration / file size before captioning.
  - After TTS, convert to MP3: `ffmpeg -y -i audio/voiceover.wav -ar 24000 -ac 1 -b:a 64k audio/voiceover.mp3`
  - Keep the `.wav` until MP3 is verified, then delete to save space.
- `references/trailer-agegates-and-footage-verification-2026-06-06.md` — Age-gated YouTube video rule (high-yield failure mode in this session):
  - When `yt-dlp` responds with "Sign in to confirm your age" / age-restricted error, do **not** retry the same URL.
  - Switch to another official State of Play recap or gameplay video that is not age-gated.
  - Always probedownload one frame with `vision_analyze` when a downloaded trailer is from a recap/bundle show, not a direct game trailer.
- `references/trailer-agegate-workaround-2026-06-10.md` — Documented working non-age-restricted mirror for MW4 reveal trailer (`-Zp2CM6yVFI`). Pattern: search for same official trailer under different video IDs/regional uploads.
- Footage verification rule:
  - After every trailer download, extract a probe frame at `00:00:03` (`-ss 00:00:03 -frames:v 1`) and inspect it.
  - If the frame shows recap graphics, channel overlays, or unrelated game footage, discard and redownload from a different URL immediately.
  - Confirm at least one frame contains the target game's UI/logo/character before building the edit.
- Piper invocation pattern (use stdin for long/custom text to avoid shell-quoting failures):
  ```bash
  cat script/script.txt | /mnt/c/Users/qthas/.venvs/piper-tts/bin/piper \
    -m /mnt/c/Users/qthas/.piper/voices/en_US-lessac-medium.onnx \
    -c /mnt/c/Users/qthas/.piper/voices/en_US-lessac-medium.onnx.json \
    -f audio/voiceover.wav
  ```
  Then convert to MP3:
  ```bash
  ffmpeg -y -i audio/voiceover.wav -ar 24000 -ac 1 -b:a 64k audio/voiceover.mp3
  ```
- Outputs: `.wav` at 22050 Hz mono → convert to 24kHz mono MP3 before STT/captioning.

- `references/ass-burn-verification-2026-06-06.md` — Verified behavior: ASS subtitle burn with ffmpeg `ass` filter does **not** create a separate subtitle stream in the output MP4. Burned-in subtitles are part of the video frames. Do not verify subtitle presence with `ffprobe` stream listings.
- `references/windows-ffmpeg-subtitle-burn-quirk-2026-06-06.md` — Windows ffmpeg 8.1.1 subtitle path parsing bug and repo-relative `ass=...:fontsdir=...` fix with `cwd=REPO`
- `references/windows-ffmpeg-vtt-path-quirks.md` — Windows subtitle path/format pitfalls and fixes for ffmpeg ASS/VTT subtitle burning.
- `references/youtube-shorts-pipeline-bugfixes-2026-06-05.md` — Session-specific fixes: `txt.isdigit()` caption filter, ASS font change to `Burbank Big Condensed`, and upload filename derivation bug.
- `references/youtube-shorts-subtitle-font-fix-2026-06-06.md` — Caption burn fix: use local Burbank `otf` path, keep template/format key names aligned, and rebuild after changing subtitle settings.
- `references/custom-font-install-and-ass-usage.md` — How to install a user-supplied font zip under `assets/fonts/<name>/`, set `fontsdir` and `FontName`, keep ASS margin fields empty for style-level layout, and verify rendered text.
- `references/clip-builder-nonlooping-fix-2026-06-06.md` — Fix for looping trailer edits: switch from always starting at 0 to random-start fixed-length segment extraction capped at source duration.
- `references/shuffled-trailer-edit-2026-06-06.md` — Updated edit behavior: default to fixed 5-second shuffled chunks assembled to match narration length, with random start offsets instead of linear playback.
- `references/wsl-render-script-invocation-2026-06-06.md` — Reliable pattern for WSL ffmpeg render scripts from Windows paths, including POSIX path translation and avoiding `bash script: No such file or directory` failures.
- `references/ass-title-burn-pattern-2026-06-06.md` — Compatible ASS title-burn pattern for Windows ffmpeg/libass on this host.
- `references/whisper-tts-sync-fix-2026-06-15.md` — **ASS/Whisper sync fix**: Whisper on synthetic TTS often ends early. Patched `shorts_builder.py:_word_end()` to accept `audio_duration` and extend the last word's end timestamp to match actual audio length. Prevents ~0.3s drift at end of video.
- `references/tmpfiles-org-delivery-2026-06-15.md` — **tmpfiles.org delivery fallback**: Native Discord/Telegram media upload can fail silently or time out. Upload MP4s to tmpfiles.org API and share download link instead. Permanent user preference for this project.
- `references/search-engine-scheduler-edge-cdp-2026-06-17.md` — **Search-engine-based news scheduler with Edge CDP auto-management**: Replaced RSS feeds with Bing/Yahoo HTML scraping; auto-checks/launches headless Edge on port 9222 (survives laptop restarts); rotates 15 shooter + 6 leaker queries; dedupes against editorial_state.json; outputs 10 stories to scheduler_output.json via cronjob `no_agent=True`.

## Platform delivery and upload policy

- Default delivery: Telegram only.
- The scheduler and builder must not auto-upload to YouTube, TikTok, or any other platform.
- Any upload requires an explicit, unambiguous approval from the user.
- TikTok support, if added later, must remain manual-first and approval-gated.
- YouTube integration is manual-only today; do not extend automation for YouTube/TikTok uploads inside `src/shorts_builder.py` or the scheduler prompt.
- Existing helper: `src/scripts/youtube_upload.py`
- If TikTok support is added, it should use a dedicated manual upload helper with the same approval and credential-safety rules.

## YouTube Shorts upload rule

The source of truth for the upload filename is `shorts/<slug>/metadata/title.txt`. Final MP4 files in `TO UPLOAD` must use that title verbatim. Do not derive the upload filename from the short folder name or any date prefix.

## YouTube Shorts content constraints

Limit to news/topics from the last 3 days only. The same game may be reused across shorts only when the sub-topic is different. The narration script must be one long line with punctuation. The script must end with an open-ended engagement question. On-screen captions must be 1 word per cue from the STT-aligned voiceover.

## Stream-copy edit pipeline (2026-06-08)

Drop all re-encoding for chunk extraction, concat, and trim to eliminate timeout failures on large trailers.

Working ffmpeg commands:

```bash
# Chunk extraction (stream copy, drop audio)
ffmpeg -y -ss <start> -i trailer_full.mp4 -t <5.0> -c copy -an part_000.mp4

# Concat (stream copy)
ffmpeg -y -f concat -safe 0 -i clips.txt -c copy reordered.mp4

# Trim to exact voiceover length if needed (stream copy)
ffmpeg -y -i reordered.mp4 -t <duration> -c copy reordered.trimmed.mp4
```

Only the final subtitle-burned render re-encodes:

```bash
ffmpeg -y -i clips/reordered.mp4 -i audio/voiceover.mp3 \
  -filter_complex '[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,ass=captions.ass:fontsdir=assets/fonts/whoosh[v]' \
  -map [v] -map 1:a -c:v libx264 -c:a aac -pix_fmt yuv420p -shortest TO_UPLOAD/TITLE.mp4
```

Do not re-encode intermediate clips, concat output, or trim outputs. Final render re-encode is unavoidable because of subtitle burn + H.264/AAC packaging for YouTube.

## Editorial automation (2026-06-08)

MashButtonGaming uses a lightweight editorial state tracker instead of full automation:

- `src/editorial_state.py`: deduplication and daily upload counter
- `src/editorial_state.json`: persistent state file
- `shorts-news-scheduler`: Hermes cron job, 8x/day at 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00
- `shorts-news-watchdog`: monitors scheduler, upload, and cleanup job health
- `shorts-news-cleanup`: daily at 03:00, removes `tmp` at project root and `videos/tmp`, plus builder temp folders under `videos/` except `videos/TO_UPLOAD`

State check commands:

```bash
python src/editorial_state.py count
python src/editorial_state.py check "<TITLE>" "<URL>"
python src/editorial_state.py mark "<TITLE>" "<URL>"
```

Policy signals implemented in the scheduler prompt:

- Coverage: Military Shooter, Tactical FPS, Extraction Shooter news
- Primary franchises: Battlefield, Call of Duty, Escape from Tarkov, Rainbow Six Siege
- News age limit: last 72 hours only
- Source priority: official sources first, then trusted publications/insiders/events
- Duplicate prevention: URL and normalized title checks across runs
- Story scoring with franchise multipliers; ignore stories scoring below 50
- Daily upload cap: max 8, prefer 4-8, do not create filler
- Script format: sensational opening ending with `and here's what you need to know.`, factual body, closing with `but what do you think?`
- Title format: concise news-style, never includes the opening sentence phrase
- Footage selection: official reveal trailer > official gameplay > official update > official dev video

## Caption alignment fix (recursive strictness)

Use a multi-pass matcher instead of a single best-score scan to prevent off-sync phrases:

1. **Exact pass** — search a small forward window (`strict_match_window=6`) for a normalized exact match.
2. **High-confidence fuzzy pass** — same short window; accept `SequenceMatcher` score >= `0.88`.
3. **Best-score fallback** — scan a slightly wider window (`fuzzy_window=8`); accept the best match only if score >= `0.8`.

When a match is found:

- Use the matched token’s own timing, bounded to the next token start minus `0.02` when possible.
- Advance the cursor to `match_idx + 1`.

When no match is found:

- Use the timing of the token at the current cursor position.
- Advance the cursor by exactly `+1`.

This preserves strict 1:1 token consumption and avoids drift that caused phrase-level misalignment (e.g. `looks surprisingly polished`).

## STT typo normalization rule

Use dynamic fuzzy matching for STT token alignment instead of any hardcoded correction list or external mapping file:

- Match subtitle text words against faster-whisper word timestamps using `difflib.SequenceMatcher` similarity.
- Normalize both sides to lowercase alphanumeric before scoring.
- Scan a small window (`window=10` tokens) from the current cursor forward.
- Accept matches with similarity >= `0.75` and use that token’s timing for the subtitle word.
- Unmatched subtitle words must still consume exactly one Whisper token and advance the cursor by +1; use the timing of the token at the current cursor position, not the next token. This preserves 1:1 alignment and prevents drift when fuzzy matches fail.
- Do not maintain `.subtitles_host_rules.json`, per-game typo lists, or any static normalization file. Fuzzy matching covers existing and future STT artifacts uniformly.

## Engagement question rule

The engagement question must come from `--subtitle` text only. The builder must never append, inject, or hardcode engagement wording, and wording must not be hidden inside `src/shorts_builder.py`. Generate engagement text externally, include it in `--subtitle`, and let the builder treat that as the single source of truth.

- Treat `--subtitle` as the single source of truth for both narration and captions.
- Validate that the submitted text contains an engagement question when policy requires it; do not generate or append one.
- The narration script is one long line; if it already ends with a question, use it as-is.

## No hardcoded typo normalization in builder

Do not hardcode narrative text fixes such as `favourite -> favorite` or any other per-word spelling normalization inside `src/shorts_builder.py`.

- Typo handling must be global and dynamic, not a static mapping.
- Alignment should rely on fuzzy matching instead of manual merges.
- If handling is needed later, prefer configuration-driven rules or runtime fuzzy matching over hardcoded cases.

## Subtitle source and timing rule

Use the hand-written `--subtitle` strictly for TTS input. On-screen subtitles should come from STT result text whenever possible so on-screen words match what is actually spoken.

- Prefer STT-derived display words over hand-written text for caption cues.
- Timing should come from STT token timestamps; unmatched words should consume one token and advance the cursor by +1.
- Keep fallback timing only when STT is unavailable.

## Subtitle text sanitization rule

Sanitize `--subtitle` text before any word counting, TTS, or caption alignment passes in `src/shorts_builder.py`:

- Replace `-` (hyphen/dash) with ` ` (space) so compounds like `fans-off-guard` don’t become single merged tokens.
- Replace `—` (em dash) with `, ` (comma + space) to preserve readable pauses instead of collapsing clauses into one word.
- After symbol replacement, collapse any resulting consecutive whitespace down to a single space before further processing.
- Sanitization must happen immediately after CLI parsing and before `_check_subtitle_words()` so word counts and later alignment reduce on the same cleaned text.
- Preserve other meaningful punctuation: commas, periods, `?`, `!`, apostrophes.
- Do not rely on hardcoded per-word typo mappings; sanitize universally.

This avoids the known failure mode where `fans-off-guard` or merged tokens mismatch script words and push captions out of sync.

## Single-game rule

Each short must cover exactly one game or topic.

- Script text, title, trailer, hashtags, and captions must all match that same single game.
- Do not mention or compare other games/topics when the selected footage and topic are for only one title.

## Deliverable definition

A build is not deliverable merely because an MP4 file exists.
The only local build success criterion is production of the final delivery asset with visible burned-in subtitles and a valid duration/length.
The scheduler prompt wording must distinguish local build completion from playedback/platform delivery, because platform delivery can fail independently of build quality.
A file in `videos/TO_UPLOAD` is a built artifact; successful playback is a separate delivery phase.

## Cron upload schedule

- Preferred upload windows: 20:00

## Telegram delivery semantics (Windows gateway)

Built ≠ delivered.
"Delivered" means platform send actually completed, not that file creation succeeded.

## Deliverable verification sequence

Before reporting done or claiming "delivered":

1. Confirm the final MP4 exists in videos/TO_UPLOAD/ with the exact title-derived filename.
2. Confirm duration meets minimum length.
3. Confirm burned-in subtitles are actually visible by inspecting a frame at an active cue timestamp.
4. Attempt the platform send only after all local checks pass.
5. Report platform delivery status explicitly; distinguish build success from send success.

Treat an MP4 present in TO_UPLOAD as a local build artifact. Delivery is a separate phase and must be reported with the actual send status, not conflated with file existence.

When `send_message` with a `MEDIA:/absolute/path/to/video.mp4` attachment fails on Telegram:

- Do not retry the exact same call. The failures are consistent and add noise.
- The warning `Failed to send media <path>: Timed out` means the adapter reached the upload phase and then stalled before completion.
- The warning `Skipping unsafe MEDIA directive path` means the path was rejected before reaching the network upload.
- Treat these as transport issues, not file issues. The MP4 can still be valid and complete.
- Subtitle visibility and file existence remain the local success criteria. If the video file is present and frame probes show visible captions, the build is locally complete even if platform delivery is blocked.
- If the gateway timeout persists, capture the broken state for debugging instead of delivering via the same failing path again.
- When the filename contains `#`, retry once with the `#` stripped from the filename before declaring permanent delivery failure.
- **Document fallback (validated 2026-06-11):** When media send times out, sending the same file as a Telegram document (same `MEDIA:` path) succeeds. This is the preferred fallback for files >5 MB.
  - Both HAEX Short (6.5 MB) and Warzone EOS Short (15 MB) timed out on media send but succeeded as documents.
  - Document delivery preserves the file for user download; inline playback is sacrificed but deliverable reaches user.
- If Telegram media send times out from `MEDIA:` delivery, do not keep retrying as media. First try delivering the same file as a Telegram document, stripping hashtags from the filename for transport. If document delivery also times out, stop and report the transport failure without more identical attempts.
- Local success = final MP4 exists in `videos/TO_UPLOAD/`, duration meets minimum, and burned captions are visible at an active cue timestamp. Treat delivery timeout as a transport-layer failure, not a build failure.
