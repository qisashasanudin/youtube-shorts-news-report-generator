#!/usr/bin/env python3
"""
Full mirror backup — mirrors memories, skills, and cron to external folder.
Runs every 15m via cron. No threshold; destination always reflects source.

Place at: ~/.hermes/scripts/full_mirror_backup.py
Cron:   hermes cron create "15m" --name "Hermes Full Mirror Backup" --script "full_mirror_backup.py" --no-agent --repeat -1
"""
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────────
HERMES_BASE = Path(os.environ.get("HERMES_BASE", Path.home() / "AppData" / "Local" / "hermes"))
BACKUP_BASE = Path(os.environ.get("BACKUP_BASE", Path.home() / "hermes-backup"))

DIRS_TO_BACKUP = [
    ("memories", HERMES_BASE / "memories"),
    ("skills", HERMES_BASE / "skills"),
    ("cron", HERMES_BASE / "cron"),
]

# ─── Helpers ─────────────────────────────────────────────────────────────
def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def mirror_dir(src: Path, dst: Path, name: str) -> bool:
    """Mirror src -> dst (rsync-like: delete orphaned, copy new/updated)."""
    if not src.exists():
        log(f"  {name}: source not found at {src}, skipping")
        return False

    dst.mkdir(parents=True, exist_ok=True)

    # Remove orphaned items in dest
    if dst.exists():
        for item in dst.iterdir():
            if not (src / item.name).exists():
                log(f"  {name}: removing orphaned {item.name}")
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

    # Copy new/updated items
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
            # Only copy if newer or doesn't exist
            if not dst_item.exists() or src_item.stat().st_mtime > dst_item.stat().st_mtime:
                shutil.copy2(src_item, dst_item)
                copied += 1

    log(f"  {name}: synced {copied} items")
    return True

# ─── Main ────────────────────────────────────────────────────────────────
def main() -> int:
    log("Starting Hermes full mirror backup...")
    BACKUP_BASE.mkdir(parents=True, exist_ok=True)

    success = all(
        mirror_dir(src, BACKUP_BASE / name, name)
        for name, src in DIRS_TO_BACKUP
    )

    if success:
        log("Backup completed successfully")
    else:
        log("Backup completed with warnings")

    return 0  # Always exit 0 for cron — warnings aren't failures

if __name__ == "__main__":
    sys.exit(main())