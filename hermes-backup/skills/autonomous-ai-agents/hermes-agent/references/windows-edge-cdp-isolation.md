# Windows Edge CDP Isolation for Hermes Schedulers

**Problem:** Hermes cron jobs that launch headless Edge with CDP (Chrome DevTools Protocol) on port 9222 conflict with the user's personal Edge browser — killing their browser, locking their profile, preventing normal use.

**Root Cause:** The scheduler script used:
- Default CDP port 9222 (same port user's Edge might use for debugging)
- User's personal Edge profile: `%LOCALAPPDATA%\Microsoft\Edge\User Data`
- `taskkill /f /im msedge.exe` — kills ALL Edge processes including user's

**Solution:** Isolate the scheduler's browser completely:

```python
# In scheduler script (e.g., mashbutton_scheduler_search.py)

# 1. Use a DIFFERENT port (not 9222)
EDGE_CDP_PORT = 9223  # or any free port
EDGE_CDP_URL = f"http://127.0.0.1:{EDGE_CDP_PORT}"

# 2. Use a DEDICATED user data directory (not user's personal profile)
SCHEDULER_EDGE_USER_DATA = Path.home() / ".hermes" / "edge-scheduler-profile"
SCHEDULER_EDGE_USER_DATA.mkdir(parents=True, exist_ok=True)

# 3. Launch with isolated profile — NO taskkill
cmd = [
    edge_exe,
    f"--remote-debugging-port={EDGE_CDP_PORT}",
    "--headless=new",
    f"--user-data-dir={SCHEDULER_EDGE_USER_DATA}",  # isolated!
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-extensions",
    "--disable-background-networking",
    "about:blank",
]
subprocess.Popen(cmd, creationflags=subprocess.DETACHED_PROCESS, ...)
```

**Result:**
| Before (broken) | After (fixed) |
|-----------------|---------------|
| Scheduler uses user's personal Edge profile | Scheduler uses `~/.hermes/edge-scheduler-profile/` |
| Scheduler holds port 9222 | Scheduler uses port 9223 |
| Scheduler kills ALL Edge processes | Scheduler never touches user's Edge |
| User can't open Edge normally | User's Edge works perfectly |

**Verification:**
```bash
# Check CDP ports
netstat -ano | findstr :922

# Should show:
#   9222 → user's Edge (if they have devtools open)
#   9223 → scheduler's headless Edge (isolated profile)

# Check processes
tasklist | findstr msedge.exe
# Scheduler's process uses the isolated profile directory
```

**Key Principle:** Any Hermes cron job that launches a browser **must** use:
1. A dedicated port (avoid 9222)
2. A dedicated user data directory under `~/.hermes/` or project-specific path
3. **Never** `taskkill /im msedge.exe` or similar — it kills the user's browser

**Applies to:** Any scheduler/script using `browser` toolset, CDP, or headless Chromium/Edge on Windows.