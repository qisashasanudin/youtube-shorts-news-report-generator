---
name: youtube-api-setup
title: YouTube API Setup
description: Google OAuth pattern for YouTube upload/analytics integrations, scope issues, and channel-level rules for MashButtonGaming.
---

# YouTube API Setup

Class-level guidance for authenticating Google APIs (`youtube`, `youtubeAnalytics`, etc.) and enforcing channel-specific upload/logging rules for the MashButtonGaming Shorts pipeline.

## Trigger

Use this skill when:
- Setting up or updating OAuth credentials for any `googleapiclient` or `google-auth` script
- Recovering from `403 Insufficient Permission` or scope mismatches
- Creating reusable auth helpers that rely on `client_secrets.json` and `token.json`
- Enforcing channel rules that should appear in upload/logging workflows (not just build scripts)

## Pitfalls

1. **Relative path resolution is unreliable on Windows Git Bash/MSYS** — `Path(__file__).resolve().parents[n]` can resolve against the wrong working directory when invoked from bash shortcuts. Use explicit absolute paths or reliable file-lookup from the script's own parent tree.
2. **A token can be `creds.valid == True` while still missing required scopes** — `YouTube Data API` scopes are additive. An upload-scope-only token (`youtube.upload`) will appear valid but fail analytics calls. Always check `set(creds.scopes).issubset(needed_scopes)` before skipping re-auth.
3. **`invalid_scope` refresh errors mean die, don't retry** — If `creds.refresh(Request())` raises `invalid_scope`, the existing grant is poisoned for those scopes. Skip refresh entirely and go straight to fresh console auth.
4. **`client_secrets.json` must be the same file used originally** — Re-auth fails or creates a mislinked grant if you point at a different secrets file than the one that created the original `token.json`.

## Auth Pattern

Use this sequence in any new Google API helper:

1. Define scopes explicitly.
2. Load existing token if present.
3. Compute `have_scopes = set(creds.scopes or [])` and `need_scopes = set(SCOPES)`.
4. If `creds.valid and need_scopes.issubset(have_scopes)` → early exit.
5. If `creds.expired and creds.refresh_token` → attempt refresh, then re-check scopes.
6. If refresh fails or scopes still missing → run `InstalledAppFlow.run_console()`.
7. Save updated token immediately.

## Existing Implementation Reference

The project's `src/scripts/youtube_upload.py` implements this exact pattern:
- Loads `client_secrets.json` from project root
- Persists `token.json` in project root
- Scopes: `youtube.upload`, `yt-analytics.readonly`, `youtube.readonly`
- Uses `InstalledAppFlow.run_local_server(port=0)` for interactive auth
- Auto-refreshes expired tokens with valid refresh_token
- Uploads via `googleapiclient.discovery.build("youtube", "v3")` + `MediaFileUpload(resumable=True)`
- CLI entry point: `python src/scripts/youtube_upload.py <video_path> --title <title> --privacy <private|public|unlisted>`

When debugging auth issues, compare against this working implementation.

## Channel Rules (MashButtonGaming)

- **Subtitle word count**: 50–100 words. This is enforced in `shorts_builder.py` and should be checked in any script that generates or sanitizes subtitle text.
- **YouTube title**: never include hashtags in the title. Hashtags belong in the video description and tags only.
- **Upload cadence**: max 1 per day if channel is under 100k subscribers to avoid splitting algorithm attention.
- **Dead video rule**: if a Short gets less than 100 views in 48 hours, delete and reupload with a new title on a different day.
- **Default privacy**: private, until explicit approval to make public/unlisted.
- **Workflow**: proposal-then-approve. Do not build or upload from any automated job without explicit user approval.
