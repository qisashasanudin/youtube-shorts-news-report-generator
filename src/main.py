from __future__ import annotations

import argparse
import sys
from pathlib import Path

from config import DEFAULT_FONT_DIR, FFPROBE, SRC_VIDEOS, TO_UPLOAD
from download import download_trailer
from edit import build_segmented_edit
from render import render_final
from subtitles import generate_ass
from utils import now_stamp, run, slugify
from voice import generate_voiceover


def _check_subtitle_words(text: str) -> None:
    count = len(text.split())
    if not (50 <= count <= 150):
        raise ValueError(f"[ERROR] --subtitle must be 50-150 words; got {count} words.")


def _sanitize_subtitle(text: str) -> str:
    text = text.replace("-", " ").replace("—", ", ")
    return " ".join(text.split())


def _build_work_dir(title: str) -> Path:
    return SRC_VIDEOS / f"{now_stamp('%Y-%m-%d')}-{slugify(title)}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--youtube", required=True, help="Trailer YouTube URL")
    ap.add_argument("--title", required=True, help="Exact title / filename stem")
    ap.add_argument("--subtitle", required=True, help="TTS/subtitle text (50-150 words)")
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

    work = _build_work_dir(args.title)
    print(f"[INFO] project={work}")
    print(f"[INFO] title={args.title}")
    print(f"[INFO] subtitle word count: {len(args.subtitle.split())}")

    trailer_path = work / "clips" / "trailer_full.mp4"
    voice_path = work / "audio" / "voiceover.mp3"
    reordered_path = work / "clips" / "reordered.mp4"
    ass_path = work / "captions" / "captions.ass"
    final_path = TO_UPLOAD / f"{slugify(args.title)}.mp4"

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

    if not final_path.exists():
        sys.exit(f"[ERROR] missing output: {final_path}")
    size = final_path.stat().st_size
    dur_res = run([
        str(FFPROBE),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(final_path),
    ], capture_output=True, text=True)
    if dur_res.returncode != 0:
        sys.exit(f"[ERROR] probe output duration failed: {dur_res.stderr.strip()}")
    dur = dur_res.stdout.strip()
    print(f"[OK] verify size={size:,} bytes  duration={dur}s  path={final_path}")


if __name__ == "__main__":
    main()
