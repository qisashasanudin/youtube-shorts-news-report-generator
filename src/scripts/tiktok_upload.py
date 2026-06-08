#!/usr/bin/env python3
"""TikTok upload helper: generate optimized TikTok metadata and an upload-ready package for a finished Shorts MP4."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = PROJECT_ROOT / "videos" / "TO_UPLOAD"
TIKTOK_META_DIR = PROJECT_ROOT / "videos" / "tiktok_meta"


@dataclass(frozen=True)
class TikTokMeta:
    video_path: str
    title: str
    caption: str
    hashtags: List[str]
    scheduled_time: Optional[str] = None


def build_tiktok_caption(title: str, subtitle: str, hashtags: List[str]) -> str:
    base = f"{title}\n\n{subtitle}"
    tags = " ".join(f"#{t.strip('#')}" for t in hashtags[:8])
    return f"{base}\n\n{tags}"


def build_tiktok_hashtags(title: str) -> List[str]:
    base = ["#fyp", "#foryou", "#foryoupage"]
    words = [w for w in title.replace("'", " ").split() if len(w) > 3][:5]
    tags = [f"#{w.lower()}" for w in words]
    seen = set()
    out: List[str] = []
    for t in base + tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out[:10]


def ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    TIKTOK_META_DIR.mkdir(parents=True, exist_ok=True)


def save_meta(meta: TikTokMeta) -> Path:
    ensure_dirs()
    stem = Path(meta.video_path).stem
    out = TIKTOK_META_DIR / f"{stem}.tiktok.json"
    payload = {
        "video_path": meta.video_path,
        "title": meta.title,
        "caption": meta.caption,
        "hashtags": meta.hashtags,
        "scheduled_time": meta.scheduled_time,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate TikTok upload metadata for a Shorts video.")
    parser.add_argument("video", help="Path to the final MP4")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--subtitle", default="", help="Short caption/narration summary")
    parser.add_argument("--hashtags", default="", help="Comma-separated hashtags")
    parser.add_argument("--schedule", default="", help="ISO publish time, e.g. 2026-06-08T20:00:00+07:00")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    hashtags = [h.strip() for h in args.hashtags.split(",") if h.strip()] or build_tiktok_hashtags(args.title)
    caption = build_tiktok_caption(args.title, args.subtitle, hashtags)
    meta = TikTokMeta(
        video_path=str(args.video),
        title=args.title,
        caption=caption,
        hashtags=hashtags,
        scheduled_time=args.schedule or None,
    )
    out = save_meta(meta)
    print(f"TikTok package ready: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
