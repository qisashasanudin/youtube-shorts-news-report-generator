from __future__ import annotations

from pathlib import Path

from utils import probe_duration


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
