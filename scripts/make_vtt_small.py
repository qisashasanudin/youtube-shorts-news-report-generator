import sys
from pathlib import Path
from faster_whisper import WhisperModel

ROOT = Path(r'C:/Users/qthas/Videos/Youtube Projects/MashButtonGaming')
audio = Path(sys.argv[1]) if len(sys.argv) >= 2 else ROOT / 'videos/final-fantasy-vii-rebirth-switch2/audio/voiceover.mp3'
vtt = Path(sys.argv[2]) if len(sys.argv) >= 3 else ROOT / 'videos/final-fantasy-vii-rebirth-switch2/captions/captions.vtt'

model = WhisperModel('small', device='cpu', compute_type='int8')
segments, _ = model.transcribe(str(audio), language='en', word_timestamps=True, beam_size=5, vad_filter=True)

words = []
for seg in segments:
    if seg.words:
        for w in seg.words:
            word = w.word.strip()
            if word:
                words.append((word, float(w.start), float(w.end)))

if not words:
    print('no words')
    raise SystemExit(0)

def fmt(t):
    t = max(0.0, float(t))
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:06.3f}"

lines = []
for i, (word, start, end) in enumerate(words):
    s = fmt(start)
    e = fmt(end)
    lines.append(f"{i+1}\n{s} --> {e}\n{word}\n")

out = "WEBVTT\n\n" + "\n".join(lines)
vtt.write_text(out, encoding='utf-8')
print('written cues:', len(lines))
preview = "\n".join(lines[:20])
print(preview)