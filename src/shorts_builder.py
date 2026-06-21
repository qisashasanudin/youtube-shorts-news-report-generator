#!/usr/bin/env python3
"""One-shot YouTube Shorts builder.
Usage:
    .venv\\Scripts\\python.exe src/shorts_builder.py --youtube "<url>" --title "<TITLE>" --subtitle "<TEXT>"
"""
from __future__ import annotations

import argparse
import asyncio
import os
import random
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from yt_dlp import YoutubeDL

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
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    ).decode().strip()
    return float(out)


def _slugify(text: str) -> str:
    text = text.strip().upper()
    text = "".join(c for c in text if c.isalnum() or c in " _#")
    text = text.replace(" ", "_")
    text = "_".join(part for part in text.split("_") if part)
    return text[:80]


def _now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")


def _build_work_dir(title: str) -> Path:
    return SRC_VIDEOS / f"{_now_stamp()}_{_slugify(title)}"


def download_trailer(url: str, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    outtmpl = str(dest)
    attempts = [
        {"format": "bestvideo[ext=mp4][height<=1080][height>=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080][height>=720]/best[ext=mp4][height<=1080]/best[ext=mp4]/best"},
        {
            "format": "bestvideo[ext=mp4][height<=1080][height>=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080][height>=720]/best[ext=mp4][height<=1080]/best[ext=mp4]/best",
            "extractor_args": {"youtube": {"player_client": ["web"]}},
        },
        {
            "format": "bestvideo[ext=mp4][height<=1080][height>=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080][height>=720]/best[ext=mp4][height<=1080]/best[ext=mp4]/best",
            "extractor_args": {"youtube": {"player_client": ["android"]}},
        },
        {"format": "299+140/best[filesize<100M]/best"},
    ]
    for attempt in attempts:
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
    raise last_error


class MediaExtractionError(RuntimeError):
    pass


def _build_ytdlp_http_headers(url: str, user_agent: str) -> dict:
    return {
        "User-Agent": user_agent,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": url,
        "Origin": "https://www.youtube.com",
    }


def generate_voiceover(text: str, out: Path) -> float:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    count = len(text.split())
    if not (50 <= count <= 150):
        raise ValueError(
            f"[ERROR] --subtitle must be 50-100 words; got {count} words."
        )
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    url = "https://www.youtube.com/watch?v=3x_p_jw0j2U"
    headers = _build_ytdlp_http_headers(url, user_agent)
    piper = shutil.which("piper")
    if piper is None:
        piper = REPO / "apps/piper/piper.exe"
    if piper and Path(piper).exists():
        voice = os.environ.get("PIPER_VOICE", "en_US-lessac-medium")
        cmd = [
            str(piper),
            "-m", voice,
            "-f", str(out),
            "--cuda",
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate(input=text.encode("utf-8"))
        if proc.returncode != 0:
            raise MediaExtractionError(stderr.decode("utf-8", "ignore"))
        return probe_duration(out)
    edge_tts = shutil.which("edge-tts")
    if edge_tts is not None and Path(edge_tts).exists():
        cmd = [
            str(edge_tts),
            "--voice", "en-US-BrianMultilingualNeural",
            "--rate", "+25%",
            "--text", text,
            "--write-media", str(out),
        ]
        res = run(cmd)
        if res.returncode != 0:
            raise MediaExtractionError("edge-tts CLI failed")
        return probe_duration(out)

    try:
        import edge_tts as edge_tts_module

        async def _synthesize() -> None:
            communicate = edge_tts_module.Communicate(
                text,
                "en-US-BrianMultilingualNeural",
                rate="+25%",
            )
            await communicate.save(str(out))

        asyncio.run(_synthesize())
        return probe_duration(out)
    except Exception as exc:  # pragma: no cover
        raise MediaExtractionError(f"edge-tts synthesis failed: {exc}")


def _find_downloaded_file(out_dir: Path) -> Path:
    for candidate in sorted(out_dir.iterdir()):
        if candidate.is_file() and candidate.suffix.lower() == ".mp4":
            return candidate
    raise MediaExtractionError(f"Downloaded MP4 not found in {out_dir}")


def _yt_dlp_meta(url: str) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "retries": 1,
        "socket_timeout": 15,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info or {}


def build_segmented_edit(
    source: Path,
    clips_dir: Path,
    reordered: Path,
    duration: float,
    shuffle: bool = True,
) -> None:
    clips_dir.mkdir(parents=True, exist_ok=True)
    random.seed(int(datetime.now().timestamp() * 1000) % 2**32)

    clip_secs = 5.0
    source_dur = probe_duration(source)
    max_clips = max(1, int(source_dur // clip_secs))
    needed = max(1, int((duration + clip_secs - 0.1) // clip_secs))
    if needed > max_clips:
        needed = max_clips

    # Use the full trailer chunk pool, then pick the minimum needed segments.
    raw_parts: list[Path] = []
    for i in range(max_clips):
        ss = i * clip_secs
        part = clips_dir / f"part_{i:03d}.mp4"
        seg_dur = clip_secs if i < max_clips - 1 else max(0.5, source_dur - ss)
        run(
            [
                str(FFMPEG),
                "-y",
                "-ss",
                f"{ss:.3f}",
                "-t",
                f"{seg_dur:.3f}",
                "-i",
                str(source),
                "-c",
                "copy",
                "-an",
                str(part),
            ],
            check=True,
        )
        raw_parts.append(part)

    if shuffle:
        other_parts = raw_parts.copy()
        random.shuffle(other_parts)
        selected: list[Path] = other_parts[:needed]
    else:
        selected = raw_parts[:needed]

    # Step 3/4: build concat list, then merge.
    filelist = clips_dir / "filelist.txt"
    with filelist.open("w", encoding="utf-8") as f:
        for p in selected:
            f.write(f"file '{p.as_posix()}'\n")

    run(
        [
            str(FFMPEG),
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(filelist),
            "-c",
            "copy",
            "-an",
            str(reordered),
        ],
        check=True,
    )
    if probe_duration(reordered) > duration:
        trimmed = reordered.with_suffix(".trimmed.mp4")
        run(
            [
                str(FFMPEG),
                "-y",
                "-i",
                str(reordered),
                "-t",
                f"{duration:.3f}",
                "-c",
                "copy",
                str(trimmed),
            ],
            check=True,
        )
        trimmed.replace(reordered)


def _ts(t: float) -> str:
    t = max(0.0, float(t))
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"


def _word_end(mapped: list[dict], idx: int, audio_duration: float = None) -> tuple[float, float]:
    if idx + 1 < len(mapped):
        nxt = mapped[idx + 1]["start"]
        s = max(mapped[idx]["start"], 0.0)
        e = max(mapped[idx]["end"], s + 0.05)
        if nxt > s:
            e = min(e, nxt - 0.02)
        return s, max(e, s + 0.05)
    s = max(mapped[idx]["start"], 0.0)
    e = max(mapped[idx]["end"], s + 0.05)
    # Extend last word to audio duration if provided and Whisper ends early
    if audio_duration is not None and e < audio_duration:
        e = audio_duration
    return s, max(e, s + 0.05)


def generate_ass(
    text: str,
    audio_duration: float,
    ass_path: Path,
    *,
    voiceover: Path | None = None,
) -> None:
    words = text.split()
    per_word = audio_duration / max(1, len(words))
    word_dur = per_word * 0.95

    word_data: list[dict] = []
    used = "fallback"
    if voiceover and voiceover.exists() and audio_duration > 0:
        try:
            from faster_whisper import WhisperModel

            model = WhisperModel("small", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(
                str(voiceover), language="en", word_timestamps=True
            )
            for seg in segments:
                if not seg.words:
                    continue
                for w in seg.words:
                    word = w.word.strip()
                    # Whisper may emit leading dashes from tokenization like '-founder'.
                    word = word.lstrip("-").strip()
                    if not word:
                        continue
                    start = max(w.start, 0.0)
                    end = max(w.end, start)
                    word_data.append({"word": word, "start": start, "end": end})
            if word_data:
                used = "whisper"
                for i in range(len(word_data)):
                    s, e = _word_end(word_data, i, audio_duration)
                    word_data[i]["start"] = s
                    word_data[i]["end"] = e
        except Exception as exc:
            print(f"[WARN] faster_whisper timing unavailable: {exc}")
            word_data = []

    if not word_data:
        for i, word in enumerate(words):
            s = max(0.0, i * per_word)
            e = s + word_dur
            if i + 1 == len(words) and audio_duration is not None and e < audio_duration:
                e = audio_duration
            word_data.append({"word": word, "start": s, "end": e})

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
        "Style: Default,Whoosh,120,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,6,1.2,5,5,5,0,0,150",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    for item in word_data:
        s = item["start"]
        e = item["end"]
        text_line = item["word"].upper()
        lines.append(f"Dialogue: 0,{_ts(s)},{_ts(e)},Default,,,,,,{text_line}\r\n")

    ass_path.parent.mkdir(parents=True, exist_ok=True)
    ass_path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    print(f"[OK] ASS: {ass_path}  words={len(word_data)}  timing={used}")


def _relink(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink(missing_ok=True)
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
        str(FFPROBE), "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio),
    ]
    dur_res = run(dur_cmd, capture_output=True, text=True, cwd=work)
    if dur_res.returncode != 0:
        sys.exit(f"[ERROR] probe audio duration failed: {dur_res.stderr.strip()}")
    _ = dur_res.stdout.strip()

    font_dir = font_dir or DEFAULT_FONT_DIR
    vm = reordered.resolve().relative_to(REPO).as_posix()
    am = audio.resolve().relative_to(REPO).as_posix()
    ass_path = ass.resolve().relative_to(REPO).as_posix()
    font_path = font_dir.resolve().relative_to(REPO).as_posix()
    out_path = out.resolve().relative_to(REPO).as_posix()

    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(FFMPEG), "-y",
        "-i", vm,
        "-i", am,
        "-vf", f"scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,ass=filename={ass_path}:fontsdir={font_path}",
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        out_path,
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


def verify(path: Path) -> None:
    if not path.exists():
        sys.exit(f"[ERROR] missing: {path}")
    size = path.stat().st_size
    dur = probe_duration(path)
    print(f"[OK] verify size={size:,} bytes  duration={dur:.3f}s  path={path}")


def _check_subtitle_words(text: str) -> None:
    count = len(text.split())
    if not (50 <= count <= 150):
        raise ValueError(
            f"[ERROR] --subtitle must be 50-100 words; got {count} words."
        )


def _sanitize_subtitle(text: str) -> str:
    text = text.replace("-", " ").replace("—", ", ")
    return " ".join(text.split())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--youtube", required=True, help="Trailer YouTube URL")
    ap.add_argument("--title", required=True, help="Exact title / filename stem")
    ap.add_argument("--subtitle", required=True, help="TTS/subtitle text (100-200 words)")
    shuffle_group = ap.add_mutually_exclusive_group()
    shuffle_group.add_argument(
        "--shuffle",
        action="store_true",
        dest="shuffle",
        help="Enable random shuffling of trailer segments (default)",
    )
    shuffle_group.add_argument(
        "--no-shuffle",
        action="store_false",
        dest="shuffle",
        help="Disable random shuffling of trailer segments",
    )
    ap.set_defaults(shuffle=True)
    args = ap.parse_args()
    args.subtitle = _sanitize_subtitle(args.subtitle)
    _check_subtitle_words(args.subtitle)

    def _slugify(text: str) -> str:
        text = text.strip().upper()
        text = "".join(c for c in text if c.isalnum() or c in " _#")
        text = text.replace(" ", "_")
        text = "_".join(part for part in text.split("_") if part)
        return text[:80]

    def _now_stamp() -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def _build_work_dir(title: str) -> Path:
        return SRC_VIDEOS / f"{_now_stamp()}-{_slugify(title)}"

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

    build_segmented_edit(
        trailer_path,
        work / "clips",
        reordered_path,
        voice_dur,
        shuffle=args.shuffle,
    )
    print(f"[3/6] segmented edit ready  shuffle={args.shuffle}")

    generate_ass(args.subtitle, voice_dur, ass_path, voiceover=voice_path)
    print("[4/6] generating captions...")

    render_final(work, reordered_path, voice_path, ass_path, DEFAULT_FONT_DIR, final_path)
    print(f"[5/6] rendered final to {final_path}")

    verify(final_path)
    print("[DONE]")


if __name__ == "__main__":
    main()
