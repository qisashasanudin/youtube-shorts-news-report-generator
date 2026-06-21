---
name: scheduled-task-management
description: "Manage durable cron/scheduled jobs via the cronjob tool — create, update, list, pause, resume, and remove jobs with multi-platform delivery."
version: 1.0.0
author: agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cron, scheduler, scheduled-tasks, automation, delivery]
    related_skills: [hermes-agent, kanban-orchestrator]
---

# Scheduled Task Management

This skill covers managing durable scheduled jobs in Hermes using the **`cronjob` tool** (not the CLI `hermes cron` commands). The tool is the programmatic interface used inside agent sessions and supports chaining, multi-platform delivery, per-job model overrides, and pre-run scripts.

## When to Use This Skill

- You need to create, modify, or inspect scheduled jobs from inside an agent session
- You want to chain jobs (job B runs after job A via `context_from`)
- You need multi-platform delivery (Telegram, Discord, etc.) from a single job
- You want per-job model/provider overrides or custom toolsets
- You need pre-run data collection via `script` (with `no_agent=True` for watchdog patterns)

## Core Operations

### List All Jobs

```python
cronjob(action="list")
```

Returns: array of job objects with `job_id`, `name`, `schedule`, `deliver`, `next_run_at`, `last_run_at`, `last_status`, `enabled`, `state`, `workdir`, `skills`, `enabled_toolsets`, `model`, `provider`.

### Create a Job

```python
cronjob(
    action="create",
    schedule="0 10,13,16,19 * * *",  # cron expression or "every 2h", "30m", ISO timestamp
    prompt="Self-contained prompt for the agent to run each tick",
    name="optional-friendly-name",
    deliver="telegram,discord",  # or "local" (no delivery), "origin" (same chat), "all"
    skills=["skill-name"],       # optional ordered list of skills to load
    model={"provider": "nous", "model": "stepfun/step-3.7-flash:free"},  # optional override
    toolsets=["web", "terminal", "file"],  # optional toolset restriction
    workdir="/absolute/path/to/project",   # optional: runs with that dir's AGENTS.md/CLAUDE.md
    script="optional-script-path",         # optional: pre-run data collection
    no_agent=False,                        # True = script IS the job (watchdog pattern)
    context_from=["other-job-id"],         # optional: inject upstream job's output
    repeat=0,                              # optional repeat count (0 = forever)
)
```

### Update a Job

```python
cronjob(
    action="update",
    job_id="<job-id>",
    schedule="0 10,13,16,19 * * *",   # any field can be updated
    deliver="telegram,discord",
    prompt="...",
    skills=[],
    model={"provider": "...", "model": "..."},
    toolsets=[],
    workdir="",
    script="",
    context_from=[],
    # Pass empty array to clear: skills=[], context_from=[]
)
```

### Pause / Resume / Remove / Run Once

```python
cronjob(action="pause", job_id="<job-id>")
cronjob(action="resume", job_id="<job-id>")
cronjob(action="remove", job_id="<job-id>")
cronjob(action="run", job_id="<job-id>")  # trigger on next tick
```

## Schedule Formats

| Format | Example | Meaning |
|--------|---------|---------|
| Duration | `"30m"`, `"2h"`, `"1d"` | Every N minutes/hours/days |
| Every phrase | `"every monday 9am"`, `"every 2h"` | Natural language |
| 5-field cron | `"0 10,13,16,19 * * *"` | Standard cron (min hour dom month dow) |
| ISO timestamp | `"2026-06-15T16:00:00+07:00"` | One-shot at exact time |

**Timezone:** Cron expressions run in the scheduler's local timezone (WIB/UTC+7 for this user). Use `cronjob(action="list")` to verify `next_run_at` matches expectation.

## Delivery Targets

| Value | Behavior |
|-------|----------|
| `"telegram"` | Home Telegram channel |
| `"discord"` | Home Discord channel |
| `"telegram,discord"` | Both home channels |
| `"origin"` | Same chat that created the job (default) |
| `"local"` | No delivery — output saved only |
| `"all"` | Fan out to every connected home channel |
| `"telegram:-100xxx:thread"` | Specific chat + thread |

## Common Patterns

### Work-Hour Schedule (This User)

```python
# 4x/day during work hours: 10:00, 13:00, 16:00, 19:00 WIB
schedule="0 10,13,16,19 * * *"
deliver="telegram,discord"
```

### Cleanup Job (no_agent=True) — Project-Local Script, Hourly Schedule

```python
cronjob(
    action="create",
    name="project-cleanup",
    schedule="1h",  # Hourly is usually enough; 15m is excessive for cleanup
    script="cron/cleanup_shorts.py",  # project-local cron/ folder (see template)
    no_agent=True,
    deliver="local",
    workdir="/absolute/path/to/project",
    enabled_toolsets=["terminal", "file"],
)
```

**Schedule frequency best practice:** Cleanup/housekeeping jobs rarely need to run every 15m. `1h` or `every 6h` is sufficient and reduces scheduler overhead. The script is deterministic and idempotent — running it more often doesn't change outcomes.

### Watchdog Job (no_agent=True)

```python
cronjob(
    action="create",
    name="pipeline-watchdog",
    schedule="every 30m",
    script="scripts/check_pipeline_health.py",  # runs in workdir
    no_agent=True,
    deliver="local",  # silent unless error/exit or stdout non-empty
    workdir="/path/to/project",
)
```

- Script stdout delivered verbatim (non-empty = message, empty = silent)
- Non-zero exit → error alert
- Use for health checks, threshold alerts, API pollers with fixed output

### Converting Agent-Driven Jobs to Script-Driven (no_agent=True)

When an existing agent-driven job has deterministic, rule-based logic, convert it to `no_agent=True` to save tokens and latency. See `references/agent-to-script-conversion.md` for the complete recipe.

**Quick pattern:**
```python
cronjob(
    action="update",
    job_id="<job-id>",
    no_agent=True,
    script="cleanup_shorts.py",  # in ~/AppData/Local/hermes/scripts/
    prompt="",        # empty
    skills=[],        # cleared
    model=None,       # cleared
    provider=None,    # cleared
    # keep: schedule, deliver, workdir
)
```

**Removing Model Overrides to Fall Back to Default Agent Model**

If a cron job has an explicit `model`/`provider` that fails (e.g., upstream 503), remove the override so the job inherits the current default agent model. The `cronjob` tool with `action='update'` rejects setting model/provider to `null` with "No updates provided". Use the CLI instead:

```bash
hermes cron edit <job-id>
# In the editor, delete the explicit model/provider lines
```

Or manually edit `~/AppData/Local/hermes/cron/jobs.json` and set:
```json
"model": null,
"provider": null
```

Then the next run will use whatever model is currently configured as the agent's default (e.g., `nvidia/nemotron-3-ultra:free` via Nous).

**Good candidates:** file cleanup, log rotation, disk usage checks, backup verification  
**Bad candidates:** story selection, content generation, any "analyze/judge/pick" logic

### Chained Jobs

```python
# Job A collects data
cronjob(action="create", job_id="collector", schedule="0 9 * * *", prompt="Fetch latest news...", deliver="local")

# Job B processes Job A's output
cronjob(action="create", job_id="processor", schedule="0 9 * * *", prompt="Summarize the collected news...", context_from=["collector"], deliver="telegram")
```

## Pitfalls & Gotchas

1. **Timezone confusion** — Cron runs in scheduler's local TZ. Verify with `next_run_at` in list output.
2. **Delivery target "origin" vs explicit** — "origin" means the chat that created the job. In gateway sessions, this is the DM/channel where `/cron create` was run. Explicit `"telegram,discord"` is more reliable for cross-platform.
3. **Skills don't auto-reload** — If you update a skill, existing cron jobs won't see changes until next tick (they load skills at start of each run).
4. **`no_agent=True` requires `script`** — The script IS the job. No LLM call happens. Stdout = message, empty = silent, error = alert.
5. **3-minute hard timeout** — Each cron run is killed after 3 minutes. Long tasks need background delegation or external workers.
6. **`.tick.lock` prevents duplicate ticks** — Only one scheduler process runs a given job at a time.
7. **Cron sessions skip memory by default** — Set `skip_memory=False` in job config if you need cross-session memory (rare).
8. **Toolset restriction reduces tokens** — Use `enabled_toolsets: ["web", "terminal"]` for simpler jobs to cut prompt size.
9. **Windows `shutil.rmtree` permission errors** — On Windows, read-only or locked files/folders can cause `PermissionError` during deletion. Use `shutil.rmtree(path, onerror=...)` with a handler that retries after `chmod(0o666)` where supported. Do not let delete failures abort an entire backup run; log a warning and continue.
10. **Windows nested-dir path accidents** — Passing an empty `root_name` when `dest_dir` already ends with that name creates unintended nested directories like `.../skills/skills`. Name the stable target explicitly and mirror the source there.
11. **Avoid `.with_suffix(x)` on directory paths** — On Windows, `Path("skills").with_suffix(".bak")` can produce paths like `skills.bak`, which breaks rename/replace flows that assume a sibling directory.
12. **Prefer safest replacement order** — When refreshing a directory backup safely on Windows: copy source to a temp directory inside destination, remove the target, then rename temp into place. If rename fails, attempt to keep the original source as a fallback and abort with a warning, don't leave the destination empty.
13. **CDP port conflict with user's browser** — If a scheduled job launches a Chromium-family browser (Edge/Chrome) with `--remote-debugging-port` for CDP automation, it will conflict with the user's personal browser if they use the same port (default 9222). **Fix:** Use a dedicated port (e.g., 9223) AND a dedicated `--user-data-dir` (e.g., `~/.hermes/edge-scheduler-profile/`) so the scheduler's browser is completely isolated. Never `taskkill /f /im msedge.exe` — that kills the user's session too. See `references/browser-cdp-isolation.md` for the complete fixed pattern.
14. **Orphaned CDP processes after job completion** — A cron job that leaves its headless browser running (DETACHED_PROCESS) will accumulate zombie processes and hold the CDP port. Add a cleanup step (graceful shutdown via CDP `Browser.close` or `taskkill /PID <cdp-pid>`) at the end of the script, or launch with a wrapper that ensures the browser exits when the script exits.

15. **Windows startup scripts for Hermes notifications** — Background notification scripts like `hermes-agent-ding.py` (polls `state.db` for new assistant messages and plays `SystemAsterisk` sound) may be added to `HKCU:\Software\Microsoft\Windows\CurrentVersion\Run` as `pythonw.exe` entries. These are NOT Windows Task Scheduler tasks and won't appear in `Get-ScheduledTask`. To remove: `Remove-ItemProperty -Path HKCU:\Software\Microsoft\Windows\CurrentVersion\Run -Name HermesAgentDing -ErrorAction SilentlyContinue`, then kill the running `pythonw.exe` process. The companion script `hermes-complete-notify.py` (one-shot, triggers on `HERMES_COMPLETE_NOTIFY=1`) can be deleted from `~/AppData/Local/hermes/scripts/` if not needed.

16. **Hercules Gateway CDP (browser toolset) vs local Edge** — Hermes cron jobs can use the `browser` toolset which connects to the Hermes gateway's CDP endpoint (configured in `~/.hermes/config.yaml` as `browser.cdp_url`). This avoids launching a local browser entirely. The cron job agent gets `browser_navigate`, `browser_snapshot`, `browser_click` tools that operate on the gateway's CDP session. **Pattern:** `browser_navigate` → `browser_snapshot(full=true)` → extract links → `browser_click` to follow → write file. No local browser, no port conflicts, no orphaned processes. See `references/hermes-gateway-cdp-pattern.md`.

17. **Watchdog vs self-contained catch-up design pattern** — A separate watchdog job that checks "did the main job run?" adds complexity (two jobs to maintain, potential race conditions, duplicate runs). **Better pattern:** embed catch-up logic directly in the main scheduled job. On each run, the job checks its persistent state (`last_successful_run` timestamp), computes missed scheduled slots since then, and re-runs for each missed slot before doing the current run. This keeps scheduling authority in one place.
    - **Even better when environment is reliable:** If the machine reliably runs during all scheduled hours (e.g., laptop on 9-5 weekdays matching cron schedule), skip catch-up entirely. The user's explicit preference: "self-healing on laptop wake mechanism is not really necessary as i always turn on my laptop on 9-5 weekdays to work. make everything simpler." Over-engineering catch-up for reliable environments wastes tokens and adds failure surface.
    - **Iterative design lesson from session:** watchdog → self-contained catch-up → no catch-up (simplify based on actual environment). Each step was driven by the user's real operational reality.

18. **`no_agent=True` requires a script** — The `script` field is mandatory when `no_agent=True`. The script IS the job (no LLM call). Stdout = message delivered, empty = silent, non-zero exit = error alert. A watchdog without a script cannot use `no_agent=True` — it would need an LLM prompt (agent mode) or a real script file. This was a concrete blocker in the session: the watchdog job had `no_agent` not set and no `script`, so it ran in agent mode; converting it would have required creating a watchdog script first.

## Templates

- `templates/cleanup_shorts.py` — Generic cleanup script template for `no_agent=True` cron jobs. Copy to your project's `cron/` folder, adapt paths/rules, reference as `script="cron/cleanup_shorts.py"` in cronjob update. Includes Windows-safe `shutil.rmtree` with `onerror` handler and silent-on-success / noisy-on-failure stdout pattern.

## Verification Checklist

After creating/updating a job:
- [ ] `cronjob(action="list")` shows the job with correct `schedule`, `deliver`, `next_run_at`
- [ ] `next_run_at` matches expected local time (check timezone)
- [ ] `workdir` points to correct project (if using AGENTS.md/CLAUDE.md)
- [ ] `skills` list includes required skills (order matters)
- [ ] `enabled_toolsets` matches what the prompt needs
- [ ] For `no_agent=True`: script exists at `workdir/references/...` or absolute path, is executable, produces correct stdout format

## References

- `references/cdp-browser-isolation-pattern.md` — Concrete fix for CDP port/profile conflicts when scheduled jobs launch Chromium-family browsers (Edge/Chrome) for headless automation.
- `references/agent-to-script-conversion.md` — Complete recipe for converting agent-driven cron jobs to `no_agent=True` script-driven jobs.
- `references/session-2026-06-17-cron-lessons.md` — Session-specific findings: model override clearing, cleanup frequency, cron output debugging, memory backup pattern, Windows environment awareness.

## Related Skills

- `hermes-agent` — Full Hermes CLI reference including `hermes cron` commands
- `kanban-orchestrator` / `kanban-worker` — Durable task queue alternative for complex workflows