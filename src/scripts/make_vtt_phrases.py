from faster_whisper import WhisperModel
from pathlib import Path

audio = Path(r'C:/Users/qthas/Videos/Youtube Projects/MashButtonGaming/output/audio/voiceover.mp3')
out_vtt = Path(r'C:/Users/qthas/Videos/Youtube Projects/MashButtonGaming/output/captions/captions.vtt')

model = WhisperModel('small', device='cpu', compute_type='int8')

segments, info = model.transcribe(
    str(audio),
    language='en',
    word_timestamps=True,
    beam_size=5,
    vad_filter=True,
)

words = []
for seg in segments:
    if seg.words:
        for w in seg.words:
            words.append({
                'word': w.word.strip(),
                'start': w.start,
                'end': w.end,
            })

lines = []
current = []
for item in words:
    word = item['word']
    if not word:
        continue
    letters = sum(len(w) for w in current) + len(word)
    if current and letters >= 10:
        lines.append(current)
        current = []
    current.append(item)
if current:
    lines.append(current)

def fmt(t):
    t = max(0.0, float(t))
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:06.3f}"

lines_out = ["WEBVTT\n", "\n"]
for idx, line in enumerate(lines, start=1):
    start = fmt(line[0]['start'])
    end = fmt(line[-1]['end'])
    text = " ".join(w['word'] for w in line)
    lines_out.append(f"{idx}\n")
    lines_out.append(f"{start} --> {end}\n")
    lines_out.append(f"{text}\n\n")

Path(out_vtt).write_text("".join(lines_out), encoding='utf-8')
print('rewrote word/phrase VTT with len<10 rule')
print('lines:', len(lines))
for line in lines:
    text = " ".join(w['word'] for w in line)
    if len(text) > 15:
        text = text[:15] + "..."
    print('-', text)
