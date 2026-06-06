
import os, sys, re, shutil, subprocess, json, math
from pathlib import Path
import random, tempfile

PROJECT = Path(r'C:/Users/qthas/Videos/Youtube Projects/MashButtonGaming')
ASSETS = PROJECT / 'assets'
OUT = PROJECT / 'output_tmp'
RENDER = OUT / 'renders'
FINAL_NAME_FILE = OUT / 'final_filename.txt'

OUT.mkdir(exist_ok=True), RENDER.mkdir(exist_ok=True, parents=True)

TITLE = (PROJECT / 'output/news/title.txt').read_text(encoding='utf-8').strip()
DUR = 34.67
PORTRAIT = '720x1280'
FONT = ASSETS / 'burbank_big_condensed.otf'
FALLBACK_FONT = ASSETS / 'arial.ttf'

def has_junk_tail(text):
    m = re.search(r'[A-Za-z]\s*[\\|/|]\s*$', text.strip())
    return bool(m)

def clean_junk_tail(text):
    text = text.strip()
    text = re.sub(r'[A-Za-z]\s*[\\|/|]\s*$', '', text).strip()
    return text

base_mp3 = PROJECT / 'output/audio/voiceover.mp3'
true_dur = 0.0
if base_mp3.exists():
    p = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1', str(base_mp3)], capture_output=True, text=True)
    try:
        true_dur = float(p.stdout.strip())
    except Exception:
        true_dur = DUR

print('true audio dur', true_dur)

trailer = PROJECT / 'output_tmp/trailer.mp4'
if not trailer.exists():
    raise SystemExit('trailer.mp4 missing')

info = subprocess.check_output([
    'ffprobe','-v','error',
    '-select_streams','v:0',
    '-show_entries','stream=width,height,r_frame_rate,duration',
    '-of','default=noprint_wrappers=1',
    str(trailer)], text=True)
print('trailer info', info)

# Make portrait clip ~target duration from trailer
clip = RENDER / 'portrait_clip.mp4'
ss = random.uniform(0.0, max(0.0, true_dur - 1.0))

# ss based on true audio duration later here: keep a simple approach: rand(max(dur-1,0))
ss = random.uniform(0.0, max(0.0, true_dur - 0.5))

# randstart is just trimmed start; duration = true_dur
cmd = [
    'ffmpeg','-y','-ss',str(round(ss,3)),'-i', str(trailer),
    '-t','-0',
    '-vf', f'scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p',
    '-r','30','-an','-movflags','+faststart', str(clip)
]
subprocess.run(cmd, check=True, capture_output=True, text=True)
print('clip', clip.exists(), clip.stat().st_size)

# Convert VTT to ASS manually
vtt_path = PROJECT / 'output/captions/captions.vtt'
ass_path = PROJECT / 'output_tmp/render_work/captions.ass'
out_lines = [
    '[Script Info]',
    'ScriptType: ASS',
    'PlayResX: 720',
    'PlayResY: 1280',
    '',
    '[V4+ Styles]',
    'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
    'Style: Default,Burbank Big Condensed,58,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2.8,1,5,10,10,22,1',
    '',
    '[Events]',
    'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
]
# Use VTT cues but only timecodes and text
vtt = vtt_path.read_text(encoding='utf-8').splitlines()
cues=[]
cur=None
for line in vtt:
    if '-->' in line and cur is None:
        a,b=line.split('-->',1)
        cur={'start':a.strip(),'end':b.strip().split(' ')[0].strip(),'text':[]}
    elif cur is not None:
        t=line.strip()
        if not t:
            if cur['text']:
                cues.append(cur); cur=None
        else:
            cur['text'].append(t)
if cur and cur['text']:
    cues.append(cur)

def to_ass_time(t):
    t=t.strip()
    if t.count(':')==2 and '.' in t:
        h,m,s=t.split(':'); s,ms=s.split('.')
        return f"{int(h):01d}:{int(m):02d}:{float('0.'+ms)+int(s):06.3f}"
    if t.count(':')==1 and '.' in t:
        m,s=t.split(':'); s,ms=s.split('.')
        return f"{int(m)}:{float('0.'+ms)+int(s):06.3f}"
    return t

ass=[]
for c in cues:
    ass.append(f"Dialogue: 0,{to_ass_time(c['start'])},{to_ass_time(c['end'])},Default,,0,0,0,,{' '.join(c['text'])}")
ass_path.write_text('\n'.join(out_lines+ass), encoding='utf-8')
print('ass cues', len(cues))

# Build ASS with font fallback: use installed Arial if file missing
font_use = FONT if FONT.exists() else FALLBACK_FONT
print('using font', font_use)

final = RENDER / 'final.mp4'
cmd = [
    'ffmpeg','-y',
    '-i', str(clip),
    '-i', str(base_mp3),
    '-filter_complex',
    f"[0:a]anull[noa];[1:a]volume=1[va];[noa][va]amix=inputs=2:duration=longest[aout];[0:v]ass='{str(ass_path).replace(chr(92),'/').replace('\\\\\\\\','/')}'[v]",
    '-map','[v]','-map','[aout]',
    '-c:v','libx264','-b:v','4500k','-maxrate','5000k','-bufsize','9000k',
    '-c:a','aac','-b:a','192k',
    '-shortest', str(final)
]
print('render cmd ready')
print('final', final)

# Write updated title in case
(FINAL_NAME_FILE).write_text(TITLE+'.mp4', encoding='utf-8')
print('final filename ->', FINAL_NAME_FILE.read_text())
