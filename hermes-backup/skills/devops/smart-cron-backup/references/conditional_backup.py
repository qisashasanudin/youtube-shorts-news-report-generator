#!/usr/bin/env python3
"""
Smart Conditional Backup Script
Runs via hourly cron, but only performs backup if last backup is older than threshold.
Supports laptop sleep/off gracefully.
"""
import os
import shutil
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# ─── Config via environment (with defaults) ──────────────────────────────
SOURCE_DIR = Path(os.environ.get("BACKUP_SOURCE", r"C:\Users\qthas\AppData\Local\hermes\memories"))
DEST_DIR = Path(os.environ.get("BACKUP_DEST", r"C:\Users\qthas\Documents\Backups\Hermes Agent's Memory"))
FILE_PATTERNS = os.environ.get("BACKUP_PATTERNS", "*.md,*.json").split(",")
THRESHOLD_HOURS = int(os.environ.get("BACKUP_THRESHOLD_HOURS", "24"))
KEEP_TIMESTAMPED = int(os.environ.get("BACKUP_KEEP_TIMESTAMPED", "10"))  # Retention

# ─── Helpers ─────────────────────────────────────────────────────────────
def log(level: str, msg: str) -> None:
    print(f"[{datetime.now().isoformat()}] [{level}] {msg}", file=sys.stderr)

def get_latest_backup_time(dest: Path) -> datetime | None:
    """Return mtime of newest file in dest, or None if empty/missing."""
    if not dest.exists():
        return None
    files = list(dest.iterdir())
    if not files:
        return None
    try:
        latest_mtime = max(f.stat().st_mtime for f in files if f.is_file())
        return datetime.fromtimestamp(latest_mtime)
    except ValueError:
        return None

def should_backup() -> bool:
    latest = get_latest_backup_time(DEST_DIR)
    if latest is None:
        log("INFO", f"No previous backup found in {DEST_DIR} → will backup")
        return True
    elapsed = datetime.now() - latest
    threshold = timedelta(hours=THRESHOLD_HOURS)
    if elapsed > threshold:
        log("INFO", f"Last backup {elapsed} ago (> {THRESHOLD_HOURS}h threshold) → will backup")
        return True
    log("INFO", f"Last backup {elapsed} ago (< {THRESHOLD_HOURS}h) → skipping")
    return False

def collect_source_files() -> list[Path]:
    files = []
    for pattern in FILE_PATTERNS:
        files.extend(SOURCE_DIR.rglob(pattern.strip()))
    # Deduplicate
    seen = set()
    unique = []
    for f in files:
        if f.is_file() and f not in seen:
            seen.add(f)
            unique.append(f)
    return unique

def perform_backup(dry_run: bool = False) -> bool:
    if not SOURCE_DIR.exists():
        log("ERROR", f"Source directory not found: {SOURCE_DIR}")
        return False

    DEST_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    files = collect_source_files()

    if not files:
        log("WARNING", f"No files matched patterns {FILE_PATTERNS} in {SOURCE_DIR}")
        return False

    if dry_run:
        log("INFO", f"[DRY RUN] Would backup {len(files)} files:")
        for f in files:
            log("INFO", f"  {f.relative_to(SOURCE_DIR)}")
        return True

    success_count = 0
    for src in files:
        try:
            rel = src.relative_to(SOURCE_DIR)
            # Timestamped version
            stem = src.stem
            suffix = src.suffix
            ts_name = f"{stem}_{timestamp}{suffix}"
            ts_dst = DEST_DIR / ts_name
            shutil.copy2(src, ts_dst)

            # Latest version (overwrites)
            latest_dst = DEST_DIR / rel.name
            shutil.copy2(src, latest_dst)

            log("INFO", f"Backed up {rel} → {ts_name} (and latest)")
            success_count += 1
        except Exception as e:
            log("ERROR", f"Failed to backup {src}: {e}")

    # Retention: prune old timestamped backups
    prune_old_backups()

    if success_count == 0:
        log("ERROR", "No files successfully backed up")
        return False

    log("SUCCESS", f"Backup completed: {success_count} files")
    return True

def prune_old_backups() -> None:
    """Keep only the N most recent timestamped backups per stem."""
    if KEEP_TIMESTAMPED <= 0:
        return
    by_stem: dict[str, list[Path]] = {}
    for f in DEST_DIR.iterdir():
        if not f.is_file():
            continue
        # Match timestamped files: stem_YYYY-MM-DD_HH-MM-SS.suffix
        parts = f.stem.rsplit("_", 1)
        if len(parts) != 2:
            continue
        stem, ts_str = parts
        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%d_%H-%M-%S")
        except ValueError:
            continue
        by_stem.setdefault(stem, []).append((ts, f))

    for stem, entries in by_stem.items():
        entries.sort(key=lambda x: x[0], reverse=True)
        for _, old_file in entries[KEEP_TIMESTAMPED:]:
            try:
                old_file.unlink()
                log("INFO", f"Pruned old backup: {old_file.name}")
            except Exception as e:
                log("WARNING", f"Failed to prune {old_file}: {e}")

# ─── CLI ────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description="Smart conditional backup")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--force", action="store_true", help="Ignore threshold, always backup")
    args = parser.parse_args()

    log("INFO", f"Backup check started (threshold={THRESHOLD_HOURS}h)")

    if args.force or should_backup():
        ok = perform_backup(dry_run=args.dry_run)
        return 0 if ok else 1
    return 0

if __name__ == "__main__":
    sys.exit(main())