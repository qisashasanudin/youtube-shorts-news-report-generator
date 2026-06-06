from faster_whisper import WhisperModel
from pathlib import Path

audio = Path(r'C:/Users/qthas/Videos/Youtube Projects/MashButtonGaming/output/audio/voiceover.mp3')
out_vtt = Path(r'C:/Users/qthas/Videos/Youtube Projects/MashButtonGaming/output/captions/captions.vtt')

model = WhisperModel('small', device='cpu', compute_type='int8')
segments, _ = model.transcribe(str(audio), language='en', word_timestamps=True)

with out_vtt.open('w', encoding='utf-8') as f:
    f.write('WEBVTT\n\n')
    for seg in segments:
        if not seg.words:
            continue
        for w in seg.words:
            def fmt_ts(t):
                t = max(float(t), 0.0)
                h = int(t // 3600)
                m = int((t % 3600) // 60)
                s = t % 60
                return f'{h}:{m:02d}:{s:06.3f}'
            f.write(f"{fmt_ts(w.start)} --> {fmt_ts(w.end)}\n{w.word.strip()}\n\n")
print('wrote', out_vtt)
