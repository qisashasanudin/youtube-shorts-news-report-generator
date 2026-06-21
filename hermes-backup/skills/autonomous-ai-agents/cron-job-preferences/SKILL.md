---
name: cron-job-preferences
description: Reusable rules for creating and managing Hermes cron jobs with the right model inheritance and override behavior.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cron, jobs, model, override, scheduler]
---

# Cron Job Preferences

Use this to keep cron configuration aligned with the active Hermes model setup and avoid unnecessary per-job model duplication.

## Hard automation rule

**Never remove automation for jobs the user depends on.** If a recurring job is the reason the user is using Hermes, a "manual step" fix is itself a failure. Prefer a script-backed `no_agent=True` job over asking the user to run something.

```bash
hermes cron update <id> --no-agent --script "python src/scripts/scheduler_search.py"
```

## When the AI search path can't feed output files

If an AI-driven cron run can write its output file only through brittle web tooling, replace the prompt-driven search step with a deterministic local helper script. The job still runs on schedule, still delivers automatically, and doesn't require manual execution.

## Script Organization Best Practices

**CRITICAL: Cron script paths are resolved from `~/AppData/Local/hermes/scripts/`, NOT from the job's workdir.**

When you set `script="cron/cleanup_shorts.py"` in a cronjob update, Hermes looks for the script at:
```
~/AppData/Local/hermes/scripts/cron/cleanup_shorts.py
```
NOT at:
```
<workdir>/cron/cleanup_shorts.py
```

This is a common pitfall. The `workdir` setting affects the agent's working directory for `terminal`/`file` tools, but the `script` field is always resolved relative to the Hermes scripts directory.

### Two valid patterns:

**Pattern A: Project-local scripts (recommended for version control)**
```
project-repo/
├── cron/
│   ├── cleanup_shorts.py
│   ├── backup_memory.py
│   └── scheduler_search.py
├── src/
└── ...
```
Deploy by copying scripts to `~/AppData/Local/hermes/scripts/`:
```bash
cp project-repo/cron/*.py ~/AppData/Local/hermes/scripts/
cronjob(action="update", job_id="<id>",
        no_agent=True, script="cleanup_shorts.py",  # basename only!
        prompt="", skills=[])
```

**Pattern B: Direct Hermes scripts folder**
```
~/AppData/Local/hermes/scripts/
├── cleanup_shorts.py
├── backup_memory.py
└── scheduler_search.py
```
```python
cronjob(action="update", job_id="<id>",
        no_agent=True, script="cleanup_shorts.py",
        prompt="", skills=[])
```

**Do NOT use:** `script="cron/cleanup_shorts.py"` expecting it to resolve from workdir — it won't.

## Script Organization Best Practices (Legacy Guidance)

**Prefer project-local `cron/` folder for cron scripts** over `~/AppData/Local/hermes/scripts/`:
- Scripts live in the repo they operate on (version controlled, portable)
- Co-locates automation logic with the project code
- Easier to review, test, and iterate alongside the main codebase

**Pattern:**
```
project-repo/
├── cron/
│   ├── cleanup_shorts.py      # no_agent cleanup
│   ├── backup_memory.py       # no_agent backup
│   └── scheduler_search.py    # web search script
├── src/
└── ...
```

**Cronjob update with project-local script (after deploying to scripts dir):**
```python
cronjob(action="update", job_id="<id>",
        no_agent=True, script="cleanup_shorts.py",  # basename, not path!
        prompt="", skills=[])
```

## Pitfalls

- **Empty-output success:** a cron job can return `ok` while writing `{"stories": []}` because the prompt-side web search silently fails. Don't rely on job status alone.
- **`cronjob update` model clearing:** do not try to clear per-job model/provider via the tool by passing `null`. Use `hermes cron edit <id>` if you need a job to inherit the main config default after it had an explicit override.
- **Browser tools don't execute in cron agents:** cron jobs with `no_agent: false` + `enabled_toolsets: ["browser"]` return "ok" but silently skip browser_navigate, browser_snapshot, browser_click, and write_file calls. See `references/cron-browser-limitation.md` for details and workaround (direct HTTP to Bing News RSS).
- **Script path resolution is ALWAYS from `~/AppData/Local/hermes/scripts/`, never from workdir.** The `script` field in cronjob updates is resolved relative to the Hermes scripts directory. If you use `script="cron/cleanup_shorts.py"`, it looks for `~/AppData/Local/hermes/scripts/cron/cleanup_shorts.py`. The `workdir` setting only affects the agent's terminal/file tool cwd, NOT script resolution. To use project-local scripts, copy them to the Hermes scripts dir (or subdirectories there) and reference by basename only: `script="cleanup_shorts.py"`.
- **Windows Task Scheduler vs Hermes cron:** Legacy `.ps1` files checking Windows Task Scheduler (via `Get-ScheduledTask`) are irrelevant for Hermes cron jobs. Hermes manages its own scheduler (`cronjob` tool / `hermes cron` CLI) with jobs stored in `~/AppData/Local/hermes/cron/jobs.json`. Windows Task Scheduler only contains the `Hermes_Gateway` task for the messaging gateway service.

## Clearing overrides

If a cron job has an explicit model/provider but should now inherit the main config default, use `hermes cron edit <job-id>` to remove the explicit model/provider from that job.

Some programmatic update paths treat clearing these fields as a no-op. The edit path is the reliable way to revert a cron job back to config defaults.

**If both `cronjob update` (with null model/provider) and `hermes cron edit` fail with "No updates provided"**, directly edit the jobs database:
```
~/AppData/Local/hermes/cron/jobs.json
```
Find the job by `id`, set `"model": null, "provider": null` in its object. The cron scheduler picks up changes on the next tick.