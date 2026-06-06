set -euo pipefail
cd '/mnt/c/Users/qthas/Videos/Youtube Projects/MashButtonGaming/videos/silent-hill-townfall-sop-june2026'
dur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 audio/voiceover.mp3)
ffmpeg -y -ss 0 -t "${dur}" -i clips/reordered.mp4 -i audio/voiceover.mp3 \
-filter_complex "[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,subtitles=captions/captions.ass:fontsdir=assets/fonts/whoosh:force_style='FontName=Whoosh,FontSize=64,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=0,Alignment=2,MarginV=100'[v]" \
-map "[v]" -map 1:a -c:v libx264 -c:a aac -shortest render/final.mp4
ls -lh render/final.mp4
