import os
import random
import subprocess
from pathlib import Path

ROOT = Path(r'C:/Users/qthas/Videos/Youtube Projects/MashButtonGaming/videos/marvels-wolverine-sop-june2026')
audio = ROOT / 'audio/voiceover.mp3'
master = ROOT / 'clips/trailer_full.mp4'
clips_dir = ROOT / 'clips/ordered_segments'
reordered = ROOT / 'clips/reordered.mp4'

random.seed(12345)

# Detected actual voiceover duration for this project
audio_dur = 36.816

dur_probe = subprocess.run(
    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(master)],
    capture_output=True, text=True, check=True
)
master_dur = float(dur_probe.stdout.strip())
print(f'master duration: {master_dur:.3f}s')

segment_duration = 4.0
segments = []
start = 0.0
idx = 0
while start + segment_duration <= master_dur:
    segments.append((idx, float(start), float(start + segment_duration)))
    start += segment_duration
    idx += 1
print(f'segments: {len(segments)}')

if not segments:
    raise RuntimeError('No segments generated from master clip')

chosen = random.sample(segments, k=min(len(segments), max(1, int(audio_dur / segment_duration) + 2)))
print(f'chosen segments: {len(chosen)}')

clips_dir.mkdir(parents=True, exist_ok=True)
segment_files = []
for i, (idx, seg_start, seg_end) in enumerate(chosen):
    out = clips_dir / f'seg_{i:03d}.mp4'
    subprocess.run([
        'ffmpeg', '-y', '-ss', f'{seg_start:.3f}', '-t', f'{segment_duration:.3f}', '-i', str(master),
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
        '-an', str(out)
    ], check=True, capture_output=True, text=True)
    segment_files.append(out)
    print(f'wrote segment: {out}')

# Build concat input for ffmpeg to avoid path quoting issues
concat_path = ROOT / 'clips/concat_segments.txt'
concat_path.write_text('\n'.join(f"file '{p.absolute()}'" for p in segment_files), encoding='utf-8')

subprocess.run([
    'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_path),
    '-c', 'copy', str(reordered)
], check=True, capture_output=True, text=True)
print(f'reordered: {reordered} ({reordered.stat().st_size} bytes)')
