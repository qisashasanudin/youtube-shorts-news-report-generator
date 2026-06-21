from __future__ import annotations

import subprocess
from pathlib import Path

from config import FFMPEG, FFPROBE


def run(cmd, check=False, **kwargs):
    if isinstance(cmd, str):
        print(f"[RUN] {cmd}")
    else:
        print(f"[RUN] {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, check=check, **kwargs)


def probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            str(FFPROBE),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    ).decode().strip()
    return float(out)


def slugify(text: str) -> str:
    text = text.strip().upper()
    text = "".join(c for c in text if c.isalnum() or c in " _#")
    text = text.replace(" ", "_")
    return "_".join(part for part in text.split("_") if part)[:80]


def now_stamp(fmt: str = "%Y-%m-%d-%H-%M-%S") -> str:
    from datetime import datetime

    return datetime.now().strftime(fmt)
