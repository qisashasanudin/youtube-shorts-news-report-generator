from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC_VIDEOS = REPO / "videos"
TO_UPLOAD = SRC_VIDEOS / "TO_UPLOAD"
DEFAULT_FONT_DIR = REPO / "assets/fonts/whoosh"

if not DEFAULT_FONT_DIR.exists():
    sys.exit(f"[ERROR] Whoosh font dir missing: {DEFAULT_FONT_DIR}")


def _find_tool(name: str) -> Path:
    if name == "ffmpeg":
        candidates = [shutil.which("ffmpeg-full") or ""]
        if sys.platform == "darwin":
            candidates.extend([
                "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",
                "/usr/local/opt/ffmpeg-full/bin/ffmpeg",
            ])
        candidates.append(shutil.which("ffmpeg") or "")
    elif name == "ffprobe":
        candidates = [shutil.which("ffprobe-full") or ""]
        if sys.platform == "darwin":
            candidates.extend([
                "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe",
                "/usr/local/opt/ffmpeg-full/bin/ffprobe",
            ])
        candidates.append(shutil.which("ffprobe") or "")
    else:
        candidates = [shutil.which(name) or ""]

    for candidate in candidates:
        if candidate:
            candidate_path = Path(candidate)
            if candidate_path.exists():
                return candidate_path

    raise FileNotFoundError(
        f"[ERROR] Required tool '{name}' was not found in PATH or Homebrew opt directories."
    )


FFMPEG = _find_tool("ffmpeg")
FFPROBE = _find_tool("ffprobe")
