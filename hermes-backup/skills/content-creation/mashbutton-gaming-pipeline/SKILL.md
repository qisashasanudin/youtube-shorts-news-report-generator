---
name: mashbutton-gaming-pipeline
description: End-to-end YouTube/TikTok Shorts pipeline for youtube-shorts-news-report-generator (formerly MashButtonGaming). Use this skill for trailer download, TTS voiceover, caption generation, subtitle burn, final MP4 deliverable creation, TikTok metadata packaging, approved manual uploads, and YouTube Analytics reauth.
tags: [youtube, tiktok, shorts, gaming, tts, stt, ffmpeg, mashbutton, analytics]
---

# MashButtonGaming Shorts News Report Generator Pipeline

Short-form news pipeline for one-game FPS/gaming stories across TikTok and YouTube Shorts. Handles trailer download, TTS narration, caption alignment, subtitle burn, final MP4, TikTok metadata packaging, and manual-first upload workflows.

## Authoritative Reference

Use the reference short at https://www.youtube.com/shorts/wlZbtb-7T9o as the style baseline.

Required behaviors:
- Title/text style: all-caps punchy headline with hashtags
- Orientation: portrait Short
- Subtitles: tiny short-on-screen captions, 1-2 words when possible
- Lens: quick news beats and clear callouts

## Unified Entrypoint (`src/shorts_builder.py`) — **ONLY BUILDER IN REPO**

**One-shot command pattern (Windows `.venv`, primary runtime):**
```bash
cd C:\Users\qthas\Programming\Belajar\YouTube\youtube-shorts-news-report-generator
.venv\Scripts\python.exe src\shorts_builder.py --youtube "URL" --title "Exact Title" --subtitle "Narration text 50-100 words"
```

This project uses the repo-root Windows `.venv` as the canonical runtime. Do not add a browser-only fallback.

**This is the ONLY builder script in the repository.** All prior experimental wrappers (`src/scripts/build_short.py`, `src/scripts/main.py`, `src/scripts/mashbutton_scheduler_search.py`, `src/scripts/search_web.py`, `src/scripts/search_engine.py`, `src/scripts/ensure_edge_cdp.py`) have been **permanently deleted** (commit d3f9969). The architecture is now strictly:

```
┌─────────────────────────────────────────────────────────────┐
│  HERMES CRON (job 80c55b5a2392) — runs 4×/day               │
│  → browser_navigate → Bing News (CDP on port 9222)          │
│  → extracts 10 fresh shooter/FPS stories                   │
│  → delivers formatted list to Discord                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (you pick one in Discord)
┌─────────────────────────────────────────────────────────────┐
│  python src/shorts_builder.py                               │
│    --youtube "https://youtu.be/..."                         │
│    --title "BOMBASTIC CLICKBAIT TITLE"                      │
│    --subtitle "50-100 word narration, plain words..."       │
│  → videos/TO_UPLOAD/{TITLE}.mp4 (720×1280, subs + audio)    │
└─────────────────────────────────────────────────────────────┘
```

**Zero local search code remains in the repo.** All web search is handled exclusively by Hermes gateway CDP via the cron job's browser toolset.

This single script handles the full chain:
1. Download trailer via yt-dlp (1080p+, Android client fallback for age-gated)
2. Generate TTS voiceover (edge-tts Brian +25% rate)
3. Build segmented edit (5s shuffled clips, stream-copy assembly)
4. Generate ASS captions (faster-whisper word-level alignment)
5. Burn subtitles + render final 720×1280 H.264/AAC
6. Verify + copy to `videos/TO_UPLOAD/`

### WordPress Count Guard (enforced)

`--subtitle` must be **50–100 words**. The builder exits immediately if outside this range. This prevents unusably short TTS output and improves TikTok view-to-swipe retention.

### Filename Sanitization (automatic)

Unsafe characters in `--title` are sanitized automatically before writing the final MP4. The sanitized filename is used as the final output stem plus `.mp4` in `videos/TO_UPLOAD/`.

Sanitization rules:
- Uppercase output: `text.strip().upper()`
- Allowed characters: `A-Z`, `0-9`, spaces, underscores, and `#`
- Spaces become `_`
- All other characters are stripped
- Result is truncated to 80 characters

This preserves hashtags in the filename. Slugs like `BATTLEFIELD_6_SEASON_3_BLASTPOINT_IS_COMING_IN_JUST_A_FEW_DAYS_#GAMING_#BATTLEFIELD6_#BATTLEFIELD_#BF6` are valid and expected.

### Render / Burn

Final render uses repo-relative paths:
```
ass=captions/captions.ass:fontsdir=assets/fonts/whoosh[v]
```
ffmpeg is launched with `cwd=REPO` so these paths resolve correctly on Windows.

### Rebuild and Title/Subtitle Correction Protocol

When changing title or subtitle content after a build has started or finished:
1. Kill the active build process first.
2. Update verified facts/subtitle text only.
3. Re-invoke the unified builder once with the corrected input.
4. Reuse the same source trailer unless the user requests a different source.

**Work Directory Caching Gotcha:** The builder creates work directories named `videos/<DATE>-<SLUGIFIED_TITLE>/`. If you rebuild with the **same title on the same day**, the existing work directory is reused — including any cached `trailer_full.mp4` from the previous run. This causes stale trailer footage to be used even when you pass a different `--youtube` URL.

Fix options:
- Delete the existing work directory before rebuilding: `rm -rf "videos/2026-06-09-MARATHON_SEASON_2_..."`
- Or change the title slightly (e.g., append `_GAMEPLAY` or `_V2`) to force a fresh work directory and fresh trailer download.
- The builder does NOT re-download the trailer if `trailer_full.mp4` already exists in the work dir.

**Specific corrections from this session:**
- If the title contains `and here's what you need to know`, remove it and ensure the subtitle places that phrase at the end of the first sentence before any facts.
- The subtitle's first sentence must end with `and here's what you need to know.` and facts must follow after; never place facts before this bridge phrase.
- Game facts (map names, dates, modes, unlocks) must come from official/authoritative sources only, not intuition or prior memory.
- Hashtag policy: include at least 5 lowercase hashtags in the title when requested. Hashtags should be alphanumeric or single hyphen; preserve case per user request.
- **Narration input format**: The `--subtitle` argument expects normal sentence-case paragraphs with conversational phrasing — NOT the rendered ASS output format (which is one-word-per-line ALL CAPS). The builder internally converts to ASS. Do not pass pre-formatted ASS text.
- **Minimum duration enforcement**: All final videos must be ≥ 30 seconds for YouTube Shorts compliance. If the generated audio + shuffled clips produce < 30s, add more trailer segments or adjust TTS rate before final render.
- **Hashtag handling in upload**: The `youtube_upload.py` script extracts hashtags from the `--title` stem and moves them to the video description. The YouTube title will be the clean text without hashtags. This is intentional — do not remove hashtags from the title stem to preserve the filename convention.

## Clip Reordering Optimization

When stitching trailer clips, do not extract or render more source footage than needed.
- Minimum clips = clips needed to reach or slightly exceed narration duration.
- After shuffling without reuse, stop selecting as soon as the combined selected clip duration reaches the narration duration.
- This avoids unnecessary chunk generation and keeps the concat encode from ballooning in size and time.

## Copy-Mode Assembly (Default)

Re-encoding trailer chunks and the final concat is not required. Use stream copy for all edit-stage assembly:
- Chunk extraction (`part_*.mp4`): `-c copy -an`
- Concat (`reordered.mp4`): `-f concat -safe 0 -c copy -an`
- Trim pass if needed: `-t <duration> -c copy`

This preserves source codec quality and removes the GPU/CPU re-encode bottleneck that causes timeouts on long builds. The final subtitle-burn stage still re-encodes once to 720×1280 H.264; that is the only required transcode.

## Blocked Build Recovery Pattern

When direct builder execution stalls on trailer download or final render for a long period and cannot complete:
1. Do not blind-retry the same command immediately.
2. Inspect the existing `videos/<timestamp>-<title>/` work tree for usable artifacts (`clips/trailer_full.mp4`, generated `clips/part_*.mp4`, and `audio/voiceover.mp3`).
3. If the reusable clip and audio assets are already present, rebuild only the remaining pipeline stages locally (ASS generation, shuffled selection/concat, final render with subtitle burn) instead of rerunning the entire channel chain.
4. When failing mid-run is caused by CPU-heavy full-source chunk extraction, use faster intermediate encoding settings for edit-stage clip generation before the final 720×1280 subtitle burn.
5. If an existing `videos/TO_UPLOAD/<sanitized title>.mp4` is already too long or incorrect, remove it first before recreating it from cleaner intermediate assets.

## Fact-First Research Rule

Before generating subtitle text about a game update:
1. Search EA/official blog/roadmap source for the exact update name and content additions.
2. Use only confirmed facts: map names, mode returns, unlock windows, date ranges, platform coverage.
3. Do not include fluff metrics or unsupported claims like "player counts climbing" unless verified from official numbers.
4. When a fact correction arrives during an active build, stop and rebuild; do not patch copy mid-encode.

**Fact Verification Lesson (2026-06-15):** The agent hallucinated a fake Battlefield map "Giants of Karelia" as a flop comparison. User caught this immediately. **Never fabricate game names, dates, or features.** If a comparison is needed, use verified real examples (e.g., Orbital, Hourglass, Fjell 652, Aerodrome, Manifest for BF2042/V maps). When uncertain, omit the comparison rather than invent one.

**Primary Source Verification Toolkit (2026-06-15):**
- **YouTube oEmbed API** — confirms video title/author/uploader/thumbnail/duration without API key:
  ```bash
  curl "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=VIDEO_ID&format=json"
  ```
- **yt-dlp metadata extraction** (used by builder) — full description, tags, upload date, duration, uploader:
  ```bash
  python -c "import yt_dlp; ydl=yt_dlp.YoutubeDL({'quiet':True}); info=ydl.extract_info('URL', download=False); print(info.get('title'), info.get('description')[:500])"
  ```
- **Bing HTML scrape** (when web_search fails) — see `references/web-search-tool-limitation-and-workaround.md`

### Fallback Subtitle Rule

If ASS burn succeeds but subtitles are not visible, the next debug step is to inspect the ASS file contents and the ffmpeg burn log for "Added subtitle file" / font loading lines. If libass complains, switch to `subtitles=captions.ass` with explicit `force_style` overrides before reverting to VTT.

### Subtitle Text Cleanup First (optional diagnostic)

Before attempting any merge logic, sanity-check the hand-written `--subtitle` text itself. Hyphenated compounds and punctuation-bound tokens like `1-3,` or `3's` are especially likely to split badly across STT/manual boundaries.

**Important:** This cleanup is an optional diagnostic step, not automatic rewriting. Do not silently mutate the caller's `--subtitle` text. If cleanup is needed, surface it explicitly. A simple cleanup pass on the subtitle text — removing stray spaces before punctuation, normalizing punctuation-bound tokens, or replacing tricky symbols with simpler equivalents — gives much better on-screen results than complex word-matching code. But the default behavior must be: pass `--subtitle` through unchanged.

## Codebase Rules

- All source code is under `src/` and `src/scripts/`
- Do not create per-video scripts under `videos/<slug>/scripts/`
- Do not create standalone topic-specific build scripts at repo root or anywhere outside `src/` (e.g. `build_hell_let_loose_vietnam.py`); use the unified one-shot entrypoint instead. If a scratch script is created as part of recovery, delete it before finishing the task.
- Merge any duplicate `scripts/` back into `src/scripts/`
- The main builder is `src/shorts_builder.py`
- Final output must be placed in `videos/TO_UPLOAD/<title>.mp4` matching the exact title
- Keep `src/scripts/` tracked; do not add it to `.gitignore`
- All temporary artifacts (subtitle drafts, context dumps, test files) belong under `tmp/` and must be gitignored
- Caption typing/style behavior must be fully dynamic via input text, not hardcoded in code or templates.

## Subtitle Proofreading / View Preference Rule

Prefer `manual` on-screen text over STT tokens when both sides are likely the same word:
1. Build `manual_words` from `--subtitle` and `stt_words` from Whisper.
2. Truncate the longer list so lengths match one-to-one before comparing.
3. For each aligned pair:
   - If `stt == manual`, keep `manual`.
   - If they differ slightly, use a normalized/similarity comparison: lowercase, keep only alphanumeric characters, then `SequenceMatcher(..., ratio() >= 0.8`. If that passes, keep `manual`.
   - Otherwise keep the remaining STT token so timing-bearing tokens still flow.
4. Apply this in a config-driven alignment path inside the builder; do not hardcode global typo tables or language-specific normalization rules inline.

### Script Style (Must Follow)

Narration structure:
1. Sensational ambiguous hook / clickbait hold
2. Opening sentence must END with: `...and here's what you need to know.` This phrase must appear at the very end of the FIRST sentence, before any facts are stated.
3. Main information (50-100 words total)
4. Closing engagement sentence must START with: `but what do you think?` and ALWAYS end with a question mark `?`

Use casual conversational phrasing. One game/topic per short. Closed captions with hashtags in the title.

These phrases are non-negotiable placement rules. The opening hook never trails off into facts before the bridge line; the bridge line terminates the opening sentence. The engagement closer is always the LAST sentence and always reads as a direct question.

### Narration Tone (Grounded, Not Hype)

**Correction from session 2026-06-09:** The user rejected "corny/hype" narration (e.g., "collapsed into chaos," "buckled under demand," "stranded in orbit") in favor of a grounded, factual style.

Preferred tone:
- Plain language: "launched with major server issues," "servers couldn't handle the player count," "progression tracking failed"
- Avoid: "disaster," "chaos," "collapsed," "stranded," "amplified the disaster"
- State facts directly; let the situations speak. The engagement question carries the emotional hook.
- Still use the required bridge phrase (`and here's what you need to know`) and closer (`but what do you think?`) — just don't inflate the middle.

**Correction from session 2026-06-11:** User provided explicit narration corrections in sequence:
1. "The narration is too short" — expanded from ~65 to ~95 words (target 50–100 word range fully)
2. "There is not 'and here is what you need to know'" — phrase must be present
3. "It should be at the very first sentence" — bridge phrase terminates the opening sentence, no facts before it
4. "The closing question is not good enough" — binary "good/bad" questions rejected; must target a specific debatable aspect (unique mechanic, dev pedigree vs. genre, design trade-off)
5. "Use this narration instead" — user may provide final exact text; accept it verbatim

**Engagement Question Quality (validated 2026-06-11):** See `references/engagement-question-guidelines.md`. Examples that passed:
- HAEX: "Is the world-reshaping mechanic exciting or just a gimmick?" — targets signature mechanic
- Warzone EOS: "Forced upgrade or justified evolution?" — targets player tension (forced migration vs. technical necessity)
- Rejected: "Survival genius or just Division 2.0?" — too binary, doesn't invite substantive debate

## Dynamic Subtitle Text Rule

The `--subtitle` argument is the only authoritative source for text content. The builder must not apply hardcoded engagement text, hooks, or repeat phrases. If no engagement question is present, do not append one. Any caller-required closing question must be written into `--subtitle` by the caller before invoking the builder.

## Preferred Subtitle Source Split

Use this exact split to avoid drift and mismatch:

- **TTS audio input**: use the hand-written `--subtitle` exactly as supplied.
- **On-screen captions**: use `faster-whisper` STT word tokens from the generated voiceover when available; otherwise fall back to evenly spaced manual tokens from the subtitle word count.

Never use fuzzy/manual word matching to infer STT text. If STT is available, the caption text must be the STT token text itself.

## Platform Workflow

TikTok is the primary distribution platform. YouTube Shorts is selective/scheduled for high-signal stories (story score 75 or higher) and new-channel conservative daily caps.

- Build once with `src/shorts_builder.py`.
- For TikTok: run `src/scripts/tiktok_upload.py --title <title> --subtitle <caption> --hashtags <comma-separated>` to produce `videos/tiktok_meta/<sanitized-title>.tiktok.json`.
- For YouTube: use `src/scripts/youtube_upload.py` for manual-first uploads only.
- Do not use the same upload cadence, hashtag rules, or title style on both platforms without explicit approval.

## File Delivery (Discord/Telegram)

**User directive:** Use `tmpfiles.org` as the primary delivery method for final MP4s to Discord and Telegram — native Discord/Telegram media upload can fail silently or time out on files >5 MB.

```bash
curl -F "file=@/path/to/video.mp4" https://tmpfiles.org/api/v1/upload
# Returns: {"status":"success","data":{"url":"https://tmpfiles.org/.../video.mp4"}}
```

Share the `tmpfiles.org` download link in the chat. Do not rely on native `MEDIA:` attachment delivery unless the file is small (<5 MB) and tmpfiles.org is unavailable. Surface the exact local file path as ultimate fallback if all delivery methods fail.

## TikTok Leaderboard Rules

- Same finished video asset can be reused on TikTok and YouTube Shorts.
- Preferred posting distribution: 4 TikTok posts/day when story supply allows, spaced to reduce audience overlap.
- Spacing rules:
  - Breaking/major news: every 1 hour.
  - Normal news day: every 3–4 hours.
  - Minimum gap: 1 hour between posts.
- TikTok proposal surface must include: score, target platform(s), optimized TikTok caption, and scheduling note.
- Only recommend YouTube when story score is 75 or higher.

**Scheduler Behavior (Multi-candidate workflow)**

These rules apply to the main scheduler and any substitute automation:
- Scheduler runs **4×/day** during 09:00–18:00.
- Each run proposes exactly 10 candidate gaming news stories from the last 7 days.
- Story quality scoring applies to every proposal: 0–100 using freshness, broad audience appeal, shareability, official trailer availability, and brand fit for MashButtonGaming.
- Minimum story score for proposals: 65.
- TikTok is the default platform for every valid proposal.
- YouTube is recommended only if score >= 75.
- Proposals must include: title, official trailer URL, brief rationale, story score, target platform(s), approximate story age, and publication/event date.
- Do not auto-build or auto-upload.
- Do not include "and here's what you need to know" in title text; placement belongs in the subtitle bridge line only.
- Proposals must be factual. Verified leaks/ratings-board signals may be included when clearly labeled as rumors, not confirmed announcements.
- Build/upload happens only after explicit user selection and guided step-by-step direction.

**Hard rule — automation is non-negotiable:** Do not propose removing, pausing, or reducing the scheduler. The user relies on this automation. If the scheduler is failing, fix the source or input path; do not suggest manual operation as the solution.

**Hard rule — search scope must stay broad:** Do not hardcode specific game titles in the scheduler query list. Use broad FPS/TPS discovery queries. User explicitly rejected narrowing the search scope.

### Scheduler Implementation (Zero-Cost Hermes Gateway CDP) — CURRENT LIVE CONFIG

**Critical:** The scheduler must NOT use Firecrawl, Nous web search, or any paid/gated search tool. The only approved search path is Hermes gateway browser tools (CDP).

**Architecture:** Agent mode cron job with `browser` toolset
- Job config: `no_agent: false`, `enabled_toolsets: ["browser", "file"]`
- Uses Hermes gateway's browser tools (CDP on port 9222) for Bing News search
- **Zero local search code in repo** — all web search happens through Hermes gateway
- Job ID: `80c55b5a2392` — runs 4×/day at 09:00, 12:00, 15:00, 18:00 (WIB)

**Agent Workflow:**
1. `browser_navigate` to Bing News search (2 queries: general + leaker)
2. `browser_snapshot(full=true)` to extract structured results (titles, snippets, sources, relative times)
3. `browser_click` on result links to get canonical article URLs
4. `read_file` editorial_state.json for URL deduplication
5. `write_file` scheduler_output.json with exactly 10 stories
6. Print Discord-formatted report to stdout

**Search URLs (broad, no hardcoded titles):**
- General: `https://www.bing.com/news/search?q=gaming+news+2026+shooter+FPS+this+week`
- Leaker: `https://www.bing.com/news/search?q=gaming+leak+2026+shooter+FPS+this+week`

**No local search scripts in repo** — all web search externalized to Hermes gateway.

**Required configuration:**
- Job mode: `no_agent=False` (agent mode)
- `enabled_toolsets: ["browser", "file"]`
- Deliver to Discord
- Prompt instructs agent to use browser tools for all search steps

**Why agent mode (not no_agent=True):**
- The Hermes gateway manages CDP connection internally
- Agent can execute multi-step browser workflows reliably
- No need to maintain local Edge instance or CDP URL config
- Gateway handles browser lifecycle

**Windows scheduler path resolution:** Uses project workdir (`C:\\Users\\qthas\\Programming\\Belajar\\YouTube\\youtube-shorts-news-report-generator`) so file operations resolve correctly.

**Discord delivery:** Cron output includes story count plus numbered title, URL, and source for each story.

**Key behavior (corrected 2026-06-17):** The scheduler script prints the Discord-formatted report to **stdout only** — it does NOT write to `scheduler_output.json`. The file write was removed after user correction. The cron job's `deliver: "discord"` captures stdout and sends it to Discord. Any downstream builder invocation reads no scheduler file; it consumes only the user-chosen YouTube URL, title, and narration passed at invocation time.

**Design rule:** Do not hardcode specific game titles. Use broad FPS/TPS discovery queries. User explicitly rejected narrowing the search scope.

**Path resolution:** `scheduler_output.json` written to project root. `--subtitle` builder reads no search state; it only consumes the user's chosen title + narration + YouTube URL.

**Scheduler Failure Recovery (Real-World Paths)**

These are the observed failure modes for the scheduler’s news-search step in this environment:
- **`web_search` fails with `Feature 'search.firecrawl' unavailable`** when the `firecrawl-py` install is blocked by an externally-managed Python environment (`pip install` errors, PEP 668). This stops all Firecrawl/Bing-style web search results.
- **`browser_navigate` fails with `Invalid CDP value: 'null'`** when `browser.cdp_url` is `'null'` or unconfigured. The built-in browser/gateway search path is unavailable until CDP is configured.
- **Direct Bing HTML scraping may return 0 results** even with HTTP 200 if the page is a `b_hide` / anti-bot response. Selectors like `li.b_algo` return nothing.
- **Free HTML search output may be category-style URLs or generic index pages**, not real articles. Use URL path filtering and query emphasis on patch notes, announcements, and launches.
- **User constraint (explicit):** Do not use Firecrawl or any paid Nous web tool in the scheduler. The scheduler must stay on free local HTML search only.

**Recovery sequence:**
1. Verify with `hermes status --all` whether web tools are usable.
2. If managed web search is unavailable, do not retry the same broken tool in a loop.
3. Switch to a direct verified HTML scrape using curl (`requests.get`) and save the raw HTML for inspection if needed.
4. If free HTML search yields zero parsable results, stop — do not fabricate candidate stories or blind-retry the scheduler.
5. Deliver the existing `scheduler_output.json` content only if it already contains verified recent stories; otherwise halt generation and surface the search blocker.
6. Never invent URLs, titles, or dates to fill a 10-candidate quota. Halting and surfacing the blocker is safer than hallucinating news.

**User rule (explicit, enforced):** Finish what was started. Do not abandon a broken job and send a synthetic/hallucinated fallback list. If real search/data is blocked, report the exact blocker.

**Scheduler-side verification policy:** The scheduler searches for candidates only. Do not open, preview, or verify individual result URLs inside the scheduler run. Verification happens in a later review step.

### Scheduler Output Format (STRICT)

Output format must match exactly:

```
Cronjob Response: shorts-news-scheduler
(job_id: 80c55b5a2392)
-------------

1. [Game Title] — [Hook/Event]  
Official source/trailer: [URL]  
Publication/event: [source, date]  
Approximate age: [e.g., ~2 days].  
Rationale: [Why this works for Shorts — one sentence].

2. [Game Title] — [Hook/Event]  
Official source: [URL]  
Publication/event: [source, date]  
Approximate age: [e.g., ~7 days].  
Rationale: [Why this works for Shorts — one sentence].

... (continue to 10)
```

Rules:
- Use "Official source/trailer:" when there's a direct trailer URL, "Official source:" for articles
- Age in days relative to today
- Rationale: one sentence, specific to short-form engagement (clips, reveals, urgency, community reaction)
- Mix of reveals, updates, controversies, DLCs, betas
- Prefer FPS/TPS/gaming content; shooter genres first, general gaming news second
- Prefer official first-party sources (studio blogs, YouTube channels, press releases)
- Deduplicate against last 7 days of used_stories in editorial_state.json
- Output EXACTLY 10 numbered items
- Header must be exactly: "Cronjob Response: shorts-news-scheduler\n(job_id: 80c55b5a2392)\n-------------"

## Deduplication Rule (same-day filter)

When filtering duplicates against `editorial_state.json`:
- Block repeats only if the story was already covered **today**.
- Stories covered yesterday or any earlier date are allowed again.
- This keeps same-day variety while allowing older stories to resurface in future runs.

## Scheduler Failure Recovery (Real-World Paths)

These are the observed failure modes for the scheduler’s news-search step in this environment:
- **`web_search` fails with `Feature 'search.firecrawl' unavailable`** when the `firecrawl-py` install is blocked by an externally-managed Python environment (`pip install` errors, PEP 668). This stops all Firecrawl/Bing-style web search results.
- **`browser_navigate` fails with `Invalid CDP value: 'null'`** when `browser.cdp_url` is `'null'` or unconfigured. The built-in browser/gateway search path is unavailable until CDP is configured.
- **Direct Bing HTML scraping may return 0 results** even with HTTP 200 if the page is a `b_hide` / anti-bot response. Selectors like `li.b_algo` return nothing.
- **User constraint (explicit):** Do not use Firecrawl or any paid Nous web tool in the scheduler. The scheduler must stay on free local HTML search only.

**Recovery sequence:**
1. Verify with `hermes status --all` whether web tools are usable.
2. If managed web search is unavailable, do not retry the same broken tool in a loop.
3. Switch to a direct verified HTML scrape using curl (`requests.get`) and save the raw HTML for inspection if needed.
4. If free HTML search yields zero parsable results, stop — do not fabricate candidate stories or blind-retry the scheduler.
5. Deliver the existing `scheduler_output.json` content only if it already contains verified recent stories; otherwise halt generation and surface the search blocker.
6. Never invent URLs, titles, or dates to fill a 10-candidate quota. Halting and surfacing the blocker is safer than hallucinating news.

**User rule (explicit, enforced):** Finish what was started. Do not abandon a broken job and send a synthetic/hallucinated fallback list. If real search/data is blocked, report the exact blocker.

**Scheduler-side verification policy:** The scheduler searches for candidates only. Do not open, preview, or verify individual result URLs inside the scheduler run. Verification happens in a later review step.

## Scheduler Command Sequence

Use this sequence when the scheduler state appears stuck or `last_run_at` does not advance after an attempted run:
1. List current cron jobs: `cronjob action='list'`
2. Update the job to the current cadence, candidate count, and prompt: `cronjob action='update' job_id='<id>' schedule='0 8-22/2 * * *' prompt='...'`
3. If runtime state cannot be recovered, bypass automation and invoke the builder CLI directly in the project directory instead of retrying scheduler runs.

## TikTok Metadata Packaging

This project already supports TikTok packaging via the `tiktok_upload.py` helper:
- Build once with `src/shorts_builder.py`.
- Run `src/scripts/tiktok_upload.py --title <title> --subtitle <caption> --hashtags <comma-separated>` to produce a metadata package in `videos/tiktok_meta/`.
- Keep TikTok upload manual-first until explicit auto-upload access is provided.
- The finished video asset itself is reused for both TikTok and YouTube; packaging differs by platform.

## Preferred TikTok Posting Spacing

Same-day batch rules from verified creator behavior:
- Breaking/major news: every 1 hour.
- Normal news day: every 2–3 hours.
- Minimum gap: 30 minutes between posts.
- Avoid posting back-to-back in a 5-minute burst; audience overlap is more likely to hurt performance than spam penalties on new accounts.

## YouTube Analytics Integration

### OAuth Scope Upgrade Procedure

`token.json` must include `youtube.readonly`, `yt-analytics.readonly`, and `yt-analytics-monetary.readonly`. If analytics calls return `insufficientPermissions` or `invalid_scope` on refresh, the existing token cannot be expanded incrementally — full re-auth is required with the complete scope set.

Use the helper at `_reauth_youtube.py` (create/deploy content from `references/youtube-analytics-oauth-upgrade.md` if missing). Run from desktop shell:

```bash
cd C:\Users\qthas\Programming\Belajar\YouTube\youtube-shorts-news-report-generator
python _reauth_youtube.py
```

It will print the new scopes after saving. Verify with:

```bash
python -c "import json; d=json.load(open('token.json')); print(d['scopes'])"
```

### Per-Video Metrics Logging (`src/scripts/log_metrics.py`)

Logs per-video English YouTube Data API v3 stats (`views`, `likes`, `dislikes`, `comments`, `favorites`) into `analytics_log.json`.

```bash
.venv\Scripts\python.exe src\scripts\log_metrics.py <VIDEO_ID>
```

Output is appended to `analytics_log.json` as `videos[<id>]`. Use this after each successful upload to seed performance telemetry for the scheduler.

### Shorts-Safe Analytics Metrics

The YouTube Analytics API rejects some metrics for Shorts channels (`impressions`, `clickThroughRate`). When calling `src/scripts/youtube_analytics.py`, use Shorts-compatible metrics:

`views,estimatedMinutesWatched,averageViewDuration,comments,likes,dislikes,shares,subscribersGained,subscribersLost`

## Preferred Toolkit Updates

`log_metrics.py` and `tiktok_upload.py` are now first-class helpers under `src/scripts/`. Treat them as core pipeline components, not scratch utilities.

## Trailer Segment Assembly (Preferred Behavior)

Split the downloaded trailer into fixed-length source clips and reorder them to avoid continuous playback:

- Slice the source into consecutive 3-second clips from `0` onward.
- Number of clips is derived from `floor(source_duration / 3.0)` (minimum 1).
- Generate exactly one concat input clip per slice; do not vary segment length.
- Shuffle clip order using a no-reuse-until-exhausted pattern:
  - Keep an `unused` index pool.
  - Select randomly from `unused` until empty; when empty, refill from the full set and continue.
- Stop when the selected clip count matches the planned clip count.
- build_segmented_edit() should pass the ffmpeg concat demuxer a `filelist.txt` with one `file '...'` entry per selected clip in shuffled order.
- The final assembled clip duration should match the planned narration duration; do not loop or trim to force exact equality unless explicitly required.

## External Subtitle Correction Rules

Do not hardcode typo merge rules inside the pipeline. STT token variance handling belongs in alignment behavior, not in a hardcoded exception list. If global correction rules are required, keep them outside the code as a data-driven config and apply them only in the alignment path; never add `source -> normalized` hardcoding inside `shorts_builder.py` itself.

Do not normalize spelling variants such as `favorite` vs `favourite`. The caption path should not silently rewrite on-screen text to a chosen dialect.

If a typo-correction config is present, it must be optional and non-authoritative. Missing or malformed config must not fail the build; the alignment path must continue without correction. The same section should not encode language-specific normalization as permanent rules.

## Subtitle Text Merge Rule

When incorporating STT tokens into the final on-screen caption list:
1. Build `manual_words` from `--subtitle` and `stt_words` from Whisper.
2. Make the lists one-to-one aligned before comparing:
   - If one side runs out, use the remaining tokens from the longer list.
3. For each aligned position:
   - If `stt == manual`, keep `manual`.
   - If `stt != manual`, prefer `stt` only when it is time-bearing; otherwise keep `manual`.
4. Content and on-screen text remain controlled by `--subtitle`; only timing comes from STT when available.

## Voice Behavior

Stability matters more than variety. Keep the configured Edge TTS voice/rate across rebuilds until the user explicitly changes it. Do not silently revert to older defaults.

### Subtitle Correct Edit Sync Rule

When subtitle text is updated after a build has already run:
- The saved caption or subtitle file is the new source of truth; any cached burned-subtitle artifact that was produced from prior text is now stale.
- The next render must regenerate captions/audio from the updated source text before delivery.
- Do not mark a final MP4 as current unless its `captions.ass`, `audio/voiceover.mp3`, and `clips/reordered.mp4` all come from the same render run as the final file.
- Before building after an edit, inspect the existing work dir and remove or rebuild stale intermediate assets instead of reusing them blindly.

## Subtitle Input Sanitization

Before word-count checks and caption generation, normalize punctuation in the supplied `--subtitle` text. This prevents word-count drift and tokenization mismatches in ASS generation. Sanitization is a data-prep step, not content rewriting.

Required replacements:
- Replace `-` with ` `
- Replace `—` with `, `
- Collapse consecutive whitespace to a single space

## Subtitle Positioning (ASS Alignment)

- Verified approach for controlling vertical placement of burned-in captions on 720×1280 YouTube Shorts output:
  - Use bottom-center placement: `Alignment=2` with `MarginV=25` in the style line.
  - `Alignment=2` = bottom-center anchor.
  - `MarginV=25` keeps captions close to the bottom edge without overlapping navigation.
  - Do not rely on per-dialogue overrides like `{\an5}` inside Dialogue lines; they can override style alignment unpredictably and break placement.
  - The style-derived alignment should be treated as authoritative unless the user asks for a placement change.
- From this session onward: when results are already looking good, skip routine frame-by-frame subtitle verification and do not generate or keep extra frame-check image artifacts in the repo; declare success from final asset existence and duration checks instead.
- Root-level subtitle scratch files (`*-subtitle.txt` in the repo root) must not be created during normal operation if `tmp/` is available. If they do appear, add matching patterns to `.gitignore` and treat them as untracked local scratch files only.

## Hardcoded Wording Prohibition

**Do not hardcode any engagement question, hook, or filler text inside the builder or pipeline.** The `--subtitle` string is the single source of truth for both narration and captions. Text generation, including any engagement closer, must come from the caller (LLM or script) at invocation time, not from inside `src/shorts_builder.py`, `generate_ass()`, or any render helper.

## Generative Content Policy

All caption and narration text must come from invocation-time parameters or the caller's LLM-generated content. The builder must not auto-append, infer, or synthesize engagement lines, hooks, or closers when the provided input text lacks them. Keep the interface parameter-driven so wording can evolve without code changes.

## Caption Source and Timing Rules

**Preferred source split:**
- TTS input: use hand-written `--subtitle` exactly as provided.
- On-screen captions: use `faster-whisper` STT word tokens from the generated voiceover.

This removes manual-to-STT drift and spelling mismatch risk. The builder must accept both paths and prefer STT text when available.

**Alignment fallback:**
- If STT is unavailable or fails, fall back to manual word timings evenly spaced from audio duration.
- Do not silently rewrite or normalize STT tokens; display them exactly as spoken.
- Do not merge spelling variants together in code; leave that to the caller if needed.

**No hardcoded text in builder:**
- The builder must not inject engagement questions, hooks, or filler text.
- All narration and caption content comes from `--subtitle`.

## Trailer Footage Rules

- When choosing a topic, first search for the most recent news or verified leaks/dataminer reports for the chosen game. Do not assume a game is currently relevant based on older reveal or early-access context.
- If the most recent verified news is a delay, shutdown, or similar status change, use that as the topic; do not republish an earlier announcement story as if it were current.
- **Trailer type verification is mandatory before building.** Confirm the source is an official gameplay trailer or cinematic, not a livestream, podcast, recap, or fan compilation. Use title/description cues plus quick frame/section verification before launching the builder.
- **Explicit trailer selection rule:** When multiple official trailers exist (e.g., "Cinematic Trailer" vs "Gameplay Trailer"), the caller must specify which one to use. Do not assume the first search result is correct. Verify the trailer URL matches the requested type (gameplay vs cinematic) by checking the YouTube title/description before invoking the builder.
- **Work directory caching gotcha:** The builder creates work directories named `videos/<DATE>-<SLUGIFIED_TITLE>/`. If you rebuild with the **same title on the same day**, the existing work directory is reused — including any cached `trailer_full.mp4` from the previous run. This causes stale trailer footage to be used even when you pass a different `--youtube` URL.
  - Fix: Delete the existing work directory before rebuilding: `rm -rf "videos/2026-06-09-MARATHON_SEASON_2_..."` 
  - Or change the title slightly (e.g., append `_GAMEPLAY` or `_V2`) to force a fresh work directory and fresh trailer download.
- **Hard source-size guard:** If the selected trailer source exceeds 500 MB, stop before download and reconsider format/title. Surface the size issue to the user before retrying. This prevents multi-minute waste on unsuitable footage.
- **Fact-check game-specific details before invoking the builder.** Verify map names, modes, and content additions from authoritative/official sources. Do not invent or reuse stale facts.
- Use the proven multi-attempt yt-dlp pattern with a strict quality-first fallback chain.
- **Canonical fallback order:**
  1. `bestvideo[ext=mp4][height>=1080]+bestaudio[ext=m4a]/best[ext=mp4][height>=1080]`
  2. Web player fallback
  3. Android player fallback
  4. `best`
  5. Last-resort thumbnails/static only with explicit user permission
- Do NOT create a broad `best[ext=mp4]` fallback between 1080p and the player-client fallbacks; that can pull 4K unexpectedly.
- If 1080p fails, silently fall back through web then android client selectors before ending with `best`.
- Reorder trailer segments into fixed 3-second shuffled clips with no-reuse-until-exhausted selection, recombining to match voiceover length.
- Verify trailer content visually before cutting.
- The title, script, narration, and footage must always refer to the exact same single game/topic with verified facts. If any fact changes, stop and rebuild with corrected copy.

**Age-gated YouTube Videos (2026-06-11):** Official CoD/Warzone trailers are frequently age-restricted, causing `yt-dlp` to fail with "Sign in to confirm your age."
- **Workaround 1:** Use `--extractor-args "youtube:player_client=android"` with format 18 (360p MP4) to bypass age gate. Acceptable for commentary/analysis fallback footage.
- **Workaround 2:** Use non-age-restricted commentary/breakdown videos (e.g., creator analysis of the announcement) as trailer source when official trailer is gated.
- **Workaround 3:** Search for same official trailer under different video IDs/regional uploads (see `references/trailer-agegate-workaround-2026-06-10.md`).
- **Rule:** When official trailer is age-gated, do NOT retry the same URL. Switch to verified alternative source immediately.

## Existing Output Check Before Rebuild

Before invoking the builder for a title/topic, scan `videos/TO_UPLOAD/` for any file whose sanitized stem matches the requested title. If a matching file already exists with size >= 1 MB and duration >= 30s, surface that file immediately instead of building a duplicate. Rebuilding identical content wastes time and risks trailer-download timeouts on large videos. Only rebuild when the existing file is stale, corrupted, or the user explicitly requests a refresh.

## Content Integrity Rule

Do not edit subtitle text during an active build. The `--subtitle` argument is the single source of truth; any engagement question, hook, or closing must come from the caller at invocation time. Modifying subtitle content mid-pipeline bypasses the scheduler contract and creates mismatches between narration and captions. If a subtitle correction is needed, abort the current build, update the source script or scheduler prompt, then re-invoke cleanly.

## Known Paths and Artifacts

- `videos/<project-id>/clips/trailer_full.mp4`
- `videos/<project-id>/clips/reordered.mp4`
- `videos/<project-id>/audio/voiceover.mp3`
- `videos/<project-id>/captions/captions.ass`
- `videos/TO_UPLOAD/<Exact Title>.mp4`
- `assets/fonts/whoosh/Whoosh.otf`
- `assets/fonts/whoosh/Whoosh.ttf`
- `src/scripts/` — merged home for all pipeline scripts
- `videos/tiktok_meta/<sanitized-title>.tiktok.json`

## Reference Files

- `references/architecture-simplification-2026-06-17.md` — Architecture simplification: single builder, Hermes CDP scheduler, 6 scripts deleted
- `references/workdir-caching-and-minimum-duration.md` — Work directory caching gotcha and YouTube Shorts 30s minimum duration enforcement
- `references/browser-search-integration-2026-06-15.md` — Zero-cost browser search replacing Firecrawl (built-in Bing scrape, $0.00 credits)
- `references/scheduler-free-search-implementation.md` — Free local HTML search scheduler implementation: no_agent mode, path resolution pitfall, parser format, and Discord delivery format
- `references/cron-job-schedule-updates-2026-06-15.md` — All monitoring/backup jobs aligned to 15-minute cadence
- `references/copy-mode-assembly-fix.md`
- `references/font-style-and-render-notes.md`
- `references/rails-audit-workflow.md`
- `references/stale-ass-sync.md`
- `references/subtitle-burn-verification-workflow.md`
- `references/subtitle-positioning.md`
- `references/subtitle-sanitization-and-alignment-fixes.md`
- `references/telegram-delivery-media-limitations.md` — Telegram media delivery limitations and workarounds for large MP4s
- `references/video-duration-extension-and-delivery-fallback.md` — `tpad` filter technique for 30s minimum compliance + confirmed Telegram document delivery fallback for >5MB MP4s
- `references/verified-trailers.md`
- `references/leak-research-methodology.md` — Finding & verifying deleted gaming content leaks within 7-day window
- `references/engagement-question-guidelines.md` — Closing engagement question best practices for Shorts narration
- `references/trailer-download-gotchas.md` — yt-dlp invocation, builder args, AV1 codec, Telegram document fallback
- `references/trailer-agegate-workaround-2026-06-10.md`
- `references/workdir-caching-and-minimum-duration.md`
- `references/development-crisis-story-pattern.md` — Research, structure, and language rules for games in development trouble (failed alphas, studio layoffs, reboot/cancel risk)
- `references/web-search-tool-limitation-and-workaround.md` — `web_search` tool hardcodes Nous gateway; curl+Bing HTML scrape workaround when credits exhausted
- `references/fact-verification-methodology.md` — YouTube oEmbed, yt-dlp metadata, Bing scrape for leak/source verification
- `references/ass-whisper-sync-bug-fix-2026-06-15.md` — numpy version mismatch causing silent Whisper failure; `_word_end` patch for audio-duration alignment

- `videos/`, `tmp/`, and runtime artifacts belong in `.gitignore`
- `assets/` must stay tracked; it is part of the render source files
- If `assets/` ever disappears from the remote, re-add the font files explicitly:
  - `assets/fonts/whoosh/Whoosh.otf`
  - `assets/fonts/whoosh/Whoosh.ttf`
- `src/scripts/` must remain tracked; never ignore helper scripts inside `src/`
- `tmp/` is the canonical scratch location; use it for subtitle drafts, context dumps, and one-off helpers instead of the repo root
- `.gitignore` should ignore TikTok metadata staging directories only if `videos/tiktok_meta/` becomes large; preserve tracked metadata structure by keeping manifest files checked in.

## Subtitle Burn Verification Note

Warns from 2026-06-06: ffmpeg can report subtitle burn success while the rendered frames contain no visible text. This was repeated across multiple trailers. If that happens, inspect `captions.ass` event counts and font loading lines in the burn log first. Do not claim subtitle visibility success from ffmpeg exit code alone; frame-level inspection is required for true validation.

## Proven Render References

These outputs reflect proof-of-working builds captured in earlier sessions:
- `videos/TO_UPLOAD/battlefield-6-season-3.mp4` — 68.000s, 21.2 MB, rendered with `en-US-BrianMultilingualNeural` at `+25%`, proofread merge applied
- `CROSSFIRE_REVEAL_LOOKS_JAWDROPPING_#CROSSFIRE_#GAMING_#SHOOTER_#FPS_#TPS_#SUMMER.mp4` — 40.324s, 13.7 MB, verified final MP4 delivery

## Output Verification Before Reporting

Required checks before claiming a video build complete:
1. Confirm final MP4 exists in `videos/TO_UPLOAD/` with size >= 1 MB and duration >= expected minimum.
2. Confirm the latest work dir matches the same render run, by comparing `captions.ass`, `audio/voiceover.mp3`, and `clips/reordered.mp4` timestamps to the final MP4.
3. If any of those are older than the final MP4, that win condition is stale and the latest pipeline state is invalid.
4. Inspect render frames or at least ASS event count/content; successful `ffmpeg subtitle burn -> 0` is not enough to claim subtitle visibility.
5. **Verify YouTube Shorts minimum duration: final MP4 must be >= 30 seconds.** Current builder output (~23.9s) is below platform requirement. If under 30s, add more trailer segments or adjust TTS rate before final render.
6. Final delivery claims must be backed by verified Telegram upload evidence, not just successful file creation. If upload fails, report the exact media status and path.
7. **Do not blind-retry failed delivery calls.** If Telegram sends a timeout, `No deliverable text or media remained`, or any platform-side delivery error, surface the exact file path and status once, then stop. The same applies to YouTube upload hangs. Do not rerun identical delivery commands hoping for a different outcome; instead, investigate network/auth/quota before the next attempt.
8. User expressions like "I don't see X", "wtf man", or "im so tired of this" are first-class signals to stop restating and verify with tools. The next action must be tool-based evidence, never text-only reassurance.

## Build Invocation Rule (No Per-Video Scripts)

All builds must go through the unified entrypoint: `src/shorts_builder.py --youtube "URL" --title "Exact Title" --subtitle "Full script text 50-100 words"`. Do not create per-video build scripts in `src/scripts/`, repo root, or anywhere else. If a scratch script is created for debugging, delete it before finishing. This keeps the flow global and dynamic for easier debugging and reruns.

## One-Shot Wrapper Rule (Parent/Orchestrator Calls)

When another script invokes the builder, pass `--subtitle` as the canonical input. Do not invent flags like `--voice-text`, `--trailer-url`, or `--out-dir` unless they exist in `src/shorts_builder.py`'s argparse. If an existing wrapper uses non-canonical flags, rewrite it to match the builder's actual interface or delete the wrapper.

## Approval + Send/Upload Flow

- Scheduler/cron automation must stop after the proposal step. Do not build/upload/send media unless the user explicitly approves.
- End-to-end task flow:
  1. Find one fresh news story/trailer
  2. Propose trailer URL + title + subtitle to user in Telegram
  3. Wait for explicit approval/feedback before building or delivering
  4. On approval, build with `src/shorts_builder.py`
  5. Deliver final MP4 to Telegram by default
  6. Generate TikTok metadata package with `src/scripts/tiktok_upload.py`
  7. Upload to TikTok when explicitly approved
  8. Upload to YouTube only for high-signal stories and when explicitly approved
- User default rule: “send only the MP4 to Telegram” unless instructed otherwise.
- TikTok upload remains manual-first only until explicit auto-upload settings or API access is provided.
- YouTube upload remains manual-only, triggered only by an explicit user command.
- External platform uploads (YouTube, TikTok) must always be manual-first with explicit user approval before I run any upload command.
- Do not perform any external uploads unless the user explicitly says so in the same conversation turn. General consent like “ok” after proposing a video does not grant upload permission.

## Proposal-Only Scheduler Behavior

- Main scheduler must not build/rename/upload/send on its own.
- One proposal per run: official trailer URL + title + subtitle + story score + target platform(s).
- Wait for user reply; do not take further action unless clear approval is received.

## Delivery Timeout / Media Attach Failure Rule

Observed platform-side behavior in Telegram delivery from this environment: `send_message` with `MEDIA:<absolute_windows_path>` repeatedly returns success from the Hermes gateway but the video does not appear in the user's chat for MP4 files larger than ~5 MB. Large MP4s often appear as **file attachments** (paperclip/download icon) rather than inline video, take 10-30 seconds to process, and may not auto-play in some Telegram clients.

**Discord native upload exhibits the same silent failure pattern** — API returns success but video doesn't appear. User has confirmed this and requested **tmpfiles.org as the permanent delivery method for both Telegram and Discord** to bypass platform media gateways entirely.

## Permanent Delivery Preference: Flexible Delivery (2026-06-15)

**User directive:** Use any delivery method that successfully sends the final MP4 to the user. Do not lock to a single method (tmpfiles.org, native media, document). Try methods in order of reliability for the current file/situation and use the first that works.

Suggested priority order (adapt per situation):
1. **tmpfiles.org mirror** — reliable for files up to ~100 MB, provides direct download link
2. **Telegram document send** — works for larger files that timeout on media send
3. **Native Telegram media** — fastest for small files (<5 MB)
4. **Discord native** — same file, cross-platform backup

**Agent Rule:** Default to tmpfiles.org link delivery as primary. If it fails or user reports non-receipt, immediately fall back to Telegram document send. Only use native media if file is small and previous methods have issues. Never claim "sent" without verifying the user actually receives the deliverable. Surface the exact local file path as ultimate fallback.

**Verification checklist for the user:**
1. Check for a paperclip/file icon in the chat (not inline player)
2. Open Telegram Web (web.telegram.org) — often shows media the mobile app hides
3. Restart the Telegram app or clear cache
4. Verify logged into the same account receiving the DMs

When this happens:
- Do not blind-retry identical media sends.
- Surface the exact verified local file path once, then stop.
- Do not claim "sent" or "delivered" if only the caption text arrived successfully; the deliverable is the video file, not the message text.
- **Verification checklist for the user:**
  1. Check for a paperclip/file icon in the chat (not inline player)
  2. Open Telegram Web (web.telegram.org) — often shows media the mobile app hides
  3. Restart the Telegram app or clear cache
  4. Verify logged into the same account receiving the DMs
- Alternative delivery paths to offer the user: provide the local absolute path for manual drag-and-drop transfer, initiate manual upload with explicit permission, or compress to 480p (~1-2 MB) as a fallback.

**Document fallback (validated 2026-06-11):** When media send times out, sending the same file as a Telegram document (same `MEDIA:` path) succeeds. This is the preferred fallback for files >5 MB.
- Both HAEX Short (6.5 MB) and Warzone EOS Short (15 MB) timed out on media send but succeeded as documents.
- Document delivery preserves the file for user download; inline playback is sacrificed but deliverable reaches user.

This rule applies whether the error reads "Timed out", "No deliverable text or media remained after processing MEDIA tags", or the API returns success but the user doesn't see the video.

## Process Hygiene

When the user wants to rerun the same title after a prior build is suspected stale:
1. Kill existing rebuild processes for that title before starting a fresh render.
2. Choose one fresh render run and do not start another while the current one is still finalizing output files.
3. After completion, do one consolidated verification pass and then report the result.

## Merged Scripts History

Original pipeline scripts under `scripts/` were merged into `src/scripts/` on 2026-06-06. Any duplicate `scripts/` folder elsewhere in the repo should be removed in favor of `src/scripts/`.

## Project Rename

Project renamed from `MashButtonGaming` to `youtube-shorts-news-report-generator` on 2026-06-06. All paths and references updated accordingly.

## Rule Ownership: Scheduler vs Code

Copy and structural constraints belong in the scheduler prompt, not in `src/shorts_builder.py`. The builder itself must stay neutral.
- The cron scheduler prompt enforces: subtitle word count limit, opening phrase placement, closing engagement phrasing, and question-mark requirement.
- `src/shorts_builder.py` must not validate content structure, hooks, closers, or engagement wording.
- If the user asks to hardcode a rule into code, assume they may later change their mind and prefer scheduler-only enforcement unless they explicitly revert this.

## Subtitle Text Rules (Non-Negotiable Contract)

These rules apply to both narration (`--subtitle`) and burned-in captions because the caption text is derived from the same source. Any scheduler or LLM invocation that generates subtitle text MUST follow this contract.

**Opening rule:**
- The very FIRST sentence is the bridge/hook.
- It MUST END with: `and here's what you need to know.`
- NO facts, game details, quotes, or news beats may appear before this phrase in the first sentence.
- Example: `Battlefield 6 Season 3 Blastpoint is almost here and here's what you need to know.`

**Closing rule:**
- The very LAST sentence is the engagement question.
- It MUST START with: `but what do you think?` as the complete sentence opener.
- It MUST ALWAYS end with a question mark `?`.
- It MUST be a direct open-ended question, not a statement trailer with a trailing `?`.
- Example: `but what do you think? Will you jump into Terminal War at launch?`

**Word count target:** 50–100 words total. ± is a valid range, not a rough guess.

These are placement rules enforced by the scheduler. If generated subtitle text does not match this structure, the scheduler must revise it before invoking the builder. Do not push malformed copy into the pipeline and expect the code to fix it.

## Narration Draft Review Workflow (MANDATORY)

**Critical correction from session 2026-06-13:** The user explicitly requires seeing the narration draft BEFORE any generation occurs. This is not optional.

Required sequence:
1. Research facts and write narration draft
2. **Present narration draft to user for review/approval**
3. Only on explicit "Approved" or similar confirmation, proceed to:
   - Generate TTS audio
   - Build subtitles (Whisper-aligned)
   - Render final video
4. If user requests edits, revise draft and re-present — do not generate until approved.

Violations observed: Agent generated TTS, built subtitles, and rendered video twice without showing draft first. User corrected with: "you dont even let me see the narration script" and "scrap the subtitle, start from scratch, then send the draft to me first before generating anything."

## Narration Draft Review Workflow (MANDATORY)

**Critical correction from session 2026-06-15:** The user explicitly requires seeing the narration draft BEFORE any generation occurs. This is not optional.

Required sequence:
1. Research facts and write narration draft
2. **Present narration draft to user for review/approval**
3. Only on explicit "Approved" or similar confirmation, proceed to:
   - Generate TTS audio
   - Build subtitles (Whisper-aligned)
   - Render final video
4. If user requests edits, revise draft and re-present — do not generate until approved.

Violations observed: Agent generated TTS, built subtitles, and rendered video twice without showing draft first. User corrected with: "you dont even let me see the narration script" and "scrap the subtitle, start from scratch, then send the draft to me first before generating anything."

## "Direct Language" Clarification

**Correction from session 2026-06-15:** When user asks for "more direct" language, they mean **simpler, more understandable wording** — NOT shorter/more concise.

- "Direct" = plain words, full sentences, spelled-out terms (e.g., "headquarters" not "HQ", "developers" not "devs", "two hundred million" not "$200M")
- "Direct" ≠ "condensed" — word count may stay same or increase
- Goal: factual clarity for general audience, not brevity
- Example correction: "ignored HQ and went rogue" → "ignored headquarters and did their own thing"

## Minimum Duration & TTS Rate Considerations

**Current pipeline behavior:** 79 words at edge-tts `--rate +25%` produces ~23s audio — **below YouTube Shorts 30s minimum**.

Options to hit ≥30s:
- **Increase narration to 95–100 words** (preferred — keeps fast pacing)
- **Slow TTS rate**: edit `shorts_builder.py` edge-tts `--rate +25%` → `+0%` or `-10%`
- **Add trailer segments**: builder prioritizes clips 3, 4, 5 but may need more chunks

**Agent Rule:** Before final render, verify `probe_duration(final_mp4) >= 30`. If under, extend narration or adjust TTS rate and rebuild.

## Fact Verification Methodology (2026-06-15)

Before writing narration for leaked gaming content:
1. **YouTube oEmbed API** — confirms video title/author/uploader/thumbnail/duration without API key:
   ```bash
   curl "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=VIDEO_ID&format=json"
   ```
2. **yt-dlp metadata extraction** (used by builder) — full description, tags, upload date, duration, uploader:
   ```bash
   python -c "import yt_dlp; ydl=yt_dlp.YoutubeDL({'quiet':True}); info=ydl.extract_info('URL', download=False); print(info.get('title'), info.get('description')[:500])"
   ```
3. **Bing HTML scrape** (when web_search fails) — see `references/web-search-tool-limitation-and-workaround.md`

### Web Search Tool Limitation (2026-06-15)

## Discord-Telegram Delivery Note

> **See: [File Delivery (Discord/Telegram)](#file-delivery-discordtelegram) above.** Hermes cron delivers story proposals to **Discord**. Final MP4s shared via tmpfiles.org link (works for both Discord and Telegram). Surface local path as ultimate fallback.

## Zero-Cost Operation Constraint (2026-06-15)

**User mandate:** Zero spending on Nous credits/Firecrawl/FAL/OpenAI TTS/STT.

- **Inference:** Nemotron 3 Ultra (free via Nous Portal) — $0.00 token cost, confirmed by 835M+ tokens at $0.00 spend
- **Build pipeline (`shorts_builder.py`):** Fully local — yt-dlp, ffmpeg, Piper TTS, edge-tts, faster-whisper, Whoosh font
- **Scheduler (`shorts-news-scheduler`):** ONLY component using managed tools (Firecrawl via `web` toolset)
- **Solution:** Replace Firecrawl with Edge CDP browser search (see `references/edge-cdp-web-search.md`) → **$0.00/month**
- **Scheduler frequency:** MUST stay at 4×/day (10:00, 13:00, 16:00, 19:00 WIB) — DO NOT reduce

This constraint overrides any credit-optimization suggestions that reduce scheduler cadence.

## Cron Environment Constraints

**Current pipeline behavior:** 79-82 words at edge-tts `--rate +25%` produces ~23s audio — **below YouTube Shorts 30s minimum**.

Options to hit ≥30s:
- **Increase narration to 95–100 words** (preferred — keeps fast pacing)
- **Slow TTS rate**: edit `shorts_builder.py` edge-tts `--rate +25%` → `+0%` or `-10%`
- **Add trailer segments**: builder prioritizes clips 3, 4, 5 but may need more chunks

**Agent Rule:** Before final render, verify `probe_duration(final_mp4) >= 30`. If under, extend narration or adjust TTS rate and rebuild.

## Narration Punctuation Requirement

**TTS engines require punctuation for natural pauses and prosody.** The `--subtitle` text MUST include proper punctuation (commas, periods, question marks) — not all-caps run-on sentences.

Builder behavior: `_sanitize_subtitle()` replaces `-` with space and `—` with `, ` but does NOT strip terminal punctuation. Ensure draft narration includes:
- Commas for clause separation
- Periods for sentence boundaries 
- Question mark on final engagement question
- Apostrophes for contractions (here's, it's, BF2042's)

All-caps ASS output is generated internally from the punctuated source.

## Clip Selection: Removed Hardcoded Priority Clips (2026-06-15)

**Previous behavior:** `priority_indices = [3, 4, 5]` forced clips 3, 4, 5 (seconds 15–30 of source) into every build regardless of content relevance. User confirmed this was a one-off for a specific video, not a permanent feature.

**Fix applied:** Removed priority logic entirely. All clips now fully shuffled:
```python
# Before (hardcoded priority)
priority_indices = [3, 4, 5]
priority_parts = [raw_parts[i] for i in priority_indices if i < len(raw_parts)]
other_parts = [p for i, p in enumerate(raw_parts) if i not in priority_indices]
random.shuffle(other_parts)
selected = priority_parts + other_parts[:remaining]

# After (fully shuffled)
other_parts = raw_parts.copy()
random.shuffle(other_parts)
selected = other_parts[:needed]
```

**Agent Rule:** No more hardcoded clip priorities. Every Short gets a fresh random selection from the full trailer.

## Download Size Limit: 100MB (was 500MB)

**Change:** Fallback yt-dlp format selector updated from `filesize<500M` to `filesize<100M`:
```python
{"format": "299+140/best[filesize<100M]/best"}
```

**Rationale:** Prevents multi-minute download stalls on oversized 4K/8K sources. The 100MB cap aligns with tmpfiles.org delivery limit and typical FHD trailer sizes.

## Narration Draft Review Workflow (MANDATORY)

**Critical correction from session 2026-06-15:** The user explicitly requires seeing the narration draft BEFORE any generation occurs. This is not optional.

Required sequence:
1. Research facts and write narration draft
2. **Present narration draft to user for review/approval**
3. Only on explicit "Approved" or similar confirmation, proceed to:
   - Generate TTS audio
   - Build subtitles (Whisper-aligned)
   - Render final video
4. If user requests edits, revise draft and re-present — do not generate until approved.

Violations observed: Agent generated TTS, built subtitles, and rendered video twice without showing draft first. User corrected with: "you dont even let me see the narration script" and "scrap the subtitle, start from scratch, then send the draft to me first before generating anything."

## Fact Verification Methodology (2026-06-15)

Before writing narration for leaked gaming content:
1. **YouTube oEmbed API** — confirms video title/author/uploader/thumbnail/duration without API key:
   ```bash
   curl "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=VIDEO_ID&format=json"
   ```
2. **yt-dlp metadata extraction** (used by builder) — full description, tags, upload date, duration, uploader:
   ```bash
   python -c "import yt_dlp; ydl=yt_dlp.YoutubeDL({'quiet':True}); info=ydl.extract_info('URL', download=False); print(info.get('title'), info.get('description')[:500])"
   ```
3. **Bing HTML scrape** (when web_search fails) — see `references/web-search-tool-limitation-and-workaround.md`

### Web Search Tool Limitation (2026-06-15)

The `web_search` / `web_extract` tools route through Nous Portal Firecrawl gateway. When Nous subscription credits are exhausted (billing error, $0 balance), **both tools fail with Payment Required** despite `web.backend: duckduckgo` and `web.use_gateway: false` in config — the tool implementation hardcodes the Nous gateway call.

**Workaround 1 — curl + Bing HTML scrape:**
```bash
curl -s --max-time 15 "https://www.bing.com/search?q=QUERY" | grep -o '"b_lineclamp[^"]*">[^<]*' | sed 's/.*>//'
```

**Workaround 2 — Edge CDP Browser Search (Zero-Cost, Preferred):**
See `references/edge-cdp-web-search.md` for full implementation. Start Edge with `--remote-debugging-port=9222`, connect via `/browser connect`, then use `browser_navigate` + `browser_console` to scrape DuckDuckGo/Bing/Google HTML. Consumes **$0.00 credits**.

**Agent Rule:** When web search fails with billing error, immediately switch to Edge CDP search (primary) or curl+Bing scrape (backup). Do not retry Nous tools.

## ASS / Whisper Sync Bug Fix (2026-06-15)

**Root cause:** numpy version mismatch (Python 3.11 Hermes venv had numpy 2.4.6 built for Python 3.13) → `faster_whisper` import fails silently → `mapped = []` → fallback constant per-word timing (~0.28s/word) → ASS drifts from audio.

**Fix:** Downgraded numpy to 2.4.0 in Hermes venv (compatible with Python 3.11). Whisper now runs on TTS audio.

**Code fix in `src/shorts_builder.py`:** Extended `_word_end()` to accept `audio_duration` and extend the last word to match audio end:
```python
def _word_end(mapped: list[dict], idx: int, audio_duration: float = None) -> tuple[float, float]:
    # ... existing logic ...
    if audio_duration is not None and e < audio_duration:
        e = audio_duration
    return s, max(e, s + 0.05)
```
Updated call site: `timings = [_word_end(mapped, i, audio_duration) for i in range(len(mapped))]`

**Verified working:** Variable timings (THE=0.06s, FIRST=0.18s, TIME=0.28s, BATTLEFIELD=0.36s, 4.=0.44s), last word extends to 23.30s (matches audio), `timing=whisper` logged.

## Discord-Telegram Delivery Note

> **See: [File Delivery (Discord/Telegram)](#file-delivery-discordtelegram) above.** Hermes cron delivers story proposals to **Discord**. Final MP4s shared via tmpfiles.org link (works for both Discord and Telegram). Surface local path as ultimate fallback.

## Zero-Cost Operation Constraint (2026-06-15)

**User mandate:** Zero spending on Nous credits/Firecrawl/FAL/OpenAI TTS/STT.

- **Inference:** Nemotron 3 Ultra (free via Nous Portal) — $0.00 token cost, confirmed by 835M+ tokens at $0.00 spend
- **Build pipeline (`shorts_builder.py`):** Fully local — yt-dlp, ffmpeg, Piper TTS, edge-tts, faster-whisper, Whoosh font
- **Scheduler (`shorts-news-scheduler`):** ONLY component using managed tools (Firecrawl via `web` toolset)
- **Solution:** Replace Firecrawl with Edge CDP browser search (see `references/edge-cdp-web-search.md`) → **$0.00/month**
- **Scheduler frequency:** MUST stay at 4×/day (10:00, 13:00, 16:00, 19:00 WIB) — DO NOT reduce

This constraint overrides any credit-optimization suggestions that reduce scheduler cadence.

## Cron Environment Constraints
   ```
3. Apply the standard output verification sequence on the produced MP4 before reporting.
4. Treat the direct build as a valid recovery path; do not postpone video generation until scheduler state is repaired.

## Cron Environment Constraints

- `execute_code` is blocked for cron environments. Use terminal commands directly.
- `.env` files containing secrets are blocked by tool security policy for direct read/write. Use environment variables or alternative configuration paths when possible.
