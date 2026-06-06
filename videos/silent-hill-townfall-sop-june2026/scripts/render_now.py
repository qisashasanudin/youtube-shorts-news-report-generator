import os
import subprocess
from pathlib import Path
import sys

ROOT = Path(r'C:/Users/qthas/Videos/Youtube Projects/MashButtonGaming/videos/silent-hill-townfall-sop-june2026')
wsl_root = Path('/mnt/c/Users/qthas/Videos/Youtube Projects/MashButtonGaming/videos/silent-hill-townfall-sop-june2026')

sh_path = ROOT / 'scripts' / 'render_wsl.sh'
sh_path.write_text(f"""set -x
cd '{wsl_root.as_posix()}'
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 'audio/voiceover.mp3' || true
ffmpeg -y -ss 0 -i 'clips/reordered.mp4' -i 'audio/voiceover.mp3' -filter_complex '[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,subtitles=captions/captions.ass:fontsdir=assets/fonts/whoosh[v]' -map '[v]' -map 1:a -c:v libx264 -c:a aac -shortest 'render/final.mp4'
ls -lh 'render/final.mp4'
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 'render/final.mp4'
""", encoding='utf-8')

proc = subprocess.run(['wsl', '-d', 'Ubuntu', 'bash', str(sh_path.as_posix().replace('C:/', '/mnt/c/'))], capture_output=True, text=True)
print(proc.stdout[-8000:])
print(proc.stderr[-4000:])
print('returncode', proc.returncode)
sys.exit(proc.returncode)
