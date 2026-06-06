#!/usr/bin/env python3
"""One-shot YouTube Shorts builder.

Usage:
    python shorts_builder.py --youtube "<url>" --title "<TITLE>" --subtitle "<SCRIPT TEXT>"

The script is self-contained and follows the proven Stuntman/Silent Hill pipeline:
  1. Download trailer with yt-dlp
  2. Generate TTS voiceover (Edge TTS)
  3. Build segmented edit (6x5s random clips, fixed seed)
  4. Render 720x1280 final with burned Whoosh ASS captions
  5. Copy to TO_UPLOAD and verify
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
        # Try common install locations
        candidates = [
            REPO / "apps/edge-tts.exe",
            REPO / "venv/Scripts/edge-tts.exe",
            REPO / ".venv/Scripts/edge-tts.exe",
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
        "Style: Default,Whoosh,120,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,6,1.2,2,40,40,160,0",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    for i, w in enumerate(words):
        s = max(0.0, i * per_word)
        e = s + word_dur
        lines.append(
            f"Dialogue: 0,{_ts(s)},{_ts(e)},Default,,,,,,{w.upper()}\r\n"
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

    def _safe_filename(text: str) -> str:
        safe = "".join(c if (c.isalnum() or c in " -_") else "-" for c in text)
        safe = safe.replace(" ", "-")
        safe = "-".join(part for part in safe.split("-") if part)
        return safe[:120]

    def _clean_old_work_dirs() -> None:
        if not SRC_VIDEOS.exists():
            return
        for child in SRC_VIDEOS.iterdir():
            if child.is_dir() and child.name != "TO_UPLOAD":
                shutil.rmtree(child, ignore_errors=True)

    work = SRC_VIDEOS / _slugify(args.title)
    clips_dir = work / "clips"
    reordered = clips_dir / "reordered.mp4"
    audio = work / "audio/voiceover.mp3"
    ass = work / "captions/captions.ass"
    font_dir = DEFAULT_FONT_DIR

    if work.exists():
        try:
            shutil.rmtree(work)
        except Exception:
            # Work dir cleanup is best-effort; stale files can remain if locked.
            pass
    ensure_dir(work)
    ensure_dir(TO_UPLOAD)

    final_out = TO_UPLOAD / f"{_safe_filename(args.title)}.mp4"

    print(f"[INFO] project={work}")
    print(f"[INFO] title={args.title}")

    print(f"[INFO] subtitle word count: {len(args.subtitle.split())}")

    # 1) download / reuse trailer
    trailer = clips_dir / "trailer_full.mp4"
    if trailer.exists() and trailer.stat().st_size > 0:
        trailer_meta = {
            "skipped": True,
            "path": str(trailer),
            "duration": probe_duration(trailer),
        }
        print(f"[1/6] trailer already cached: {trailer}")
    else:
        trailer_meta = download_trailer(args.youtube, trailer)
        if not trailer_meta.get("skipped"):
            print(f"[1/6] downloaded trailer: {trailer}")
    print(f"      source duration: {trailer_meta['duration']:.1f}s")

    # 2) tts
    print("[2/6] generating voiceover...")
    audio_dur = generate_voiceover(args.subtitle, audio)

    # 3) segmented edit
    print("[3/6] building segmented edit...")
    build_segmented_edit(trailer, clips_dir, reordered, audio_dur)

    # 4) captions
    print("[4/6] generating captions...")
    generate_ass(args.subtitle, audio_dur, ass)

    # 5) render
    print("[5/6] rendering final...")
    render_final(work, reordered, audio, ass, font_dir, final_out)

    # 6) verify
    print("[6/6] verifying final...")
    verify(final_out)

    print("[DONE]")


if __name__ == "__main__":
    main()
