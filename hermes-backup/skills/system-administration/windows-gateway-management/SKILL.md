---
name: windows-gateway-management
description: "Windows-specific Hermes gateway lifecycle, status verification, scheduled-task behavior, and cron model fallback."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [win32]
metadata:
  hermes:
    tags: [windows, gateway, scheduled-task, cron, service, troubleshooting]
---

# Windows Gateway Management

Windows-specific behaviors for running the Hermes gateway as a Scheduled Task, verifying its state, and managing cron job model inheritance.

## Gateway Status Verification

`hermes gateway status` is unreliable on Windows. Use the full signal set:

1. `hermes gateway status` — basic task info
2. `hermes gateway status --deep` — includes PID/lock file checks and `gateway_state.json`
3. `cat ~/.hermes/gateway_state.json` — confirm `"state":"running"`
4. `tasklist | grep -i Hermes` — confirm live `Hermes.exe` processes

### Common False Negative

The task can show `Status: Queued` and `Last Run Result: 0` while `gateway status` reports **"No gateway process detected"** even though:
- `gateway_state.json` says `running`
- `Hermes.exe` processes are alive in Task Manager

Trust the combination of `gateway_state.json` + running processes, not `gateway status` alone.

## Scheduled Task Restart Behavior

```powershell
hermes gateway restart
```

This stops and relaunches the `Hermes_Gateway` scheduled task. Expect:
- `✓ Gateway stopped`
- `⚠ Launched gateway via Scheduled Task 'Hermes_Gateway', but no process detected after 6s.`

The 6-second warning is **normal Windows task-launch behavior** and does not mean the gateway failed. Verify with `gateway status --deep` and live process checks above.

## Gateway Receiving UNKNOWN Signal Then Exiting

Symptom: gateway logs show successful Telegram + Discord connection, then 4–5 minutes later:
```
Received UNKNOWN as a planned gateway stop — exiting cleanly
```

This indicates the Scheduled Task run window/timeout is expiring or the task is configured with a bounded run duration.

**Fixes:**
1. Re-register as a proper persistent service:
   ```powershell
   hermes gateway install
   ```
2. Or run in foreground mode to bypass task behavior entirely:
   ```powershell
   hermes gateway run
   ```

Foreground mode blocks the terminal and keeps the gateway alive indefinitely.

## CDP Config Not Picked Up After Restart

Symptom: `~/.hermes/config.yaml` shows `browser.cdp_url: "http://127.0.0.1:9222"`, but gateway logs still show `Failed to resolve CDP endpoint null`.

Cause: the running Hermes process was started before the config change and is reading a stale config snapshot.

**Fix:**
- Use `hermes gateway restart` instead of Ctrl+C + relaunch.
- After restart, verify the browser tool is live before triggering any browser-based search:
  ```bash
  curl -s http://127.0.0.1:9222/json/version
  ```

## Cron Job Model Inheritance

Main model/provider are defined in `~/.hermes/config.yaml`. Individual cron jobs can override per-job, or inherit by leaving the fields unset.

### Important: Clearing Overrides

To make all cron jobs use the same default model:
1. Edit `C:/Users/qthas/AppData/Local/hermes/cron/jobs.json`
2. Remove `"model"` and `"provider"` lines from each job object
3. Restart gateway

The `cronjob` tool does not accept `null` to clear overrides; direct JSON edit is required.

### Current Known Jobs (subject to change)

| Job ID | Name | Notes |
|--------|------|-------|
| 80c55b5a2392 | shorts-news-scheduler | Discord delivery |
| bab0abf9f152 | shorts-news-watchdog | Local delivery |
| 477b924aca59 | shorts-news-cleanup | Local delivery |
| 8c2f7219609a | Memory Backup to External Folder | Script-only (`no_agent: true`) |

## Key File Paths

| File | Path |
|------|------|
| Main config | `C:/Users/qthas/AppData/Local/hermes/config.yaml` |
| Cron jobs | `C:/Users/qthas/AppData/Local/hermes/cron/jobs.json` |
| Gateway state | `C:/Users/qthas/AppData/Local/hermes/gateway_state.json` |
| Gateway PID | `C:/Users/qthas/AppData/Local/hermes/gateway.pid` |
| Gateway logs | `C:/Users/qthas/AppData/Local/hermes/logs/gateway.log` |
| Cron logs | `C:/Users/qthas/AppData/Local/hermes/logs/gateway-stdio.log` |

## Pitfalls

1. **PowerShell path quoting** — `schtasks.exe /End /TN "Hermes_Gateway"` works, but PowerShell may parse `&` or path separators incorrectly. Use full `C:/Windows/System32/schtasks.exe` paths when scripting.
2. **Gateway state stale after kill** — if the gateway process is killed outside the scheduled task, `gateway_state.json` may still say `running`. Always cross-check with live processes.
4. **Config BOM issue** — if `config.yaml` was edited with Notepad and saved as UTF-8 with BOM, first run may fail with HTTP 400 "No models provided". Re-save without BOM using `hermes config edit` or a UTF-8-aware editor.
5. **Service install requires elevation** — `hermes gateway install` may prompt for admin consent. In automation, call the underlying scheduled-task registration directly.

## References

- `references/session-2026-06-17-gateway-lessons.md` — Session-specific findings: gateway process identification, CDP via gateway, Python environment chain, cron model inheritance fix, startup notification cleanup, verification commands, file paths.
