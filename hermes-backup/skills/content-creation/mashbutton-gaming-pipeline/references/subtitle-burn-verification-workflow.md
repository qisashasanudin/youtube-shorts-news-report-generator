# Subtitle Burn Verification Workflow

Verified technique for youtube-shorts-news-report-generator: prove burned-in captions are actually visible on rendered frames, not just “ffmpeg returned 0”.

## Prerequisites
- final MP4 output from `src/shorts_builder.py`
- tesseract installed in WSL (`sudo apt-get install -y tesseract-ocr`)

## Steps
1. Extract a frame at 10–15s:
   ```bash
   ffmpeg -y -ss 15 -i videos/TO_UPLOAD/<safe-title>.mp4 -frames:v 1 frame_check.png
   ```
2. Run OCR via WSL:
   ```bash
   wsl -e bash -lc 'tesseract "/mnt/c/Users/qthas/.../frame_check.png" stdout'
   ```
3. Inspect the visible text. If expected subtitle words are not present, the burn step did not actually embed visible text.

## Expected Output When Burn Works
OCR should include the exact one-word uppercase caption text present in `captions.ass` for the sampled timestamp.