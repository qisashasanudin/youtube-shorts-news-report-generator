set -euo pipefail
proj='/mnt/c/Users/qthas/Videos/Youtube Projects/MashButtonGaming/videos/final-fantasy-vii-rebirth-switch2'
cd "$proj"
rm -f audio/voiceover.mp3 captions/captions.vtt
.venv/bin/edge-tts \
  --voice en-US-GuyNeural \
  --rate=+20% \
  --text "$(cat "$proj/script/script.txt")" \
  --write-media "$proj/audio/voiceover.mp3" \
  --write-subtitles "$proj/captions/captions.vtt"

ls -lh audio/voiceover.mp3 captions/captions.vtt
