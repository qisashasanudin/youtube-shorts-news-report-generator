# MashButtonGaming Shorts Builder

Creates short-form gaming news videos for YouTube and TikTok from official game trailers. You supply a trailer link and a script; the tool handles voiceover, captions, video editing, and scheduling.

## What it does

- Turns an official game trailer into a vertical short video
- Adds AI voiceover narration
- Burns captions directly into the video
- Suggests and schedules upcoming topics
- Delivers finished videos to Telegram for review

## How a video is made

1. Download the official trailer footage
2. Generate the voice track from your script
3. Pick and shuffle short clips from the trailer
4. Align captions to the voiceover
5. Render the final 720x1280 video
6. Verify duration and file size

## Current delivery behavior

- Telegram is the default deliver channel
- YouTube and TikTok uploads are manual only
- Nothing is uploaded automatically

## Starting a new short

Prerequisites:
- Install Python 3.11 or newer
- Run `python -m venv .venv` from the project folder
- Run `.venv\\Scripts\\python.exe -m pip install -r src/scripts/requirements.txt`

Build a video:
```bash
.venv\\Scripts\\python.exe src/shorts_builder.py \
  --youtube "<TRAILER_URL>" \
  --title "<TITLE>" \
  --subtitle "<SCRIPT>"
```

The finished file appears in `videos/TO_UPLOAD/`.

## Rules to follow

Titles:
- Do not include `and here's what you need to know`

Scripts:
- Opening must end with `and here's what you need to know.`
- Closing must start with `but what do you think?`
- Closing must end with an open-ended question

Length:
- Script should be around 100-200 words
- Final video should be at least 30 seconds

Sources:
- Use only official game trailers or official channels
- Do not download sources larger than 500 MB

## Where things live

- Builder: `src/shorts_builder.py`
- Editorial helper: `src/editorial_state.py`
- Tasks/scripts: `src/scripts/`
- Assets: `assets/fonts/whoosh/`
- Finished videos: `videos/TO_UPLOAD/`
- Temporary files: `videos/` and `tmp` are cleaned daily

## YouTube and TikTok

YouTube:
- Upload helper included: `src/scripts/youtube_upload.py`
- Supports private, public, and unlisted uploads
- Default privacy is private
- Requires `client_secrets.json` and `token.json`
- These files contain private credentials and should not be shared

TikTok:
- Not implemented yet
- Planned for manual upload only, similar to YouTube
- Official API access is recommended when available

Manual upload example:
```bash
.venv\\Scripts\\python.exe src/scripts/youtube_upload.py "videos/TO_UPLOAD/<file>.mp4" --title "<TITLE>" --privacy private --description "<DESCRIPTION>" --tags "TAG1,TAG2"
```

## Channel

- YouTube: https://youtube.com/@mashbuttongaming

## Notes

- Video assets stay local on this machine
- Large files may fail to send through chat apps; use direct transfer if needed
- Captions depend on the included Whoosh font
