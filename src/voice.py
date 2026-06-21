from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from pathlib import Path

from config import REPO
from utils import probe_duration, run


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
        raise ValueError(f"[ERROR] --subtitle must be 50-100 words; got {count} words.")

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
            "-m",
            voice,
            "-f",
            str(out),
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
            "--voice",
            "en-US-BrianMultilingualNeural",
            "--rate",
            "+25%",
            "--text",
            text,
            "--write-media",
            str(out),
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
