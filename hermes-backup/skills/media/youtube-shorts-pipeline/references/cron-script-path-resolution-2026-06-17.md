# Cron Script Path Resolution (2026-06-17)

**Critical Finding**: `no_agent` cron job scripts are resolved from `~/AppData/Local/hermes/scripts/`, NOT from the job's `workdir`.

## The Pitfall

```json
{
  "job_id": "477b924aca59",
  "script": "cron/cleanup_shorts.py",
  "workdir": "C:\\Users\\qthas\\Programming\\Belajar\\YouTube\\youtube-shorts-news-report-generator",
  "no_agent": true
}
```

This FAILS with: `Script not found: C:\Users\qthas\AppData\Local\hermes\scripts\cron\cleanup_shorts.py`

The `workdir` only affects the agent's working directory for `terminal`/`file` tool calls. The `script` field is ALWAYS resolved relative to `~/AppData/Local/hermes/scripts/`.

## Working Solution

1. Place the script directly in `~/AppData/Local/hermes/scripts/`:
   ```
   ~/AppData/Local/hermes/scripts/
   ├── cleanup_shorts.py
   ├── backup_memory.py
   └── scheduler_search.py
   ```

2. Reference by basename only:
   ```json
   "script": "cleanup_shorts.py"
   ```

## Project Structure (Updated)

We reorganized the MashButtonGaming Shorts repo to match skill conventions:

```
youtube-shorts-news-report-generator/
├── cron/                      # Cron-related scripts (PS1, etc.)
│   ├── _check_shorts_tasks.ps1
│   ├── _check_tasks.ps1
│   └── _watchdog.ps1
├── src/
│   ├── shorts_builder.py      # Main one-shot builder
│   └── scripts/               # ALL Python source code
│       ├── _reauth_youtube.py
│       ├── _tmp_ch.py
│       ├── build_final.py
│       ├── editorial_state.py
│       ├── fix_ass_timing.py
│       ├── log_metrics.py
│       ├── make_vtt.py
│       ├── make_vtt_phrases.py
│       ├── make_vtt_small.py
│       ├── render_now.py
│       ├── tiktok_upload.py
│       ├── tmp_auth_net_check.py
│       ├── vtt_to_ass.py
│       ├── youtube_analytics.py
│       ├── youtube_upload.py
│       └── ...
├── assets/fonts/whoosh/       # Subtitle fonts
└── videos/
    └── TO_UPLOAD/             # Final outputs only
```

## Verified: shorts_builder.py End-to-End on Windows Native

Full pipeline tested and working:
- ✅ Trailer download (yt-dlp with android/web client fallbacks)
- ✅ Voiceover generation (edge-tts fallback since piper not in PATH)
  - Voice: `en-US-BrianMultilingualNeural` at `+25%` rate
- ✅ Segmented edit (5s clips, random start offsets, shuffled, reordered)
- ✅ ASS captions with faster-whisper small word-level timing
  - `_word_end()` patched to accept `audio_duration` and extend last word
- ✅ Subtitle burn (720×1280, cover crop, Whoosh font)
  - Repo-relative POSIX paths + `cwd=REPO` pattern
- ✅ Final output: `videos/TO_UPLOAD/<TITLE>.mp4` (≥30s, verified)

Test command:
```bash
cd C:\Users\qthas\Programming\Belajar\YouTube\youtube-shorts-news-report-generator
python src/shorts_builder.py \
  --youtube "https://www.youtube.com/watch?v=3x_p_jw0j2U" \
  --title "TEST_BUILD" \
  --subtitle "THIS IS A COMPREHENSIVE END TO END TEST OF THE SHORTS BUILDER PIPELINE TO VERIFY THAT ALL COMPONENTS INCLUDING TRAILER DOWNLOAD VOICEOVER GENERATION SEGMENTED EDITING CAPTION CREATION AND FINAL RENDERING ARE WORKING CORRECTLY TOGETHER FROM START TO FINISH WITHOUT ANY ERRORS OR ISSUES THAT WOULD PREVENT SUCCESSFUL SHORT CREATION TODAY"
```
(50 words exactly — minimum for 50-150 word gate)

**Syntax Warning Fix**: `src/shorts_builder.py` docstring line 4 had invalid escape sequence `\S` in `.venv\Scripts\python.exe`. Fixed by doubling backslashes: `.venv\\Scripts\\python.exe`. Always escape backslashes in Python triple-quoted strings.

## Cleanup Script (`cleanup_shorts.py`)

Created as `no_agent` cron job script at `~/AppData/Local/hermes/scripts/cleanup_shorts.py`:

```python
#!/usr/bin/env python3
# Rules:
# - Delete `tmp` at project root if exists
# - Delete `videos/tmp` if exists
# - In `videos/`, keep `TO_UPLOAD`; delete all other child dirs/files
# - Do NOT touch `videos/TO_UPLOAD`, `src`, `assets`, repo root files
# - Report paths removed; silent exit (exit 0) if nothing removed
```

Cron job configuration:
```json
{
  "job_id": "477b924aca59",
  "name": "shorts-news-cleanup",
  "script": "cleanup_shorts.py",
  "no_agent": true,
  "schedule": "every 15m",
  "workdir": "C:\\Users\\qthas\\Programming\\Belajar\\YouTube\\youtube-shorts-news-report-generator"
}
```

Verified: removes builder temp folders (e.g., `2026-06-17-TEST_BUILD/`) while preserving `TO_UPLOAD/`.

## Scheduler Status

| Job | Status | Notes |
|-----|--------|-------|
| `shorts-news-scheduler` (80c55b5a2392) | ✅ OK | Model override removed; now uses default agent model (Nemotron 3 Ultra via Nous) |
| `shorts-news-watchdog` (bab0abf9f152) | ✅ OK | Agent-driven, detects scheduler error |
| `shorts-news-cleanup` (477b924aca59) | ✅ OK | `no_agent: true`, script-based, **every 1h** (was 15m) |
| `Memory Backup` (8c2f7219609a) | ✅ OK | `no_agent: true`, `backup_memory.py` |

## Windows Startup Cleanup for Hermes Notification Scripts

Background notification scripts (`hermes-agent-ding.py`, `hermes-complete-notify.py`) were found in `~/AppData/Local/hermes/scripts/` and registered in `HKCU:\Software\Microsoft\Windows\CurrentVersion\Run` as `HermesAgentDing` → `pythonw.exe hermes-agent-ding.py`. These are NOT Windows Task Scheduler tasks and won't appear in `Get-ScheduledTask`.

**Removal steps:**
```powershell
# Remove startup entry
Remove-ItemProperty -Path HKCU:\Software\Microsoft\Windows\CurrentVersion\Run -Name HermesAgentDing -ErrorAction SilentlyContinue

# Kill running process
Stop-Process -Id <PID> -Force  # or Get-Process pythonw | Where-Object {$_.CommandLine -like '*hermes-agent-ding*'}
```

Both scripts deleted from `~/AppData/Local/hermes/scripts/`. No more auto-ding on agent completion.

## Key Takeaway for Future Sessions

When converting a cron job to `no_agent: true`:
1. Write the script as a standalone `.py` file
2. Deploy to `~/AppData/Local/hermes/scripts/<script_name>.py`
3. Update cron job with `"script": "<script_name>.py"` (basename only)
4. Test with `cronjob(action="run", job_id="<id>")`
5. Verify output in `~/AppData/Local/hermes/cron/output/<job_id>/`

**Schedule Optimization**: Reduced cleanup job from `every 15m` to `every 1h` — builder temp folders don't accumulate that fast. Avoid polling overhead.

**Model Override Removal**: To fall back to default agent model, edit `~/AppData/Local/hermes/cron/jobs.json` and set `"model": null, "provider": null`. The `cronjob` tool `update` action rejects `null` values; manual JSON edit or `hermes cron edit <job-id>` required.

**Windows Startup Script Cleanup**: Check `HKCU:\Software\Microsoft\Windows\CurrentVersion\Run` for `pythonw.exe` entries related to Hermes. These are not in Task Scheduler. Remove with `Remove-ItemProperty` and kill the process.