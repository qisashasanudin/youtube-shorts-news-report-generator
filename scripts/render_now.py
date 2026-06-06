import random
import subprocess
from pathlib import Path
import re

ROOT = Path(r'C:/Users/qthas/Videos/Youtube Projects/MashButtonGaming')
OUT = ROOT / 'output'
TMP = ROOT / 'output_tmp'
RENDER = ROOT / 'render'
TO_UPLOAD = ROOT / 'TO_UPLOAD'
FONTS_DIR = ROOT / 'fonts'
FONT_FILE = FONTS_DIR / 'burbank_big_condensed.otf'
ASS_PATH = OUT / 'captions' / 'captions.ass'
FINAL_PATH = RENDER / 'final.mp4'
VOICEOVER = OUT / 'audio' / 'voiceover.mp3'
CLIPS_DIR = OUT / 'clips'
TRAILER = TMP / 'trailer.mp4'

def to_seconds(t):
    h, m, s = t.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

def fmt_ts(t):
    t = max(float(t), 0.0)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f'{h}:{m:02d}:{s:06.3f}'

text = (OUT / 'captions' / 'captions.vtt').read_text(encoding='utf-8')
cues = re.findall(r"(\d+:\d+:\d+[.,]\d+)\s*-->\s*(\d+:\d+:\d+[.,]\d+)\s*\n(.*?)(?=\n\n|\Z)", text, re.DOTALL)
words = []
for start, end, content in cues:
    line = content.replace('\n', ' ').strip()
    if not line:
        continue
    words.append((start.replace(',', '.'), end.replace(',', '.'), line))

phrases = []
current = None
for start, end, text_line in words:
    s = to_seconds(start)
    e = to_seconds(end)
    if current is None:
        current = [start, end, text_line]
        continue
    prev_start, prev_end, prev_text = current
    prev_end_s = to_seconds(prev_end)
    merged = f"{prev_text} {text_line}"
    if (s - prev_end_s) > 0.28 or len(merged) > 90 or len(prev_text.split()) >= 5:
        phrases.append((prev_start, prev_end, prev_text))
        current = [start, end, text_line]
    else:
        current[1] = fmt_ts(e)
        current[2] = merged
if current is not None:
    phrases.append(tuple(current))
print(f'merged {len(phrases)} phrase cues')

ass = """\
[Script Info]
Title: captions
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Burbank Big Condensed Bold,64,&HFFFFFF,&HFFFFFF,&H000000,&H000000,1,0,0,0,100,100,0,0,1,3,1,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text

"""
events = []
for start, end, line in phrases:
    ass += f"Dialogue: 0,{start},{end},Default,,,,,{line}\n"
    events.append((start, end, line))
ASS_PATH.write_text(ass, encoding='utf-8')
print(f'wrote {ASS_PATH} with {len(events)} cues')

# Split trailer into randomized 6s vertical clips
CLIPS_DIR.mkdir(parents=True, exist_ok=True)
for child in CLIPS_DIR.glob('clip_*.mp4'):
    child.unlink()
probe = subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,duration','-of','default=noprint_wrappers=1', str(TRAILER)], capture_output=True, text=True, check=True)
meta = dict(line.split('=',1) for line in probe.stdout.splitlines() if '=' in line)
width = int(meta.get('width','1920'))
height = int(meta.get('height','1080'))
duration = float(meta.get('duration','0'))
clip_duration = 6.0
max_clips = 20
order = list(range(int(duration // clip_duration)))
random.shuffle(order)
clip_paths = []
for idx, clip_idx in enumerate(order[:max_clips]):
    start = clip_idx * clip_duration
    out = CLIPS_DIR / f'clip_{idx:03d}.mp4'
    subprocess.run([
        'ffmpeg','-y','-ss',f'{start:.3f}','-i',str(TRAILER),'-t',f'{clip_duration:.3f}',
        '-vf',"scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1",
        '-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-an',str(out)
    ], check=True)
    clip_paths.append(out)
print(f'created {len(clip_paths)} clips')

# Build concat filter
inputs = ' '.join([f'-i {c}' for c in clip_paths])
filter_parts = []
for i in range(len(clip_paths)):
    filter_parts.append(f'[{i}:v]format=yuv420p,setsar=1[v{i}]')
concat_inputs = ''.join([f'[v{i}]' for i in range(len(clip_paths))])
filter_parts.append(f'{concat_inputs}concat=n={len(clip_paths)}:v=1:a=0[outv]')
filter_str = ';'.join(filter_parts)
spliced = TMP / 'spliced_raw.mp4'
subprocess.run(['ffmpeg','-y'] + [item for c in clip_paths for item in ('-i', str(c))] + ['-filter_complex', filter_str, '-map', '[outv]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-an', str(spliced)], check=True)
print(f'spliced -> {spliced}')

# Trim spliced to voiceover duration
vo_dur = 37.536000
spliced_trim = TMP / 'spliced_trim.mp4'
subprocess.run(['ffmpeg','-y','-i',str(spliced),'-t',f'{vo_dur:.3f}','-c','copy',str(spliced_trim)], check=True)
print(f'trimmed spliced to {vo_dur}s')

# Burn ASS and mux audio
staging = TMP / 'staging.mp4'
subprocess.run([
    'ffmpeg','-y','-i',str(spliced_trim),
    '-vf', f"ass='{ASS_PATH}':fontsdir='{FONTS_DIR}'",
    '-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','-an', str(staging)
], check=True)
subprocess.run([
    'ffmpeg','-y','-i',str(staging),'-i',str(VOICEOVER),
    '-c:v','copy','-c:a','aac','-b:a','128k','-shortest','-map','0:v:0','-map','1:a:0', str(FINAL_PATH)
], check=True)
print(f'rendered {FINAL_PATH}')

# Copy to TO UPLOAD with safe filename
safe_title = 'FF7_Revelation_Summer_Game_Fest_2026_#rpg #finalfantasy7.mp4'
dest = TO_UPLOAD / safe_title
import shutil
shutil.copy2(FINAL_PATH, dest)
print(f'copied to {dest}')
