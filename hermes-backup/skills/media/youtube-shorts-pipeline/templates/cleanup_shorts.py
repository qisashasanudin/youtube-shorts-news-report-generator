#!/usr/bin/env python3
"""
Cleanup script for MashButtonGaming Shorts repo.
Run once and exit quietly if there is nothing to report.

Rules:
- Delete `tmp` at the project root if it exists.
- Delete `videos/tmp` if it exists.
- In `videos/`, keep `TO_UPLOAD`; delete all other child dirs/files created by the builder.
- Do NOT touch `videos/TO_UPLOAD`.
- Do NOT delete `src`, `assets`, or repo root files.
- Use removal only on these exact paths: `tmp`, `videos/tmp`, and non-`TO_UPLOAD` items under `videos/`.
- After cleanup, report the paths removed and any errors.
- If nothing was removed, stay silent (exit 0 with no stdout).

Deploy to: ~/AppData/Local/hermes/scripts/cleanup_shorts.py
Cron job config: script="cleanup_shorts.py", no_agent=true
"""
import os
import sys
import shutil
from pathlib import Path


def main():
    # Workdir is set by cronjob; fallback to env or default
    workdir = Path(os.environ.get("CLEANUP_WORKDIR", os.getcwd()))
    if not workdir.exists():
        print(f"[ERROR] Workdir not found: {workdir}", file=sys.stderr)
        return 1

    removed = []
    errors = []

    # 1. Delete `tmp` at project root
    tmp_root = workdir / "tmp"
    if tmp_root.exists():
        try:
            shutil.rmtree(tmp_root)
            removed.append(str(tmp_root))
        except Exception as e:
            errors.append(f"{tmp_root}: {e}")

    # 2. Delete `videos/tmp`
    videos_tmp = workdir / "videos" / "tmp"
    if videos_tmp.exists():
        try:
            shutil.rmtree(videos_tmp)
            removed.append(str(videos_tmp))
        except Exception as e:
            errors.append(f"{videos_tmp}: {e}")

    # 3. In `videos/`, keep `TO_UPLOAD`; delete all non-TO_UPLOAD children
    videos_dir = workdir / "videos"
    if videos_dir.exists():
        for child in videos_dir.iterdir():
            if child.name == "TO_UPLOAD":
                continue
            if child.name == "tmp":
                continue  # already handled above
            try:
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
                removed.append(str(child))
            except Exception as e:
                errors.append(f"{child}: {e}")

    # Report only if something was removed or errors occurred
    if removed:
        for path in removed:
            print(f"[CLEANED] {path}")
    if errors:
        for err in errors:
            print(f"[ERROR] {err}", file=sys.stderr)

    # Exit code: 0 if no errors (even if nothing removed), 1 if any error
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())