---
name: smart-cron-backup
description: "Conditional periodic backup pattern — run cron hourly but only execute backup if last backup is older than threshold (e.g., 24h). Handles laptop sleep/off gracefully."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [backup, cron, automation, memory, persistence, conditional-execution]
  homepage: ""
---

# Smart Cron Backup Pattern

A reusable pattern for **conditional periodic backups** that runs frequently (hourly) but only performs actual work when enough time has passed since the last successful backup.

---

## Problem

Standard cron jobs either:
- Run too frequently (hourly) → waste resources, clutter backup folder
- Run too infrequently (daily) → miss backups if machine is off at scheduled time

## Solution

**Run cron hourly, but script checks last backup timestamp before executing.**

```
┌─────────────────────────────────────────────────────────────┐
│  Hourly Cron Trigger                                        │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Check: last_backup_age > THRESHOLD (e.g., 24h)?    │   │
│  └─────────────────────────────────────────────────────┘   │
│       │                    │                                  │
│      YES                   NO                                 │
│       │                    │                                  │
│       ▼                    ▼                                  │
│  Perform backup        Skip silently                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation

### Script: `scripts/conditional_backup.py`

```python
#!/usr/bin/env python3
"""
Conditional backup — only runs if last backup > threshold hours ago.
"""
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

SOURCE_DIR = Path(os.environ.get("BACKUP_SOURCE", "/path/to/source"))
DEST_DIR = Path(os.environ.get("BACKUP_DEST", "/path/to/dest"))
FILE_PATTERNS = ["*.md", "*.json"]  # Files to backup
THRESHOLD_HOURS = int(os.environ.get("BACKUP_THRESHOLD_HOURS", "24"))

def get_latest_backup_time(dest: Path) -> datetime | None:
    if not dest.exists():
        return None
    files = list(dest.glob("*"))
    if not files:
        return None
    return datetime.fromtimestamp(max(f.stat().st_mtime for f in files))

def should_backup() -> bool:
    latest = get_latest_backup_time(DEST_DIR)
    if latest is None:
        return True
    return (datetime.now() - latest) > timedelta(hours=THRESHOLD_HOURS)

def perform_backup() -> bool:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # ... copy logic here ...
    return True

if __name__ == "__main__":
    if should_backup():
        perform_backup()
```

---

## Cron Configuration

| Schedule | Why |
|----------|-----|
| `* * * * *` (every minute) | Too frequent |
| `0 * * * *` (hourly) | **Recommended** — catches machine wake quickly |
| `0 */6 * * *` (every 6h) | Acceptable if hourly too much |

### Hermes Cron Job

```bash
hermes cron create "1h" \
  --name "Smart Backup" \
  --script "conditional_backup.py" \
  --no-agent \
  --repeat -1
```

---

## Key Features

| Feature | Benefit |
|---------|---------|
| **Timestamped backups** | `FILE_2026-06-15_14-30-00.md` — full history |
| **Latest symlinks** | `FILE.md` always points to most recent |
| **Graceful laptop sleep** | Missed hours don't matter — next run catches up |
| **Configurable threshold** | `BACKUP_THRESHOLD_HOURS` env var |
| **Silent skip** | No noise when not needed |

---

## Pitfalls & Fixes

| Pitfall | Fix |
|---------|-----|
| Cron runs but machine asleep | Hourly schedule catches wake-up |
| Backup folder grows unbounded | Add retention policy (keep last N) |
| Permission errors on dest | Run cron as same user owning files |
| Script crashes silently | Redirect stdout/stderr to log file |

---

## Variations

| Use Case | Threshold | Files |
|----------|-----------|-------|
| Memory/docs | 24h | `*.md`, `*.json` |
| Database dumps | 6h | `*.sql`, `*.dump` |
| Config snapshots | 12h | `*.yaml`, `*.conf` |
| Code checkpoints | 1h | `*.py`, `*.js` |

---

## Full Mirror Backup Pattern (Alternative)

For cases where you want a **live mirror** of all Hermes config (memories + skills + cron) that updates frequently without threshold logic:

| Property | Value |
|----------|-------|
| **Schedule** | `15m` (every 15 minutes) |
| **Mode** | Rsync-like mirror — always syncs, no skip |
| **Scope** | `memories/`, `skills/`, `cron/` (entire dirs) |
| **Destination** | `~/hermes-backup/` (flat structure) |
| **Retention** | None — destination always mirrors source |

### Script: `scripts/full_mirror_backup.py`

```python
#!/usr/bin/env python3
"""
Full mirror backup — mirrors memories, skills, and cron to external folder.
Runs every 15m via cron. No threshold; destination always reflects source.
"""
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERMES_BASE = Path.home() / "AppData" / "Local" / "hermes"
BACKUP_BASE = Path.home() / "hermes-backup"

DIRS_TO_BACKUP = [
    ("memories", HERMES_BASE / "memories"),
    ("skills", HERMES_BASE / "skills"),
    ("cron", HERMES_BASE / "cron"),
]

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def mirror_dir(src: Path, dst: Path, name: str):
    if not src.exists():
        log(f"  {name}: source not found at {src}, skipping")
        return False
    dst.mkdir(parents=True, exist_ok=True)
    # Remove orphaned items in dest
    if dst.exists():
        for item in dst.iterdir():
            if not (src / item.name).exists():
                log(f"  {name}: removing orphaned {item.name}")
                shutil.rmtree(item) if item.is_dir() else item.unlink()
    # Copy new/updated
    copied = 0
    for item in src.iterdir():
        src_item = item
        dst_item = dst / item.name
        if src_item.is_dir():
            if dst_item.exists():
                shutil.rmtree(dst_item)
            shutil.copytree(src_item, dst_item)
            copied += 1
        else:
            if not dst_item.exists() or src_item.stat().st_mtime > dst_item.stat().st_mtime:
                shutil.copy2(src_item, dst_item)
                copied += 1
    log(f"  {name}: synced {copied} items")
    return True

def main():
    log("Starting Hermes full mirror backup...")
    BACKUP_BASE.mkdir(parents=True, exist_ok=True)
    success = all(mirror_dir(src, BACKUP_BASE / name, name) for name, src in DIRS_TO_BACKUP)
    log("Backup completed successfully" if success else "Backup completed with warnings")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Cron Job Setup

```bash
hermes cron create "15m" \
  --name "Hermes Full Mirror Backup" \
  --script "full_mirror_backup.py" \
  --no-agent \
  --repeat -1
```

### When to Use Which

| Scenario | Use |
|----------|-----|
| Want history + don't need instant sync | **Conditional** (hourly, timestamped, 24h threshold) |
| Need live mirror for DR / quick restore | **Full Mirror** (15m, always syncs, no history) |
| Both | Run both — they're complementary |

---

## References

- `references/conditional_backup.py` — Full working script
- `references/hermes_cron_setup.md` — Hermes-specific cron setup
- `references/backup_retention.md` — Optional retention policy

---

## Installation

```bash
# 1. Copy script to your scripts dir
cp references/conditional_backup.py ~/scripts/

# 2. Make executable
chmod +x ~/scripts/conditional_backup.py

# 3. Set env vars (in .bashrc, .env, or cron env)
export BACKUP_SOURCE="/path/to/source"
export BACKUP_DEST="/path/to/backup"
export BACKUP_THRESHOLD_HOURS="24"

# 4. Add cron (or use hermes cron)
crontab -e
# 0 * * * * /home/user/scripts/conditional_backup.py >> /var/log/backup.log 2>&1
```

---

## Testing

```bash
# Force backup (bypass threshold)
BACKUP_THRESHOLD_HOURS=0 python conditional_backup.py

# Dry run
python conditional_backup.py --dry-run

# Check last backup time
python -c "from conditional_backup import get_latest_backup_time; print(get_latest_backup_time(Path('/backup')))"
```