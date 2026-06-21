# Narration Review & Direct Language Lessons (2026-06-13)

## Session Corrections from User

### 1. Narration Review Required Before Build
**User correction**: "you dont even let me see the narration script"
**Lesson**: Always present the narration draft to the user for explicit approval BEFORE generating TTS, subtitles, or video. The workflow is:
1. Research facts
2. Write narration draft (50-100 words, hook + body + closing question)
3. **Send draft to user for review**
4. Wait for "Approved" or edits
5. Only then generate TTS → STT alignment → render

### 2. "Direct Language" = Simpler, Not Shorter
**User corrections**:
- "can you make the language more direct?"
- "no, by direct i mean make the wordings more understandable, not shorter, make the language more simplistic but still factually accurate"
- "scrap the subtitle, start from scratch, then send the draft to me first before generating anything"

**Lesson**: When user asks for "direct" language, they mean:
- Plain, simple vocabulary (e.g., "put in charge of" not "forcing to take daily control")
- Full sentences with clear subject-verb-object structure
- Explain acronyms/jargon (e.g., "military sim" not "mil sim", "headquarters" not "HQ")
- Keep all factual details (names, numbers, specifics) — do not compress
- Target: understandable by general gaming audience, not insider shorthand

### 3. Exact Script Usage
**User correction**: "Use this exact script, then generate the video"
**Lesson**: If user provides exact wording, use it verbatim. No rephrasing, no "improvements," no cleaning up. The user's words are the final script.

### 4. Telegram Delivery: Send as Document, Not Media
**User correction**: "Thats an mp3, not the video" (when MP4 was sent as media)
**Lesson**: 
- Telegram `MEDIA:` path sends as inline media (photo/video/voice). For MP4s >5MB, this often times out.
- Preferred fallback: send the same file as a **Telegram document** (same `MEDIA:` path works).
- Both HAEX (6.5MB) and Warzone EOS (15MB) timed out as media but succeeded as documents.
- This preserves the file for download; inline playback is sacrificed but delivery succeeds.

### 5. OpenAI TTS as Fallback
**Context**: Piper TTS CLI had execution issues on this host (`/c/Users/qthas/.venvs/piper-tts/bin/piper` is a Python script with wrong shebang, not executable binary).
**Lesson**: Use `text_to_speech` tool (OpenAI TTS via Nous subscription) as primary TTS. It works reliably and produces ~39s audio for ~100 words.

## Updated Workflow for This User

```
1. Research & fact-gather
2. Write narration draft (50-100 words)
3. SEND DRAFT TO USER → WAIT FOR APPROVAL
4. Generate TTS (text_to_speech tool → OpenAI TTS)
5. STT alignment (faster-whisper → per-word ASS)
6. Build video (shorts_builder.py or manual ffmpeg)
7. Verify: duration ≥30s, 720x1280, subtitles visible at active cue
8. Send to Telegram AS DOCUMENT (MEDIA: path)
9. Wait for upload approval
10. Upload to TikTok first, then YouTube if score ≥75
```

## MashButtonGaming Narration Formula (Reinforced)

- Hook: ends with "and here's what you need to know"
- Body: factual, simple language, all key details (names, numbers, causes)
- Closer: "But what do you think? [Two-angle question, not binary]"
- 50-100 words total
- One long line (no forced breaks)
- All-caps ASS output