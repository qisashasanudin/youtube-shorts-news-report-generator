set -euo pipefail
cd '/mnt/c/Users/qthas/Videos/Youtube Projects/MashButtonGaming/videos/silent-hill-townfall-sop-june2026/scripts/render_now.sh'
ffmpeg -y -ss 0 -t 30 -i clips/reordered.mp4 -i audio/voiceover.mp3 -filter_complex '[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,subtitles=captions/captions.ass:fontsdir=assets/fonts/whoosh[v]' -map '[v]' -map 1:a -c:v libx264 -c:a aac -shortest -pix_fmt yuv420p render/final.mp4
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 render/final.mp4
