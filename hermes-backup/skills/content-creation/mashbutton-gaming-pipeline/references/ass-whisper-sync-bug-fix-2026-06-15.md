# ASS/Whisper Sync Bug Fix (2026-06-15)

## Problem

Subtitle timing was **constant ~0.28s/word** instead of variable Whisper timings. ASS file showed `timing=whisper` but was actually using fallback.

## Root Cause

`faster-whisper` failed silently due to numpy version mismatch:
- Hermes venv: Python 3.11 at `/c/Users/qthas/AppData/Local/hermes/hermes-agent/venv/`
- numpy 2.4.6 installed (built for Python 3.13/cpython-313)
- Error: `ModuleNotFoundError: numpy._core._multiarray_umath`

Whisper threw exception → caught by bare `except:` → `mapped = []` → fell back to:
```python
per_word = audio_duration / max(1, len(words))
word_dur = per_word * 0.95
timings = [(i * per_word, i * per_word + word_dur) for i in range(len(words))]
```

This produced uniform ~0.28s/word timings with `timing=whisper` incorrectly logged.

## Fix Applied

### 1. Fix numpy in Hermes venv
```bash
/c/Users/qthas/AppData/Local/hermes/hermes-agent/venv/Scripts/pip install numpy==2.4.0 --force-reinstall
```
Note: numpy 2.4.0 is the last version with Python 3.11 wheels. numpy 2.4.6 requires Python 3.13+.

### 2. Patch `_word_end()` in `src/shorts_builder.py`
```python
def _word_end(mapped: list[dict], idx: int, audio_duration: float = None) -> tuple[float, float]:
    if idx + 1 < len(mapped):
        nxt = mapped[idx + 1]["start"]
        s = max(mapped[idx]["start"], 0.0)
        e = max(mapped[idx]["end"], s + 0.05)
        if nxt > s:
            e = min(e, nxt - 0.02)
        return s, max(e, s + 0.05)
    s = max(mapped[idx]["start"], 0.0)
    e = max(mapped[idx]["end"], s + 0.05)
    # Extend last word to audio duration if provided and Whisper ends early
    if audio_duration is not None and e < audio_duration:
        e = audio_duration
    return s, max(e, s + 0.05)
```

### 3. Update call site
```python
timings = [_word_end(mapped, i, audio_duration) for i in range(len(mapped))]
```

## Verification

After fix:
- `timing=whisper` with 82 words
- Variable timings: THE=0.06s, FIRST=0.18s, TIME=0.28s, BATTLEFIELD=0.36s, 4.=0.44s
- Last word extends to 23.30s (matches audio duration)
- ASS file ends at correct timestamp

## Diagnostic Commands

```bash
# Test numpy import
/c/Users/qthas/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe -c "import numpy; print(numpy.__version__)"

# Test Whisper on voiceover
/c/Users/qthas/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe -c "
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
segments, _ = model.transcribe('videos/.../audio/voiceover.mp3', language='en', word_timestamps=True)
for seg in segments:
    if seg.words:
        for w in seg.words[:15]:
            print(f'word=\"{w.word}\" start={w.start:.2f} end={w.end:.2f}')
"
```

## Prevention

- Always install numpy 2.4.0 in Hermes venv (Python 3.11)
- Add Whisper health check in builder startup
- Improve error logging: don't silently catch `except:` without logging