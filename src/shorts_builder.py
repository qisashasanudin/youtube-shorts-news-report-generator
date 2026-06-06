#!/usr/bin/env python3
"""One-shot YouTube Shorts builder.

Usage:
    .venv\Scripts\python.exe src/shorts_builder.py --youtube "<url>" --title "<TITLE>" --subtitle "<SCRIPT TEXT>"

This script is designed to run from the repo root with the project virtual environment.
The built-in TTS fallback prefers the venv Edge TTS binary when available.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional convenience
    load_dotenv = lambda *a, **k: None

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

try:
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import DownloadError
except ImportError:  # pragma: no cover - optional dependency
    YoutubeDL = None
    DownloadError = Exception


class MediaExtractionError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Paths (relative to repo root)
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parent.parent
VIDEOS = REPO / "videos"
SRC_VIDEOS = VIDEOS
TO_UPLOAD = VIDEOS / "TO_UPLOAD"
DEFAULT_FONT_DIR = Path(os.environ.get("FONT_DIR", REPO / "assets/fonts/whoosh"))
if not DEFAULT_FONT_DIR.exists():
    sys.exit(f"[ERROR] Whoosh font dir missing: {DEFAULT_FONT_DIR}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def run(cmd: list[str] | str, **kwargs) -> subprocess.CompletedProcess:
    print(f"[RUN] {' '.join(str(c) for c in cmd) if isinstance(cmd, list) else cmd}")
    return subprocess.run(cmd, **kwargs)


def probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
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


def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# Step 1: download trailer
# ---------------------------------------------------------------------------
def _build_ytdlp_http_headers(url: str, user_agent: str) -> dict:
    return {
        "User-Agent": user_agent,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": url,
        "Origin": "https://www.youtube.com",
    }


def _find_downloaded_file(out_dir: Path) -> Path:
    for candidate in sorted(out_dir.iterdir()):
        if candidate.is_file() and candidate.suffix.lower() == ".mp4":
            return candidate
    raise MediaExtractionError(f"Downloaded MP4 not found in {out_dir}")


def _yt_dlp_meta(url: str) -> dict:
    if YoutubeDL is None:
        sys.exit("[ERROR] yt-dlp is not installed")
    opts = {
        "quiet": True,
        "no_warnings": True,
        "retries": 1,
        "socket_timeout": 15,
    }
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception:
        info = {}
    return info


def download_trailer(url: str, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return {
            "skipped": True,
            "path": str(dest),
            "duration": probe_duration(dest),
        }

    if YoutubeDL is None:
        sys.exit("[ERROR] yt-dlp is not installed")

    outtmpl = str(dest)
    attempts = [
        {
            "format": "bestvideo[ext=mp4][height>=1080]+bestaudio[ext=m4a]/best[ext=mp4][height>=1080]/best[ext=mp4]/best",
            "extractor_args": {"youtube": {"player_client": ["android"]}},
        },
        {
            "format": "bestvideo[ext=mp4][height>=1080]+bestaudio[ext=m4a]/best[ext=mp4][height>=1080]/best[ext=mp4]/best",
            "extractor_args": {"youtube": {"player_client": ["web"]}},
        },
        {"format": "best"},
    ]

    last_error: Exception | None = None
    for idx, attempt in enumerate(attempts):
        opts = {
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "retries": 2,
            "fragment_retries": 2,
            "socket_timeout": 15,
            "timeout": 60,
            "merge_output_format": "mp4",
            **(attempt),
        }
        try:
            with YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)
            resolved = _find_downloaded_file(dest.parent)
            return {
                "skipped": False,
                "path": str(resolved),
                "duration": probe_duration(resolved),
            }
        except DownloadError as error:
            last_error = error
            if idx < len(attempts) - 1:
                time.sleep(0.5 + idx * 0.5)
                continue

    raise MediaExtractionError(
        f"Unable to download media from {url} after fallback attempts. Last error: {last_error}"
    ) from last_error


# ---------------------------------------------------------------------------
# Step 2: TTS voiceover
# ---------------------------------------------------------------------------
def generate_voiceover(text: str, out: Path) -> float:
    out.parent.mkdir(parents=True, exist_ok=True)
    # Prefer Piper if available, otherwise fall back to Edge TTS
    piper = REPO / "apps/piper/piper.exe"
    if piper.exists():
        raw = out.with_suffix(".raw")
        cmd = [
            str(piper),
            "--model",
            str(REPO / "assets/piper/en_US-lessac-medium.onnx"),
            "--output_raw",
            str(raw),
        ]
        proc = subprocess.run(cmd, input=text.encode(), capture_output=True)
        if proc.returncode == 0 and raw.exists():
            # raw -> wav via ffmpeg
            run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "s16le",
                    "-ar",
                    "22050",
                    "-ac",
                    "1",
                    "-i",
                    str(raw),
                    str(out),
                ]
            )
            raw.unlink(missing_ok=True)
            return probe_duration(out)
    # Fallback: Edge TTS
    edge_tts = shutil.which("edge-tts")
    if edge_tts is None:
        candidates = [
            REPO / "apps/edge-tts",
            REPO / "apps/edge-tts.exe",
            REPO / "venv/Scripts/edge-tts.exe",
            REPO / ".venv/Scripts/edge-tts.exe",
            REPO / "venv/bin/edge-tts",
            REPO / ".venv/bin/edge-tts",
        ]
        for c in candidates:
            if c.exists():
                edge_tts = str(c)
                break
    if edge_tts is None:
        sys.exit("[ERROR] No TTS engine found ( Piper or edge-tts)")
    cmd = [
        edge_tts,
        "--voice",
        "en-US-GuyNeural",
        "--rate",
        "+15%",
        "--text",
        text,
        "--write-media",
        str(out),
    ]
    res = run(cmd)
    if res.returncode != 0:
        sys.exit(f"[ERROR] edge-tts failed with code {res.returncode}")
    return probe_duration(out)


# ---------------------------------------------------------------------------
# Step 3: build segmented edit (proven 6x5s pattern)
# ---------------------------------------------------------------------------
def build_segmented_edit(
    source: Path,
    clips_dir: Path,
    reordered: Path,
    duration: float,
) -> None:
    clips_dir.mkdir(parents=True, exist_ok=True)
    random.seed(12345)

    min_seg = 5.0
    max_seg = 5.0
    target = max(duration, 5.0)

    segments: list[float] = []
    remaining = target
    while remaining > 0:
        seg = min(min_seg + random.random() * (max_seg - min_seg), remaining)
        segments.append(seg)
        remaining -= seg

    video_dur = probe_duration(source)
    parts: list[Path] = []

    for i, seg in enumerate(segments):
        max_start = max(0.0, video_dur - seg)
        ss = random.uniform(0, max_start) if max_start > 0 else 0.0
        part = clips_dir / f"part_{i:03d}.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                f"{ss:.3f}",
                "-t",
                f"{seg:.3f}",
                "-i",
                str(source),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(part),
            ],
            check=True,
        )
        parts.append(part)

    filelist = clips_dir / "filelist.txt"
    with filelist.open("w", encoding="utf-8") as f:
        for p in parts:
            f.write(f"file '{p.as_posix()}'\n")

    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(filelist),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(reordered),
        ],
        check=True,
    )
    print(f"[OK] reordered: {reordered}  segments={len(segments)}  duration={round(sum(segments), 3)}")


# ---------------------------------------------------------------------------
# Step 4: generate ASS captions from text + audio duration
# ---------------------------------------------------------------------------
def _ts(t: float) -> str:
    t = max(0.0, float(t))
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"


def generate_ass(
    text: str,
    audio_duration: float,
    ass_path: Path,
) -> None:
    words = text.split()
    per_word = audio_duration / max(1, len(words))
    word_dur = per_word * 0.95

    lines = [
        "[Script Info]",
        "Title: MashButtonGaming",
        "ScriptType: v4.00+",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "PlayResX: 720",
        "PlayResY: 1280",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Whoosh,120,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,6,1.2,5,5,0,0,0,0",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    for i, w in enumerate(words):
        s = max(0.0, i * per_word)
        e = s + word_dur
        lines.append(
            f"Dialogue: 0,{_ts(s)},{_ts(e)},Default,,,,,,{{\\an5}}{w.upper()}\r\n"
        )

    ass_path.parent.mkdir(parents=True, exist_ok=True)
    ass_path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    print(f"[OK] ASS: {ass_path}  words={len(words)}")


# ---------------------------------------------------------------------------
# Step 5: render final
# ---------------------------------------------------------------------------
def _relink(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink(missing_ok=True)
    shutil.copy2(src, dst)
    return dst


def _render_burn_subs(
    work: Path,
    reordered: Path,
    audio: Path,
    ass: Path,
    font_dir: Path | None,
    out: Path,
) -> None:
    dur_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio),
    ]
    dur_res = run(dur_cmd, capture_output=True, text=True, cwd=work)
    if dur_res.returncode != 0:
        sys.exit(f"[ERROR] probe audio duration failed: {dur_res.stderr.strip()}")
    _ = dur_res.stdout.strip()

    font_dir = font_dir or DEFAULT_FONT_DIR
    # Use repository-relative paths to avoid Windows drive-letter parsing issues in the
    # subtitles/freetype filters. Paths are rooted at REPO so they remain correct when
    # ffmpeg is launched from the repo directory.
    vm = reordered.resolve().relative_to(REPO).as_posix()
    am = audio.resolve().relative_to(REPO).as_posix()
    ass_path = ass.resolve().relative_to(REPO).as_posix()
    font_path = font_dir.resolve().relative_to(REPO).as_posix()
    out_path = out.resolve().relative_to(REPO).as_posix()
    ass_rel = ass_path
    font_rel = font_path
    video_rel = vm
    audio_rel = am
    out_rel = out_path

    cmd = [
        "ffmpeg", "-y",
        "-i", video_rel,
        "-i", audio_rel,
        "-filter_complex", f"[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,ass={ass_rel}:fontsdir={font_rel}[v]",
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        out_rel,
    ]
    print("[RUN] ffmpeg subtitle burn ...")
    res = run(cmd, cwd=REPO)
    print("[RUN] ffmpeg subtitle burn ->", res.returncode)
    if res.returncode != 0:
        sys.exit(f"[ERROR] subtitle burn render failed for {out}")


def render_final(
    work: Path,
    reordered: Path,
    audio: Path,
    ass: Path,
    font_dir: Path | None,
    out: Path,
) -> None:
    _render_burn_subs(work, reordered, audio, ass, font_dir, out)


# ---------------------------------------------------------------------------
# Step 6: verify
# ---------------------------------------------------------------------------
def verify(path: Path) -> None:
    if not path.exists():
        sys.exit(f"[ERROR] missing: {path}")
    size = path.stat().st_size
    dur = probe_duration(path)
    print(f"[OK] verify size={size:,} bytes  duration={dur:.3f}s  path={path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def _check_subtitle_words(text: str) -> None:
    words = text.split()
    count = len(words)
    if not (100 <= count <= 200):
        sys.exit(
            f"[ERROR] --subtitle must be 100-200 words for valid TTS duration; got {count} words."
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--youtube", required=True, help="Trailer YouTube URL")
    ap.add_argument("--title", required=True, help="Exact title / filename stem")
    ap.add_argument("--subtitle", required=True, help="TTS/subtitle text (100-200 words)")
    args = ap.parse_args()
    _check_subtitle_words(args.subtitle)

    def _slugify(text: str) -> str:
        text = text.strip().lower()
        text = "".join(c for c in text if c.isalnum() or c in " -_")
        text = text.replace(" ", "-")
        text = "-".join(part for part in text.split("-") if part)
        return text[:80]

    def _now_stamp() -> str:
        return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    def _build_work_dir(title: str) -> Path:
        return SRC_VIDEOS / f"{_now_stamp()}_{_slugify(title)}"

    work = _build_work_dir(args.title)
    print(f"[INFO] project={work}")
    print(f"[INFO] title={args.title}")
    print(f"[INFO] subtitle word count: {len(args.subtitle.split())}")

    trailer_path = work / "clips" / "trailer_full.mp4"
    voice_path = work / "audio" / "voiceover.mp3"
    reordered_path = work / "clips" / "reordered.mp4"
    ass_path = work / "captions" / "captions.ass"
    final_path = TO_UPLOAD / f"{_slugify(args.title)}.mp4"

    dl = download_trailer(args.youtube, trailer_path)
    print(f"[1/6] downloaded trailer: {dl['path']}  source duration: {dl['duration']:.1f}s")

    voice_dur = generate_voiceover(args.subtitle, voice_path)
    print(f"[2/6] generating voiceover... duration={voice_dur:.2f}s")

    build_segmented_edit(trailer_path, work / "clips", reordered_path, voice_dur)
    print(f"[3/6] segmented edit ready")

    generate_ass(args.subtitle, voice_dur, ass_path)
    print(f"[4/6] generating captions...")

    render_final(work, reordered_path, voice_path, ass_path, DEFAULT_FONT_DIR, final_path)
    print(f"[5/6] rendered final to {final_path}")

    verify(final_path)
    print("[DONE]")


if __name__ == "__main__":
    main()
