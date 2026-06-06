import os
import random
import subprocess
from pathlib import Path

ROOT = Path(r'C:/Users/qthas/Videos/Youtube Projects/MashButtonGaming/videos/god-of-war-laufey-sop-june2026')
script_path = ROOT / 'script/script.txt'
audio_wav = ROOT / 'audio/voiceover.wav'
audio_mp3 = ROOT / 'audio/voiceover.mp3'
captions_vtt = ROOT / 'captions/captions.vtt'
captions_ass = ROOT / 'captions/captions.ass'
clips_dir = ROOT / 'clips'
render_dir = ROOT / 'render'
final_mp4 = render_dir / 'final.mp4'
trailer_yt = 'https://www.youtube.com/watch?v=2wxvMTotivY'

os.makedirs(clips_dir, exist_ok=True)
os.makedirs(render_dir, exist_ok=True)

text = script_path.read_text(encoding='utf-8')
subprocess.run([
    r'C:\Users\qthas\.venvs\piper-tts\Scripts\piper.exe',
    '-m', r'C:\Users\qthas\.piper\voices\en_US-lessac-medium.onnx',
    '-c', r'C:\Users\qthas\.piper\voices\en_US-lessac-medium.onnx.json',
    '-f', str(audio_wav),
], check=True)
subprocess.run([
    'ffmpeg', '-y', '-i', str(audio_wav), '-ar', '24000', '-ac', '1', '-b:a', '64k', str(audio_mp3)
], check=True)

print('TTS ready:', audio_mp3)
print('Now run make_vtt_small.py -> vtt_to_ass.py -> build_edit.py -> ffmpeg render')
