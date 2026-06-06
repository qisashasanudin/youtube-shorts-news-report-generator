import re, sys
from pathlib import Path

def vtt_time_to_ass(t):
    t = t.strip().replace(',', '.')
    m = re.match(r'^(\d+):(\d+):(\d+\.?\d*)$', t)
    if not m:
        raise ValueError(f'Bad timestamp: {t}')
    h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return f"{h}:{mi:02d}:{s:05.2f}"

in_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])
text = in_path.read_text(encoding='utf-8')
lines = text.splitlines()

cues = []
cur_start = cur_end = cur_text = None
for raw in lines:
    line = raw.strip()
    if not line:
        if cur_start is not None and cur_text:
            cues.append((cur_start, cur_end, cur_text.strip().upper()))
        cur_start = cur_end = cur_text = None
        continue
    m = re.match(r'^(\d+:\d+:\d+[\.,]\d+)\s*-->\s*(\d+:\d+:\d+[\.,]\d+)', line)
    if m:
        cur_start = vtt_time_to_ass(m.group(1))
        cur_end = vtt_time_to_ass(m.group(2))
        cur_text = ''
        continue
    if cur_start is not None:
        cur_text = (cur_text + ' ' + line).strip()

if cur_start is not None and cur_text:
    cues.append((cur_start, cur_end, cur_text.strip().upper()))

# Larger font size (64pt), bold (-1), higher position (MarginV=70)
head = """[Script Info]
Title: Short Subs
ScriptType: ASS
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Arial,64,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0.5,5,20,20,70,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

events = [head]
for s, e, txt in cues:
    events.append(f"Dialogue: 0,{s},{e},Default,,0,0,0,,{txt}\n")

out_path.write_text(''.join(events), encoding='utf-8')
print(f'wrote {len(cues)} uppercase cues to {out_path}')
