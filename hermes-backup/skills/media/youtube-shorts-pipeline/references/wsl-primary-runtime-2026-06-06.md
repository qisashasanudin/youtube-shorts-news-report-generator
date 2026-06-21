# WSL-primary runtime guidance (2026-06-06)

This session made WSL Ubuntu 24.04 the primary runtime for the YouTube shorts pipeline.

Verified environment:
- Distro: Ubuntu 24.04
- Python: 3.14
- Repo path mirrors Windows path under `/mnt/c/Users/qthas/Programming/Belajar/YouTube/youtube-shorts-news-report-generator`
- Preferred venv: `/root/mashbutton-venv`

Create and use the venv:
```bash
python3 -m venv ~/mashbutton-venv
source ~/mashbutton-venv/bin/activate
pip install -r src/scripts/requirements.txt
```

Run the builder from the same venv:
```bash
python src/shorts_builder.py --youtube "<url>" --title "<TITLE>" --subtitle "<SCRIPT TEXT>"
```

Why this venv:
- System Python is externally managed and refuses `pip install`
- The venv installs `edge-tts`, `yt-dlp`, `faster-whisper`, `python-dotenv`, `requests`, `feedparser`
- `ffmpeg` and `tesseract` are available system-wide in WSL

Path convention:
- Use `/mnt/c/Users/qthas/...` from WSL
- Do not switch between WSL and Windows paths inside the same build
- Windows native execution remains supported but is secondary
