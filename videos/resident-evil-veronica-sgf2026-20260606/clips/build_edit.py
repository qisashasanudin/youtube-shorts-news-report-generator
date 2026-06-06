import os, random, subprocess
from pathlib import Path

ROOT = Path(r'C:/Users/qthas/Videos/Youtube Projects/MashButtonGaming/videos/resident-evil-veronica-sgf2026-20260606')
audio = ROOT / 'audio/voiceover.mp3'
master = ROOT / 'clips/trailer_full.mp4'
clips_dir = ROOT / 'clips/ordered_segments'
reordered = ROOT / 'clips/reordered.mp4'
render_out = ROOT / 'render/final.mp4'

random.seed(42)

# Get audio duration
probe_audio = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1', str(audio)], capture_output=True, text=True, check=True)
audio_dur = float(probe_audio.stdout.strip())
print('audio_dur', audio_dur)

# Get master duration
probe_vid = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1', str(master)], capture_output=True, text=True, check=True)
master_dur = float(probe_vid.stdout.strip())
print('master_dur', master_dur)

# Create segments list
seg_len = 3.0
segments = []
t = 0.0
idx = 0
while t + seg_len <= master_dur:
    segments.append((idx, t, t + seg_len))
    t += seg_len
    idx += 1
print('segments', len(segments))

# Choose enough segments to cover audio duration, then shuffle
needed = max(1, int(audio_dur / seg_len) + 1)
chosen = random.sample(segments, k=min(needed, len(segments)))
print('chosen', len(chosen))

clips_dir.mkdir(exist_ok=True)
segment_files = []
for i, (idx, start, end) in enumerate(chosen):
    out = clips_dir / f'seg_{i:03d}.mp4'
    subprocess.run([
        'ffmpeg', '-y', '-ss', str(start), '-to', str(end), '-i', str(master),
        '-c:v', 'libx264', '-c:a', 'aac', str(out)
    ], check=True, capture_output=True, text=True)
    segment_files.append(out)
    print('wrote', out, 'size', out.stat().st_size)

# Build concat list
concat = ROOT / 'clips/concat.txt'
concat.write_text('\n'.join([f"file '{p.absolute()}'" for p in segment_files]), encoding='utf-8')

# Concatenate
subprocess.run([
    'ffmpeg','-y','-f','concat','-safe','0','-i', str(concat),
    '-c','copy', str(reordered)
], check=True, capture_output=True, text=True)
print('reordered', reordered, 'size', reordered.stat().st_size)

# Prepare for render: use actual subtitle file if exists, else skip
ass = ROOT / 'captions/captions.ass'
sub_filter = f"subtitles='{ass.absolute().replace(chr(39), chr(39))}'"
print('ready')
