#!/usr/bin/env python3
"""
MashButtonGaming pipeline: gaming news → TTS → STT → randomized trailer splice → rendered YouTube Short.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Third-party imports are optional at import time; we fail fast with a helpful message later.
try:
    import requests
except ImportError:
    requests = None  # type: ignore

ROOT = Path(r"C:\Users\qthas\Videos\Youtube Projects\MashButtonGaming")
OUT = ROOT / "output"
TMP = ROOT / "output_tmp"
RENDER = ROOT / "render"
TO_UPLOAD = ROOT / "TO_UPLOAD"
FONTS_DIR = ROOT / "fonts"
FONT_FILE = FONTS_DIR / "burbank_big_condensed.otf"
ASS_PATH = RENDER / "captions.ass"
FINAL_PATH = RENDER / "final.mp4"
VOICEOVER_PATH = OUT / "audio" / "voiceover.mp3"
CAPTIONS_VTT = OUT / "captions" / "captions.vtt"
CAPTIONS_ASS = OUT / "captions" / "captions.ass"
CLIPS_DIR = OUT / "clips"
NEWS_PATH = OUT / "news" / "latest_news.json"
SCRIPT_PATH = OUT / "script" / "script.txt"


@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    published: Optional[str] = None


# Shooter/FPS oriented search queries for broad web search (Bing/Yahoo via search_web.py)
SHOOTER_QUERIES = [
    "battlefield 6 news 2026",
    "call of duty modern warfare 4 news 2026",
    "valorant patch notes 2026",
    "counter-strike 2 update 2026",
    "overwatch 2 new hero 2026",
    "tactical shooter games 2026",
    "rainbow six siege update 2026",
    "escape from tarkov news 2026",
    "apex legends season 2026",
    "halo infinite update 2026",
    "destiny 2 news 2026",
    "fps games 2026 release",
    "third person shooter games 2026",
    "xbox showcase shooter games 2026",
    "playstation shooter games 2026",
]


def fetch_gaming_news(limit: int = 10) -> List[NewsItem]:
    """Fetch recent gaming news from broad web search (Bing/Yahoo)."""
    # Import here to avoid circular imports
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from search_web import search_web

    items: List[NewsItem] = []
    if requests is None:
        raise RuntimeError("requests is required for news fetch. Install requirements.")

    for query in SHOOTER_QUERIES:
        if len(items) >= limit:
            break
        try:
            results = search_web(query, max_results=5)
        except Exception as exc:
            print(f"[news] search failed ({query}): {exc}")
            continue
        for item in results:
            if len(items) >= limit:
                break
            title = item.get("title", "").strip()
            url = item.get("url", "").strip()
            if not title or not url:
                continue
            items.append(NewsItem(title=title, url=url, source=query))

    if not items:
        raise RuntimeError("No gaming news fetched. Check network or search queries.")
    return items


def pick_topic(items: List[NewsItem]) -> NewsItem:
    return random.choice(items)


def write_script(topic: NewsItem, out_path: Path = SCRIPT_PATH) -> Path:
    script = (
        f"{topic.title}. "
        "This is the latest gaming update from Mash Button Gaming. "
        "Follow for more daily gaming news, and drop a comment if you want the next story next."
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(script, encoding="utf-8")
    print(f"[script] wrote {out_path}")
    return out_path


def synthesize_voiceover(script_path: Path = SCRIPT_PATH, out_path: Path = VOICEOVER_PATH) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = script_path.read_text(encoding="utf-8")
    cmd = [
        sys.executable, "-m", "edge_tts",
        "--voice", "en-US-GuyNeural",
        "--rate", "+20%",
        "--text", text,
        "--write-media", str(out_path),
    ]
    print(f"[tts] running edge_tts")
    subprocess.run(cmd, check=True)
    print(f"[tts] wrote {out_path}")
    return out_path


def transcribe_voiceover(audio_path: Path = VOICEOVER_PATH, out_vtt: Path = CAPTIONS_VTT) -> Path:
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), language="en", word_timestamps=True)
    out_vtt.parent.mkdir(parents=True, exist_ok=True)
    with out_vtt.open("w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            if not seg.words:
                continue
            for w in seg.words:
                start = max(float(w.start), 0.0)
                end = max(float(w.end), start)
                f.write(f"{_format_ts(start)} --> {_format_ts(end)}\n{w.word.strip()}\n\n")
    print(f"[stt] wrote {out_vtt}")
    return out_vtt


def _format_ts(t: float) -> str:
    t = max(float(t), 0.0)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:06.3f}"


def download_trailer(query: str, out_dir: Path = TMP) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    query_enc = requests.utils.quote(query) if requests else query
    url = f"https://www.youtube.com/results?search_query={query_enc}"
    print(f"[trailer] search query: {query}")
    print(f"[trailer] TODO: replace this stub with yt-dlp download from an official gameplay trailer URL.")
    print(f"[trailer] for now, copy a local trailer into: {TMP / 'trailer.mp4'}")
    return TMP / "trailer.mp4"


def split_random_clips(source: Path, out_dir: Path = CLIPS_DIR, clip_duration: float = 6.0, max_clips: int = 10) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for child in out_dir.glob("clip_*.mp4"):
        child.unlink()
    probe_cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration", "-of", "default=noprint_wrappers=1",
        str(source),
    ]
    probe = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    lines = [line.strip() for line in probe.stdout.splitlines() if "=" in line]
    meta = dict(line.split("=", 1) for line in lines)
    width = int(meta.get("width", "1080"))
    height = int(meta.get("height", "1920"))
    duration = float(meta.get("duration", "0"))
    if duration <= 0:
        raise RuntimeError(f"Invalid source duration: {duration}")
    clips: List[Path] = []
    order = list(range(int(duration // clip_duration)))
    random.shuffle(order)
    for idx, clip_idx in enumerate(order[:max_clips]):
        start = clip_idx * clip_duration
        path = out_dir / f"clip_{idx:03d}.mp4"
        cmd = [
            "ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", str(source),
            "-t", f"{clip_duration:.3f}",
            "-vf", f"scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-an", str(path),
        ]
        subprocess.run(cmd, check=True)
        clips.append(path)
    print(f"[clips] created {len(clips)} randomized clips")
    return clips


def build_concat_filter(clips: List[Path]) -> str:
    inputs = " ".join([f"-i {c}" for c in clips])
    filter_parts = []
    for i in range(len(clips)):
        filter_parts.append(f"[{i}:v]format=yuv420p,setsar=1[v{i}]")
    concat_inputs = "".join([f"[v{i}]" for i in range(len(clips))])
    filter_parts.append(f"{concat_inputs}concat=n={len(clips)}:v=1:a=0[outv]")
    return inputs, ";".join(filter_parts)


def splice_clips_vertical(clips: List[Path], out_path: Path = TMP / "spliced_raw.mp4") -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    inputs, filter_str = build_concat_filter(clips)
    cmd = ["ffmpeg", "-y"]
    for c in clips:
        cmd += ["-i", str(c)]
    cmd += [
        "-filter_complex", filter_str,
        "-map", "[outv]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-an", str(out_path),
    ]
    subprocess.run(cmd, check=True)
    print(f"[splice] wrote {out_path}")
    return out_path


def build_ass_from_vtt(vtt_path: Path, ass_path: Path = CAPTIONS_ASS) -> Path:
    text = vtt_path.read_text(encoding="utf-8")
    cues = re.findall(r"(\d+:\d+:\d+[.,]\d+)\s*-->\s*(\d+:\d+:\d+[.,]\d+)\s*\n(.*?)(?=\n\n|\Z)", text, re.DOTALL)
    ass = """\\
[Script Info]
Title: captions
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Burbank Big Condensed Bold,64,&HFFFFFF,&HFFFFFF,&H000000,&H000000,1,0,0,0,100,100,0,0,1,3,1,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text

"""
    events = []
    for start, end, content in cues:
        line = content.replace("\n", " ").strip()
        if not line:
            continue
        start_n = start.replace(",", ".")
        end_n = end.replace(",", ".")
        events.append(f"Dialogue: 0,{start_n},{end_n},Default,,,,,{line}")
    ass += "\n".join(events) + "\n"
    ass_path.parent.mkdir(parents=True, exist_ok=True)
    ass_path.write_text(ass, encoding="utf-8")
    print(f"[ass] wrote {ass_path} with {len(events)} cues")
    return ass_path


def render_final(spliced: Path, audio: Path, ass: Path, out_path: Path = FINAL_PATH) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    staging = TMP / "staging_h264.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(spliced),
        "-vf", f"ass='{ass}':fontsdir='{FONTS_DIR}'",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(staging),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(staging), "-i", str(audio),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-map", "0:v:0", "-map", "1:a:0", str(out_path),
    ], check=True)
    print(f"[render] wrote {out_path}")
    return out_path


def copy_to_upload(final: Path = FINAL_PATH, topic: Optional[str] = None) -> Optional[Path]:
    dest_name = topic if topic else final.name
    dest = TO_UPLOAD / dest_name
    try:
        import shutil
        shutil.copy2(final, dest)
        print(f"[upload] copied to {dest}")
        return dest
    except Exception as exc:
        print(f"[upload] copy failed: {exc}")
        return None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MashButtonGaming pipeline")
    p.add_argument("--script-only", action="store_true", help="Only generate script")
    p.add_argument("--no-splice", action="store_true", help="Skip trailer download/splice")
    return p.parse_args()


def run_pipeline() -> Path:
    print("[pipeline] start")
    items = fetch_gaming_news()
    topic = pick_topic(items)
    print(f"[pipeline] topic: {topic.title}")

    write_script(topic)
    synthesize_voiceover()
    transcribe_voiceover()
    build_ass_from_vtt(CAPTIONS_VTT, CAPTIONS_ASS)

    if not (TMP / "trailer.mp4").exists():
        download_trailer(topic.title)

    clips = split_random_clips(TMP / "trailer.mp4")
    spliced = splice_clips_vertical(clips)
    final = render_final(spliced, VOICEOVER_PATH, CAPTIONS_ASS)
    copy_to_upload(final, topic=topic.title + ".mp4")
    print("[pipeline] done")
    return final


if __name__ == "__main__":
    run_pipeline()