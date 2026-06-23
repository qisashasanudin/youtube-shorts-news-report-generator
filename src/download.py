from __future__ import annotations

import os
from pathlib import Path

from yt_dlp import YoutubeDL
from config import REPO
from utils import probe_duration


class MediaExtractionError(RuntimeError):
    pass


def _build_ytdlp_http_headers(url: str, user_agent: str) -> dict:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.youtube.com/",
    }


def download_trailer(url: str, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    outtmpl = str(dest)
    attempts = [
        {
            "format": "bestvideo[ext=mp4][height<=1080][height>=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080][height>=720]/best[ext=mp4][height<=1080]/best[ext=mp4]/best",
        },
        {
            "format": "bestvideo[ext=mp4][height<=1080][height>=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080][height>=720]/best[ext=mp4][height<=1080]/best[ext=mp4]/best",
            "extractor_args": {"youtube": {"player_client": ["web"]}},
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
        },
        {
            "format": "bestvideo[ext=mp4][height<=1080][height>=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080][height>=720]/best[ext=mp4][height<=1080]/best[ext=mp4]/best",
            "extractor_args": {"youtube": {"player_client": ["android"]}},
        },
        {"format": "299+140/best[filesize<100M]/best"},
    ]
    last_error = None
    for attempt in attempts:
        opts = {
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "retries": 2,
            "fragment_retries": 2,
            "socket_timeout": 900,
            "timeout": 900,
            "merge_output_format": "mp4",
            **attempt,
        }
        try:
            with YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)
        except Exception as exc:
            last_error = exc
            continue

        candidates = sorted(dest.parent.iterdir())
        src = next((p for p in candidates if p.is_file() and p.suffix.lower() == ".mp4"), None)
        if src and src.exists() and src.stat().st_size > 0:
            return {
                "skipped": False,
                "path": str(src),
                "duration": probe_duration(src),
            }
        last_error = FileNotFoundError(f"No MP4 after download in {dest.parent}")

    raise last_error or FileNotFoundError(f"Failed to download trailer from {url}")
