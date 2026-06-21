# Hermes Cron Setup for Smart Backup

## Creating the Cron Job via Hermes CLI

```bash
# Create hourly cron job that runs the backup script
hermes cron create "1h" \
  --name "Smart Memory Backup" \
  --script "conditional_backup.py" \
  --no-agent \
  --repeat -1
```

## Cron Job Details

| Parameter | Value |
|-----------|-------|
| **Schedule** | `1h` (every hour) |
| **Script** | `conditional_backup.py` (in `~/.hermes/scripts/`) |
| **no_agent** | `true` — runs as simple script, no LLM |
| **repeat** | `-1` (forever) |
| **deliver** | `origin` (sends output to originating chat) |

## Verifying the Job

```bash
# List all cron jobs
hermes cron list

# Check specific job
hermes cron status 8c2f7219609a

# Manual test run
hermes cron run 8c2f7219609a

# View logs
tail -f ~/.hermes/logs/gateway.log | grep -i "conditional_backup"
```

## Environment Variables

The script reads these from the cron environment:

```bash
# Required
BACKUP_SOURCE=C:\Users\qthas\AppData\Local\hermes\memories
BACKUP_DEST=C:\Users\qthas\Documents\Backups\Hermes Agent's Memory

# Optional (with defaults)
BACKUP_PATTERNS=*.md,*.json
BACKUP_THRESHOLD_HOURS=24
BACKUP_KEEP_TIMESTAMPED=10
```

Set them via:
1. `~/.hermes/.env` (global for all Hermes processes)
2. `hermes config set` (persisted in config.yaml)
3. Cron job env override (if supported)

## Windows-Specific Notes

- Script uses `python` command — ensure Python is in PATH for cron user
- Paths use raw strings `r"C:\..."` or forward slashes `C:/Users/...`
- Cron runs in background — output goes to `~/.hermes/logs/gateway.log`

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Python not found" | Add Python to system PATH, or use full path `C:\Python311\python.exe` |
| Permission denied | Run cron as same user owning source/dest folders |
| Script not found | Ensure `conditional_backup.py` is in `~/.hermes/scripts/` |
| No output in logs | Check `~/.hermes/logs/gateway.log` for `no_agent` script output |

## Testing Locally

```bash
# Dry run (shows what would happen)
python ~/AppData/Local/hermes/scripts/conditional_backup.py --dry-run

# Force backup (ignore threshold)
python ~/AppData/Local/hermes/scripts/conditional_backup.py --force

# Normal run (respects 24h threshold)
python ~/AppData/Local/hermes/scripts/conditional_backup.py
```