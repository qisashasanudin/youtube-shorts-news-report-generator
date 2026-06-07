from __future__ import annotations

from pathlib import Path
from faster_whisper import WhisperModel


def _normalize_word(word: str) -> str:
    return "".join(ch.lower() for ch in word if ch.isalnum())


def _align_words_to_text(words, text: str):
    if not words or not text:
        return None
    text_words = text.split()
    aligned = []
    cursor = 0
    for tw in text_words:
        norm = _normalize_word(tw)
        while cursor < len(words) and _normalize_word(words[cursor].get("word", "")) != norm:
            cursor += 1
        if cursor >= len(words):
            break
        aligned.append(words[cursor])
        cursor += 1
    return aligned if len(aligned) == len(text_words) else None


def _whisper_word_timestamps(path: Path):
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(path), language="en", word_timestamps=True)

    mapped = []
    for seg in segments:
        if not seg.words:
            continue
        for w in seg.words:
            word = w.word.strip()
            if not word:
                continue
            start = max(w.start, 0.0)
            end = max(w.end, start)
            mapped.append({"word": word, "start": start, "end": end})
    return mapped


def _ts(t: float) -> str:
    t = max(0.0, float(t))
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"


def main() -> None:
    work = Path("videos/2026-06-07-09-42-56_call-of-duty-2026-content-roadmap-revealed")
    voiceover = work / "audio/voiceover.mp3"
    ass_path = work / "captions/captions.ass"
    text = Path("src/last_subtitle.txt").read_text(encoding="utf-8") if Path("src/last_subtitle.txt").exists() else "Call of Duty fans have a massive 2026 to look forward to with the newly revealed content roadmap showing Modern Warfare 4 as the headline release alongside fresh Warzone updates and surprise returning favorites. Activision is teasing the next evolution of modern combat with a first official look around more support for existing games and bolder experiments this time around. Whether you are a multiplayer diehard or campaign fan this roadmap suggests Call of Duty is pushing harder than ever to deliver variety and long term engagement across every mode Stack those reveals together and 2026 is shaping up to be one of the most packed years in franchise history"

    words = text.split()
    per_word = 30.98 / max(1, len(words))
    word_dur = per_word * 0.95

    mapped = _whisper_word_timestamps(voiceover)
    aligned = _align_words_to_text(mapped, text)
    timings = []
    if aligned:
        for i, w in enumerate(aligned):
            if i >= len(words):
                break
            s = max(w["start"], 0.0)
            e = max(w["end"], s + 0.1)
            if i + 1 < len(aligned):
                nxt = aligned[i + 1]["start"]
                if nxt > s:
                    e = min(e, nxt - 0.05)
            timings.append((s, max(e, s + 0.05)))

    if len(timings) != len(words):
        timings = []
        for i in range(len(words)):
            s = max(0.0, i * per_word)
            e = s + word_dur
            timings.append((s, e))

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
        if i < len(timings):
            s, e = timings[i]
        else:
            s = max(0.0, i * per_word)
            e = s + word_dur
        lines.append(f"Dialogue: 0,{_ts(s)},{_ts(e)},Default,,,,,,{\an5}}{w.upper()}\r\n")

    ass_path.parent.mkdir(parents=True, exist_ok=True)
    ass_path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    used = "whisper" if any(abs((s - e) - word_dur) > 0.01 for s, e in timings[:5]) else "fallback"
    print(f"[OK] ASS: {ass_path}  words={len(words)}  timing={used}")


if __name__ == "__main__":
    main()
