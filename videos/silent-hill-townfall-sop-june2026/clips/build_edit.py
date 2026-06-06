import os
import random
import subprocess
from pathlib import Path

ROOT = Path(r'C:/Users/qthas/Videos/Youtube Projects/MashButtonGaming/videos/silent-hill-townfall-sop-june2026')
clips_dir = ROOT / 'clips'
out_dir = ROOT / 'clips'
out_dir.mkdir(parents=True, exist_ok=True)

src = clips_dir / 'trailer_full.mp4'
reordered = out_dir / 'reordered.mp4'

min_seg = 5.0
max_seg = 5.0
target = 30.0

segments = []
remaining = target
while remaining > 0:
    seg = min(min_seg + random.random() * (max_seg - min_seg), remaining)
    segments.append(seg)
    remaining -= seg

parts = []
used = 0.0
video_dur = float(subprocess.check_output([
    'ffprobe','-v','error',
    '-show_entries','format=duration',
    '-of','default=noprint_wrappers=1:nokey=1', str(src)
]).decode().strip() or '0')

for i, seg in enumerate(segments):
    max_start = max(0.0, video_dur - seg)
    if max_start <= 0:
        ss = 0.0
    else:
        ss = random.uniform(0, max_start)
    p = out_dir / f'part_{i:03d}.mp4'
    subprocess.run([
        'ffmpeg', '-y', '-ss', f'{ss:.3f}', '-t', f'{seg:.3f}',
        '-i', str(src),
        '-c', 'copy', str(p)
    ], check=True)
    parts.append(p)

filelist = out_dir / 'filelist.txt'
with filelist.open('w', encoding='utf-8') as f:
    for p in parts:
        f.write(f"file '{p.as_posix()}'\n")

subprocess.run([
    'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
    '-i', str(filelist),
    '-c', 'copy', str(reordered)
], check=True)

print('reordered:', reordered)
print('segments:', len(segments), 'duration:', sum(segments))
