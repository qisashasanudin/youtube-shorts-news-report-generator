# Whisper-on-TTS ASS Sync Fix (2026-06-15)

## Problem
When using faster-whisper on synthetic TTS audio (edge-tts, Piper) to generate word-level timestamps for ASS subtitle burning, Whisper's final word `end` timestamp often falls **0.2–0.5s short** of the actual audio duration. This causes the last subtitle cue to disappear before the voiceover finishes, creating visible drift at the end of the video.

## Root Cause
Whisper models are trained on natural speech with natural silence/pauses. Synthetic TTS (especially at accelerated rates like `+25%`) has different acoustic characteristics — less natural trailing silence, sharper cutoffs — causing Whisper's VAD to stop slightly early.

## Solution
Modified `src/shorts_builder.py::_word_end()` to accept an optional `audio_duration` parameter. When provided, the last word's end timestamp is extended to match the actual audio duration:

```python
def _word_end(mapped: list[dict], idx: int, audio_duration: float = None) -> tuple[float, float]:
    # ... existing logic ...
    if idx + 1 >= len(mapped):  # last word
        if audio_duration is not None and e < audio_duration:
            e = audio_duration
    return s, max(e, s + 0.05)
```

Call site updated to pass `audio_duration`:
```python
timings = [_word_end(mapped, i, audio_duration) for i in range(len(mapped))]
```

## Result
- ASS final cue now ends at **23.29s** (matching 23.33s audio) instead of **22.99s**
- Subtitles remain visible through the full voiceover duration
- No more end-of-video subtitle drift

## Applicability
Applies to all flows using `shorts_builder.py` with Whisper-based caption timing (MashButtonGaming, AI Channel). Edge-TTS at `+25%` rate is the primary affected configuration.