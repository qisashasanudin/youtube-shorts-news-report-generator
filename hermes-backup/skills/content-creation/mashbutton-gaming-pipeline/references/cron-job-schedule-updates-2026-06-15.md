# Cron Job Schedule Updates (2026-06-15)

**Session:** 2026-06-15  
**Changes:** All monitoring/backup jobs aligned to 15-minute cadence

## Job Updates

### 1. `shorts-news-watchdog` (`bab0abf9f152`)
- **Before:** `every 30m`
- **After:** `every 15m`
- **Purpose:** Pipeline health check — verifies scheduler/builder jobs running
- **Delivery:** `local` (silent unless issues)
- **Toolsets:** `terminal`, `cronjob`

### 2. `shorts-news-cleanup` (`477b924aca59`)
- **Before:** `0 3 * * *` (daily 3:00 AM)
- **After:** `every 15m`
- **Purpose:** Repo cleanup — removes temp files, old artifacts, failed renders
- **Behavior:** Exits quietly if nothing to do (safe for frequent runs)
- **Delivery:** `local`
- **Toolsets:** `terminal`, `file`

### 3. `Memory Backup to External Folder` (`8c2f7219609a`)
- **Before:** `once in 1h` with `repeat: forever` (broken — ran once, disabled)
- **After:** `every 15m` (script gates to 24h minimum internally)
- **Purpose:** Backs up `MEMORY.md` + `USER.md` to `~/Documents/Backups/Hermes Agent's Memory`
- **Script:** `backup_memory.py` (has 24h gate — skips if last backup < 24h old)
- **Behavior:** Creates timestamped snapshots + updates latest files; skips silently if <24h
- **Delivery:** `origin` (sends result to chat)
- **Toolsets:** `script` only (`no_agent: true`)

### 4. `shorts-news-scheduler` (`80c55b5a2392`) — unchanged schedule
- **Schedule:** `0 10,13,16,19 * * *` (4×/day at 10:00, 13:00, 16:00, 19:00 WIB)
- **Toolsets updated:** `browser`, `terminal`, `file` (was `web`, `terminal`, `file`)
- **Skill added:** `browser-search`
- **Delivery:** `discord` only (Telegram removed per user request)

## Summary Table

| Job | Schedule | Purpose | Delivery |
|-----|----------|---------|----------|
| shorts-news-scheduler | 4×/day (10,13,16,19) | Propose 10 stories | Discord |
| shorts-news-watchdog | **every 15m** | Pipeline health | Local |
| shorts-news-cleanup | **every 15m** | Repo hygiene | Local |
| Memory Backup | **every 15m** (24h gate) | Memory safety | Chat |

All 4 jobs are **enabled** and **scheduled**.