# Backup Retention Policy

## Problem

Timestamped backups accumulate over time (`FILE_2026-06-15_14-30-00.md`, `FILE_2026-06-14_10-00-00.md`, etc.). Without cleanup, the backup folder grows unbounded.

## Solution: Per-Stem Retention

Keep only the **N most recent timestamped versions per file stem**.

```
Before pruning (KEEP=3):
  MEMORY_2026-06-10_10-00-00.md
  MEMORY_2026-06-11_14-30-00.md
  MEMORY_2026-06-12_09-15-00.md
  MEMORY_2026-06-13_16-45-00.md
  MEMORY_2026-06-14_12-00-00.md
  MEMORY_2026-06-15_10-30-00.md
  USER_2026-06-10_10-00-00.md
  USER_2026-06-11_14-30-00.md
  USER_2026-06-12_09-15-00.md
  USER_2026-06-13_16-45-00.md
  USER_2026-06-14_12-00-00.md
  USER_2026-06-15_10-30-00.md

After pruning (KEEP=3):
  MEMORY_2026-06-13_16-45-00.md  ← kept (3 newest)
  MEMORY_2026-06-14_12-00-00.md  ← kept
  MEMORY_2026-06-15_10-30-00.md  ← kept
  USER_2026-06-13_16-45-00.md    ← kept
  USER_2026-06-14_12-00-00.md    ← kept
  USER_2026-06-15_10-30-00.md    ← kept
```

## Configuration

```bash
# Number of timestamped backups to keep per stem
# Set to 0 or negative to disable pruning
BACKUP_KEEP_TIMESTAMPED=10
```

## Algorithm

```python
def prune_old_backups(dest_dir: Path, keep: int) -> None:
    if keep <= 0:
        return

    by_stem: dict[str, list[Path]] = {}

    for f in dest_dir.iterdir():
        if not f.is_file():
            continue
        # Parse stem_YYYY-MM-DD_HH-MM-SS.suffix
        stem, _, ts_str = f.stem.rpartition("_")
        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%d_%H-%M-%S")
        except ValueError:
            continue  # Not a timestamped file
        by_stem.setdefault(stem, []).append((ts, f))

    for stem, entries in by_stem.items():
        entries.sort(key=lambda x: x[0], reverse=True)  # Newest first
        for _, old_file in entries[keep:]:
            old_file.unlink()
            log("INFO", f"Pruned: {old_file.name}")
```

## Edge Cases Handled

| Case | Behavior |
|------|----------|
| Non-timestamped files (`FILE.md`) | Never pruned |
| Malformed timestamps | Skipped (not timestamped) |
| Fewer than `keep` files | None pruned |
| `keep <= 0` | Pruning disabled |

## Recommended Values

| Use Case | Retention |
|----------|-----------|
| Daily docs/memory | 30 (≈1 month at daily) |
| Hourly configs | 168 (1 week at hourly) |
| Frequent checkpoints | 24 (1 day at hourly) |
| Critical data | 100+ (long history) |

## Integration

The `conditional_backup.py` script includes pruning automatically after each successful backup. Configure via:

```bash
export BACKUP_KEEP_TIMESTAMPED=30
```