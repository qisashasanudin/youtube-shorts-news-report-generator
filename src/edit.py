from __future__ import annotations

import random
from pathlib import Path

from config import FFMPEG
from utils import probe_duration, run


def build_segmented_edit(
    source: Path,
    clips_dir: Path,
    reordered: Path,
    duration: float,
    shuffle: bool = True,
) -> None:
    clips_dir.mkdir(parents=True, exist_ok=True)
    random.seed(int(Path().resolve().stat().st_mtime * 1000) % 2**32)

    clip_secs = 5.0
    source_dur = probe_duration(source)
    max_clips = max(1, int(source_dur // clip_secs))
    needed = max(1, int((duration + clip_secs - 0.1) // clip_secs))
    if needed > max_clips:
        needed = max_clips

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
        selected = raw_parts.copy()
        random.shuffle(selected)
    else:
        selected = raw_parts
    selected = selected[:needed]

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
