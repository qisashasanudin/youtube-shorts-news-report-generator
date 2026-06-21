from __future__ import annotations

from pathlib import Path

from config import DEFAULT_FONT_DIR, FFMPEG, REPO
from utils import run


def _render_burn_subs(
    work: Path,
    reordered: Path,
    audio: Path,
    ass: Path,
    font_dir: Path | None,
    out: Path,
) -> None:
    font_dir = font_dir or DEFAULT_FONT_DIR
    vm = reordered.resolve().relative_to(REPO).as_posix()
    am = audio.resolve().relative_to(REPO).as_posix()
    ass_path = ass.resolve().relative_to(REPO).as_posix()
    font_path = font_dir.resolve().relative_to(REPO).as_posix()
    out_path = out.resolve().relative_to(REPO).as_posix()

    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(FFMPEG),
        "-y",
        "-i",
        vm,
        "-i",
        am,
        "-vf",
        f"scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,ass=filename={ass_path}:fontsdir={font_path}",
        "-map",
        "0:v",
        "-map",
        "1:a",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-pix_fmt",
        "yuv420p",
        out_path,
    ]
    print("[RUN] ffmpeg subtitle burn ...")
    res = run(cmd, cwd=REPO)
    print("[RUN] ffmpeg subtitle burn ->", res.returncode)
    if res.returncode != 0:
        raise RuntimeError(f"[ERROR] subtitle burn render failed for {out}")


def render_final(
    work: Path,
    reordered: Path,
    audio: Path,
    ass: Path,
    font_dir: Path | None,
    out: Path,
) -> None:
    _render_burn_subs(work, reordered, audio, ass, font_dir, out)
