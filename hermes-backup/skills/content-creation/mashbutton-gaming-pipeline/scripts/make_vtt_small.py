from pathlib import Path
from faster_whisper import WhisperModel

ROOT = Path(r'C:/Users/qthas/Videos/Youtube Projects/MashButtonGaming')
audio = ROOT / 'output/audio/voiceover.mp3'
vtt = ROOT / 'output/captions/captions.vtt'

model = WhisperModel('small', device='cpu', compute_type='int8')
segments, _ = model.transcribe(str(audio), language='en', word_timestamps=True, beam_size=5, vad_filter=True)

words = []
for seg in segments:
    if seg.words:
        for w in seg.words:
            word = w.word.strip()
            if word:
                words.append((word, float(w.start), float(w.end)))

max_letters = 10
lines = []
current_words = []
current_start = None
current_end = None

for raw, start, end in words:
    if current_start is None:
        current_start = start
        current_end = end
        current_words.append(raw)
        continue
    new_text = ' '.join(current_words + [raw])
    if current_words and sum(1 for ch in new_text if ch.isalpha()) >= max_letters:
        lines.append((current_start, current_end, ' '.join(current_words)))
        current_words = [raw]
        current_start = start
        current_end = end
    else:
        current_words.append(raw)
        current_end = max(current_end, end)

if current_words:
    lines.append((current_start, current_end, ' '.join(current_words)))

def fmt(t):
    t = max(0.0, float(t))
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:06.3f}"

vtt_lines = ["WEBVTT\n", "\n"]
for i, (s, e, text) in enumerate(lines, start=1):
    text = ' '.join(text.split())
    vtt_lines.append(f"{i}\n")
    vtt_lines.append(f"{fmt(s)} --> {fmt(e)}\n")
    vtt_lines.append(f"{text}\n\n")

vtt.write_text(''.join(vtt_lines), encoding='utf-8')
print('written cues:', len(lines))
for line in lines:
    text = line[2]
    clipped = text if len(text) <= 22 else text[:20] + '..'
    print(f"{fmt(line[0])} -> {fmt(line[1])} | {clipped}")
